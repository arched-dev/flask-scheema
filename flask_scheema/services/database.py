from functools import wraps
from typing import Callable, Union, Dict, List, Optional, Any
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from flask import request, abort
from sqlalchemy import desc, inspect, Column, and_, func
from sqlalchemy.orm import Query, Session, DeclarativeBase

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
                    output["dictionary"] = [result._asdict() for result in output["query"]]
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
        count = output.get("count")

        parsed_url = urlparse(request.url)
        query_params = parse_qs(parsed_url.query)

        next_url = None
        previous_url = None
        current_page = None
        total_pages = None

        # Calculate total_pages and current_page
        if count and limit:
            total_pages = -(-count // limit)  # Equivalent to math.ceil(count / limit)
            current_page = page

            # Update the 'page' query parameter for the next and previous URLs
            query_params["limit"] = [str(limit)]
            query_params["page"] = [str(page + 1)]
            next_query_string = urlencode(query_params, doseq=True)

            query_params["page"] = [str(page - 1)]
            prev_query_string = urlencode(query_params, doseq=True)

            # Determine if there are next and previous pages
            next_page = page + 1 if (page + 1) * limit < count else None
            prev_page = page - 1 if page > 0 else None

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
        all_columns: Dict[str, Dict[str:Column]] = get_all_columns_and_hybrids(
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
                args_dict, self.model, all_columns, join_models
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
            column = get_check_table_columns(table_name, column_name, all_columns)

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
    def get_query(self, args_dict: Dict[str, Union[str, int]],
                  lookup_val: Optional[Union[int, str]] = None,
                  alt_field: Optional[str] = None,
                  multiple: Optional[bool] = True,
                  other_model=None) -> Dict[str, Any]:
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

        query = self.get_query_from_args(args_dict)

        if lookup_val and not multiple:

            if alt_field:
                query = query.filter_by(**{alt_field: lookup_val})
            else:
                query = query.filter_by(id=lookup_val)

            results = query.first()
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

            return {"query": results, "count": count, "page": page, "limit": limit}

    def create(self, **kwargs) -> object:
        """
        Creates a new object in the database, based on the provided data.

        Args:
            kwargs (dict): A dictionary of data to create the object with.

        Returns:
            object: The newly created SQLAlchemy object.

        """
        body = kwargs.get("deserialized_data")
        new_model = self.model(**body)
        self.session.add(new_model)
        self.session.commit()
        return {"query": new_model}

    def update(self, **kwargs) -> object:
        """
        Updates an object in the database, based on the provided id and data.

        Args:
            obj (object): The SQLAlchemy object to update.

        Returns:
            object: The updated SQLAlchemy object.

        """
        obj = self.get_query(request.args.to_dict(), kwargs.get("lookup_val"), multiple=False)["query"]
        if obj:
            body = kwargs.get("deserialized_data")
            for key, value in body.items():
                setattr(obj, key, value)
            self.session.commit()
            return {"query": obj}

        abort(404)

    def delete(self, *args, **kwargs) -> dict:
        """
                Deletes an object from the database, based on the provided id.


        Kwargs:
            lookup_val (int): The id of the object to delete.

        Returns:
            dict: "complete: True if the object was successfully deleted, False otherwise.

        """
        obj = self.get_query(request.args.to_dict(), kwargs.get("lookup_val"), multiple=False)["query"]
        if obj:
            self.session.delete(obj)
            self.session.commit()
            return {"complete": True}
        abort(404)
