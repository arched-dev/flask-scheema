from functools import wraps
from typing import Callable, Union, Dict, List, Optional, Any
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

import sqlalchemy
from flask import request
from sqlalchemy import desc, inspect, Column, and_, func
from sqlalchemy.exc import IntegrityError, DataError
from sqlalchemy.orm import Query, Session, class_mapper

from flask_scheema.api.utils import get_primary_keys
from flask_scheema.exceptions import CustomHTTPException
from flask_scheema.services.operators import (
    aggregate_funcs,
    get_pagination,
    get_all_columns_and_hybrids,
    get_group_by_fields,
    get_select_fields,
    create_conditions_from_args,
    get_models_for_join,
    create_aggregate_conditions,
    get_table_and_column,
    get_column_and_table_name_and_operator,
    get_check_table_columns,
)
from flask_scheema.utilities import get_config_or_model_meta


def add_dict_to_query(f: Callable) -> Callable:
    """
    Adds a dictionary to the query result, this is for they result is an SQLAlchemy result object and not an ORM model,
    used when there are custom queries, etc.

    Returns:
        dict: Dictionary containing a query result and count.

    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        output = f(*args, **kwargs)
        if isinstance(output, dict):
            try:
                if isinstance(output["query"], list):
                    output["dictionary"] = [
                        result._asdict() for result in output["query"]
                    ]
                output["dictionary"] = output["query"]._asdict()

            except AttributeError:
                pass

        return output

    return decorated_function


def add_page_totals_and_urls(f: Callable) -> Callable:
    """
        Adds page totals and urls to the query result.

    Args:
            f (Callable): The function to decorate.

        Returns:
            Callable: The decorated function.

    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        """
                Gets the output of the function and append the page totals and urls to the output.

        Args:
            **kwargs:
        Returns:

        """
        output = f(*args, **kwargs)
        limit = output.get("limit")
        page = output.get("page")
        total_count = output.get("total_count")

        parsed_url = urlparse(request.url)
        query_params = parse_qs(parsed_url.query)

        next_url = None
        previous_url = None
        current_page = None
        total_pages = None

        # Calculate total_pages and current_page
        if total_count and limit:
            total_pages = -(
                -total_count // limit
            )  # Equivalent to math.ceil(count / limit)
            current_page = page

            # Update the 'page' query parameter for the next and previous URLs
            query_params["limit"] = [str(limit)]
            query_params["page"] = [str(page + 1)]
            next_query_string = urlencode(query_params, doseq=True)

            query_params["page"] = [str(page - 1)]
            prev_query_string = urlencode(query_params, doseq=True)

            # Determine if there are next and previous pages
            next_page = page + 1 if (page + 1) * limit < total_count else None
            prev_page = page - 1 if page > 1 else None

            # Construct next and previous URLs
            next_url = (
                urlunparse(parsed_url._replace(query=next_query_string))
                if next_page is not None
                else None
            )
            previous_url = (
                urlunparse(parsed_url._replace(query=prev_query_string))
                if prev_page is not None
                else None
            )

        if isinstance(output, dict):
            try:
                output["next_url"] = next_url
                output["previous_url"] = previous_url
                output["current_page"] = current_page
                output["total_pages"] = total_pages
            except AttributeError:
                pass

        return output

    return decorated_function


def apply_pagination(query: Union[Query], page: int = 0, limit: int = 20) -> list[Any]:
    """
        Paginates a given query.


    Args:
            query (Query): Original SQLAlchemy query.
            page (int): Page number for pagination.
            limit (int): Number of items per page.

        Returns:
            Query: Paginated query results.
    """
    return query.paginate(page=page, per_page=limit, error_out=False)


def apply_order_by(args_dict: Dict, query: Query, base_model: callable) -> Query:
    """
        Applies order_by conditions to a query.
        Use "-" prefix for descending order.
        Example: "-id,name"


    Args:
        args_dict (dict): Dictionary containing filtering and pagination conditions.
        query (Query): The query to sort.
        base_model (Base): The base model for the query.

    Returns:
        Query: The sorted query.
    """

    if "order_by" in args_dict:
        order_by = args_dict["order_by"]
        if isinstance(order_by, str):
            order_by = order_by.split(",")

        for order_key in order_by:
            descending = False
            if order_key.startswith("-"):
                descending = True
                order_key = order_key[1:]

            column = get_table_and_column(order_key, base_model)
            if column:
                if descending:
                    query = query.order_by(desc(order_key))
                else:
                    query = query.order_by(order_key)

    return query


class CrudService:
    def __init__(self, model, session: Session):
        """
                Initializes the CrudService instance.


        Args:
            model (Callable): SQLAlchemy model class for CRUD operations.
            session (Session): SQLAlchemy session.

        """
        self.model = model
        self.session = session

    def get_model_by_name(self, field_name: str):
        """
                Gets a model by name.

        Args:
            field_name (str): The name of the model to get.

        Returns:
            object: The model class.

        Raises:
            Exception: If the model does not have a relationship with the current model.

        """

        # Check for relationships between the fetched model and self.model
        relationships = inspect(self.model).relationships
        related_model = relationships.get(field_name)

        if related_model is None:
            raise CustomHTTPException(
                401,
                f"Field {field_name} does not represent a relationship in model {self.model.__name__}",
            )

        return related_model.mapper.class_

    def get_query_from_args(self, args_dict: Dict[str, Union[str, int]]) -> Query:
        """
                Filters a query based on request arguments. Handles filtering, sorting, pagination and aggregation.

        Args:
            args_dict (dict): Dictionary containing filtering and pagination conditions.

        Returns:
            Query: The filtered query.

        """
        # columns in the model

        # get the models to join
        join_models: Dict = get_models_for_join(args_dict, self.get_model_by_name)

        # get all columns in the model
        all_columns, all_models = get_all_columns_and_hybrids(
            self.model, join_models
        )  # table name, column name, column

        # get the select fields
        select_fields: List[Callable] = get_select_fields(
            args_dict, self.model, all_columns
        )

        # create the conditions
        conditions: List = [
            x
            for x in create_conditions_from_args(
                args_dict, self.model, all_columns, all_models, join_models
            )
            if x is not None
        ]

        # create the aggregates
        aggregates: Optional[Dict[str, Optional[str]]] = create_aggregate_conditions(
            args_dict
        )

        # apply the aggregates
        if aggregates:
            aggregate_columns = self.calculate_aggregates(aggregates, all_columns)
            # combine the select fields with the aggregate columns
            select_fields = select_fields + aggregate_columns

        # create the query
        if select_fields:
            query: Query = self.session.query(*select_fields)
        else:
            query: Query = self.session.query(self.model)

        # join the models
        for k, v in join_models.items():
            query = query.join(v)

        groupby_columns: List[Callable] = get_group_by_fields(
            args_dict, all_columns, self.model
        )
        # apply the groupby
        if groupby_columns:
            query = query.group_by(*groupby_columns)

        # apply the conditions
        if conditions:
            query = query.filter(and_(*conditions))

        # Handle Sorting

        query = apply_order_by(args_dict, query, self.model)

        return query

    def calculate_aggregates(
        self, aggregate_conditions: Dict, all_columns: Dict[str, Dict[str, Column]]
    ):
        """
                Applies aggregate conditions to a query and returns the aggregated query.


        Args:
            aggregate_conditions (Dict): List of aggregate conditions.
            all_columns (dict): Dictionary of all columns in the model.

        Returns:
            List: List of aggregated columns.


        """
        # Separate groupby from other aggregate functions
        aggregate_columns = []

        for key, value in aggregate_conditions.items():
            column_name, table_name, agg_func = get_column_and_table_name_and_operator(
                key, self.model
            )
            column, column_name = get_check_table_columns(
                table_name, column_name, all_columns
            )

            aggregate_func = aggregate_funcs.get(agg_func)
            if aggregate_func:
                # added this so we can have the label if we want it
                column = aggregate_func(column)
                if value:
                    column = column.label(value)
                aggregate_columns.append(column)

        # Apply other aggregate functions
        # if aggregate_columns:
        #     query = query.with_entities(*aggregate_columns)
        #
        # # Apply groupby first, if exists
        # if groupby_columns:
        #     query = query.group_by(*groupby_columns)

        return aggregate_columns

    @add_page_totals_and_urls
    @add_dict_to_query
    def get_query(
        self,
        args_dict: Dict[str, Union[str, int]],
        lookup_val: Optional[Union[int, str]] = None,
        alt_field: Optional[str] = None,
        multiple: Optional[bool] = True,
        other_model=None,
        **kwargs
    ) -> Dict[str, Any]:
        """
                Retrieves a list of objects from the database, optionally paginated.


        Args:
            args_dict (dict): Dictionary containing filtering and pagination conditions.
                Extracts 'order_by' from args_dict for sorting. Use "-" prefix for descending order.
            lookup_val (Optional[int]): The id of the object to return.
            alt_field (Optional[str]): An alternative field to search by.
            multiple (Optional[bool]): Whether to return many objects or not.
            other_model (db.model): The model to join with.

        Returns:
            dict: Dictionary containing a query result and count.

        """
        pk = get_primary_keys(self.model)
        query = self.get_query_from_args(args_dict)

        if lookup_val:  # and not multiple:

            if alt_field:
                query = query.filter_by(**{alt_field: lookup_val})
            else:
                query = query.filter(pk == lookup_val)

            results = query.first()
            if not results:
                raise CustomHTTPException(
                    404, f"{self.model.__name__} not found with {pk.key} {lookup_val}"
                )
            return {"query": results}

        else:

            if other_model:
                pk = get_primary_keys(other_model)
                query = query.join(other_model).filter(pk == lookup_val)

            count = self.session.query(func.count()).select_from(query).scalar()
            page, limit = get_pagination(args_dict)
            if page or limit:
                query = apply_pagination(query, page, limit)

            if hasattr(query, "all"):
                results = query.all()
            else:
                results = query.items

            return {
                "query": results,
                "total_count": count,
                "page": page,
                "limit": limit,
            }

    def create(self, **kwargs) -> object:
        """
        Creates a new object in the database, based on the provided data.

        Args:
            kwargs (dict): A dictionary of data to create the object with.

        Returns:
            object: The newly created SQLAlchemy object.

        """
        body = kwargs.get("deserialized_data")
        if not body:
            raise CustomHTTPException(400, "No data provided for creation.")

        try:
            new_model = self.model(**body)
            self.session.add(new_model)
            self.session.commit()
            return {"query": new_model}
        except IntegrityError as e:
            self.session.rollback()
            # Log the error as well if logging is setup
            # logging.error(f"IntegrityError: {e}")
            raise CustomHTTPException(400, f"Integrity error: {e.orig}")
        except DataError as e:
            self.session.rollback()
            # Log the error as well if logging is setup
            # logging.error(f"DataError: {e}")
            raise CustomHTTPException(400, f"Data error: {e.orig}")
        except Exception as e:
            self.session.rollback()
            # Catch-all for any other unforeseen errors
            # logging.error(f"Unexpected error: {e}")
            raise CustomHTTPException(500, "An unexpected error occurred.")

    def update(self, **kwargs) -> dict:
        """
        Updates an object in the database, based on the provided id and data.

        Kwargs:
            lookup_val (int): The id of the object to update.
            deserialized_data (dict): The data to update the object with.

        Returns:
            dict: The updated object if successful, or an error message if not.
        """
        lookup_val = kwargs.get("lookup_val")
        if not lookup_val:
            raise CustomHTTPException(400, "No lookup value provided for update.")

        obj = self.get_query(request.args.to_dict(), lookup_val, multiple=False)[
            "query"
        ]
        if obj:
            body = kwargs.get("deserialized_data")
            if body is None:
                raise CustomHTTPException(400, "No data provided for update.")
            try:
                for key, value in body.items():
                    if hasattr(obj, key):
                        setattr(obj, key, value)
                    else:
                        raise CustomHTTPException(
                            400, f"Invalid field '{key}' for update."
                        )
                self.session.commit()
                return {"query": obj}
            except sqlalchemy.exc.IntegrityError as e:
                self.session.rollback()
                raise CustomHTTPException(400, f"Integrity error during update: {e}")
            except Exception as e:
                self.session.rollback()
                raise CustomHTTPException(500, f"Unexpected error during update: {e}")
        else:
            raise CustomHTTPException(404, "Object not found for update.")

    def delete(self, *args, **kwargs) -> dict:
        """
        Deletes an object from the database, based on the provided id, with optional cascading delete.

        Kwargs:
            lookup_val (int): The id of the object to delete.

        Returns:
            dict: "complete": True if the object was successfully deleted, False otherwise.
        """
        lookup_val = kwargs.get("lookup_val")
        args = request.args.to_dict()
        cascade_delete = "cascade_delete" in args and args.pop("cascade_delete") in (
            "true",
            "1",
        )
        allow_cascade = get_config_or_model_meta(
            "API_ALLOW_CASCADE_DELETE", default=True
        )
        if not lookup_val:
            raise CustomHTTPException(400, "No lookup value provided for deletion.")

        obj = self.get_query(args, lookup_val, multiple=False)["query"]
        if obj:
            try:
                if cascade_delete and allow_cascade:
                    # Iterate over all relationships and delete related objects if cascade_delete is True
                    for relationship in class_mapper(obj.__class__).relationships:
                        related_objects = getattr(obj, relationship.key)
                        if isinstance(related_objects, list):
                            for related_obj in related_objects:
                                self.session.delete(related_obj)
                        else:
                            self.session.delete(related_objects)

                self.session.delete(obj)
                self.session.commit()
                return {"complete": True}

            except sqlalchemy.exc.IntegrityError as e:
                self.session.rollback()
                if not cascade_delete:
                    # Build a detailed error message
                    related_entities = [
                        rel.key for rel in class_mapper(obj.__class__).relationships
                    ]
                    if related_entities and allow_cascade:
                        related_entities_str = ", ".join(related_entities)
                        error_message = f"Deletion failed due to existing related records with not null constraints. "
                        error_message += f"Consider adding '?cascade_delete=1' to the request URL to delete all related records including: {related_entities_str}"

                    elif related_entities and not allow_cascade:
                        related_entities_str = ", ".join(related_entities)
                        error_message = f"Deletion failed due to existing related records including: {related_entities_str}"

                    elif allow_cascade:
                        error_message = (
                            "Deletion failed due to existing related records. "
                        )
                        error_message += "Consider adding '?cascade_delete=1' to the request URL to delete all related records."

                    raise CustomHTTPException(500, error_message)
                else:
                    raise CustomHTTPException(
                        500, "An error occurred during cascading delete."
                    )
        else:
            raise CustomHTTPException(404, "Object not found for deletion.")
