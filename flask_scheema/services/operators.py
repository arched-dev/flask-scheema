from datetime import datetime
from typing import Dict, Callable, Any, Tuple, List, Optional

from sqlalchemy import func, inspect, Column, or_, Integer, Float, Date, Boolean
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import DeclarativeBase

from flask_scheema.exceptions import CustomHTTPException

OPERATORS: Dict[str, Callable[[Any, Any], Any]] = {
    "lt": lambda f, a: f < a,
    "le": lambda f, a: f <= a,
    "gt": lambda f, a: f > a,
    "eq": lambda f, a: f == a,
    "neq": lambda f, a: f != a,
    "ge": lambda f, a: f >= a,
    "ne": lambda f, a: f != a,
    "in": lambda f, a: f.in_(a),
    "nin": lambda f, a: ~f.in_(a),
    "like": lambda f, a: f.like(a),
    "ilike": lambda f, a: f.ilike(a),  # case-insensitive LIKE operator
}
aggregate_funcs = {
    "sum": func.sum,
    "count": func.count,
    "avg": func.avg,
    "min": func.min,
    "max": func.max,
}
PAGINATION_DEFAULTS = {"page": 0, "limit": 20}
PAGINATION_MAX = {"page": 0, "limit": 100}
OTHER_FUNCTIONS = ["groupby", "fields", "join", "orderby"]


def get_pagination(args_dict: Dict[str, str]):
    """
    Get the pagination from the request arguments

    Args:
        args_dict (Dict[str, str]): Dictionary of request arguments.

    Returns:
        Tuple[int, int]: Tuple of page and limit

    """

    # Handle Pagination
    page = args_dict.get("page", PAGINATION_DEFAULTS["page"])
    limit = args_dict.get("limit", PAGINATION_DEFAULTS["limit"])
    try:
        page = int(page)
    except ValueError:
        page = PAGINATION_DEFAULTS["page"]

    try:
        limit = int(limit)
        if limit > PAGINATION_MAX["limit"]:
            limit = PAGINATION_MAX["limit"]
    except ValueError:
        limit = PAGINATION_DEFAULTS["limit"]

    return page, limit


def get_all_columns_and_hybrids(
        model: Any, join_models: Dict[str, Any]
) -> Dict[str, Any]:
    all_columns = {}

    # Get columns and hybrid properties for the primary model
    inspector = inspect(model)
    all_columns[model.__name__] = {column.key: column for column in inspector.columns}
    for attr, value in model.__mapper__.all_orm_descriptors.items():
        if value.extension_type == hybrid_property:
            all_columns[model.__name__][attr] = value

    # Get columns and hybrid properties for each join model
    for join_model_name, join_model in join_models.items():
        inspector = inspect(join_model)
        all_columns[join_model_name] = {
            column.key: column for column in inspector.columns
        }

        for attr, value in join_model.__mapper__.all_orm_descriptors.items():
            if value.extension_type == hybrid_property:
                all_columns[join_model_name][attr] = value

    return all_columns


def get_group_by_fields(args_dict, all_columns, base_model):
    """
    Get the group by fields from the request arguments

    Args:
        args_dict (Dict[str, str]): Dictionary of request arguments.
        all_columns (Dict[str, Dict[str, Column]]): Nested dictionary of table names and their columns.
        base_model (DeclarativeBase): The base SQLAlchemy model.

    Returns:
        List[Callable]: List of conditions to apply in the query.

    """
    group_by_fields = []
    if "groupby" in args_dict:
        _group_by_fields = args_dict.get("groupby").split(",")
        for field in _group_by_fields:
            # gets the table name and column name from the field
            table_name, column_name = get_table_and_column(field, base_model)
            # gets the column from the column dictionary which is the actual column for the model
            model_column = get_check_table_columns(table_name, column_name, all_columns)
            group_by_fields.append(model_column)

    return group_by_fields


def get_join_models(
        args_dict: Dict[str, str], get_model_func: Callable
) -> Dict[str, Any]:
    """
        Builds a list of SQLAlchemy models to join based on request arguments.


    Args:
        args_dict (dict): Dictionary of request arguments.
        get_model_func (Callable): Function to get a model by name.

    Returns:
        A list of SQLAlchemy models to join.

    Raises:
        ValueError: If an invalid join model is supplied, a value error will be raised.

    """

    models = {}
    if args_dict.get("join"):
        for join in args_dict.get("join").split(","):
            model = get_model_func(join)
            if not model:
                raise CustomHTTPException(400, f"Invalid join model: {join}")
            models[join] = model

    return models


def is_qualified_column(key: str, join_models: Dict[str, Any]) -> bool:
    """Check if a column name is qualified with a table name.


    Args:
        key (str): The column name.
        join_models (Dict[str, Any]): Dictionary of join models.

    Returns:
        bool: True if the column name is qualified, False otherwise.
    """
    if "." not in key:
        return False
    table_name, _ = key.split(".")
    return table_name in join_models


def get_table_column(
        key: str, all_columns: Dict[str, Dict[str, Any]]
) -> Tuple[str, str, str]:
    """Get the fully qualified column name (i.e., with table name).


    Args:
         key (str): The column name.
         all_columns (Dict[str, Dict[str, Any]]): Nested dictionary of table names and their columns.

     Returns:
         Tuple[str, str, str]: A tuple containing the table name, column name, and operator.
    """
    keys_split = key.split("__")
    column_name = keys_split[0]
    operator = keys_split[1] if len(keys_split) > 1 else ""
    table_name = ""

    for table_name, columns in all_columns.items():
        # Check if column name is qualified with a table name, if it is split it and get the table name
        if "." in column_name:
            table_name, column_name = column_name.split(".")

        # Check if the column name is in the columns' dictionary
        if column_name in columns:
            break

    return table_name, column_name, operator


def get_select_fields(
        args_dict: Dict[str, str],
        base_model: DeclarativeBase,
        all_columns: Dict[str, Dict[str, Column]],
):
    """
        Get the select fields from the request arguments

    Args:
        args_dict (Dict[str, str]): Dictionary of request arguments.
        base_model (DeclarativeBase): The base SQLAlchemy model.
        all_columns (Dict[str, Dict[str, Column]]): Nested dictionary of table names and their columns.

    Returns:
        List[Callable]: List of conditions to apply in the query.

    """

    select_fields = []
    if "fields" in args_dict:
        _select_fields = args_dict.get("fields").split(",")
        for field in _select_fields:
            # gets the table name and column name from the field
            table_name, column_name = get_table_and_column(field, base_model)
            # gets the column from the column dictionary which is the actual column for the model
            model_column = get_check_table_columns(table_name, column_name, all_columns)
            select_fields.append(model_column)

    return select_fields


def create_conditions_from_args(
        args_dict: Dict[str, str],
        base_model: DeclarativeBase,
        all_columns: Dict[str, Dict[str, Column]],
        join_models: Dict[str, DeclarativeBase],
) -> List[Callable]:
    """Create filter conditions based on request arguments and model's columns.


    Args:
        args_dict (Dict[str, str]): Dictionary of request arguments.
        base_model (DeclarativeBase): The base SQLAlchemy model.
        all_columns (Dict[str, Dict[str, Any]]): Nested dictionary of table names and their columns.
        join_models (Dict[str, Any]): Dictionary of join models.

    Returns:
        List[Callable]: List of conditions to apply in the query.

    Raises:
        ValueError: If an invalid or ambiguous column name is provided.

    Examples:
        'id__eq': 1 would return Addresses.id == 1
        'account__eq': '12345' would return Addresses.account == '12345'
        'account__in': '12345,67890' would return Addresses.account.in_(['12345', '67890'])
        'account__like': '12345' would return Addresses.account.like('%12345%')
        '[account__eq,id__eq]': '12345,1' would return (Addresses.account == '12345') | (Addresses.id == 1)

    """

    conditions = []
    or_conditions = []

    for key, value in args_dict.items():
        if (
                len([x for x in OPERATORS.keys() if x in key]) > 0
                and len([x for x in PAGINATION_DEFAULTS.keys() if x in key]) <= 0
                and len([x for x in OTHER_FUNCTIONS if x in key]) <= 0
        ):
            if key.startswith("[") and key.endswith("]"):
                or_keys = key[1:-1].split(",")
                for or_key in or_keys:
                    (
                        table,
                        column,
                        operator,
                    ) = validate_and_get_tablename_column_name_and_operator(
                        or_key, join_models, all_columns
                    )
                    condition = create_condition(
                        table, column, operator, value, all_columns, base_model
                    )
                    or_conditions.append(condition)
                continue

            (
                table,
                column,
                operator,
            ) = validate_and_get_tablename_column_name_and_operator(
                key, join_models, all_columns
            )
            if not column:
                raise CustomHTTPException(
                    400, f"Invalid table/column name: {table}.{key}"
                )

            condition = create_condition(
                table, column, operator, value, all_columns, base_model
            )
            conditions.append(condition)

    if or_conditions:
        conditions.append(or_(*or_conditions))

    return conditions


def get_key_and_label(key):
    """
        Get the key and label from the key

    Args:
        key (str): The key from request arguments, e.g. "id__eq".

    Returns:
        A tuple of key and label

    """

    key_list = key.split("|")
    if len(key_list) == 1:
        return key, None
    elif len(key_list) >= 2:
        # was getting an error where the label and operator were combined, now we split them and recombine with the key
        key, pre_label = key_list[0], key_list[1]
        if "__" in pre_label:
            label, operator = pre_label.split("__")
            key = f"{key}__{operator}"
        else:
            label = pre_label

        return key, label


def validate_and_get_tablename_column_name_and_operator(
        key: str, join_models: Dict[str, Any], all_columns: Dict[str, Dict[str, Any]]
) -> tuple[str, str, str]:
    """
            Validate and get the condition key.


    Args:
        key (str): The column name.
        join_models (Dict[str, Any]): Dictionary of join models.
        all_columns (Dict[str, Dict[str, Any]]): Nested dictionary of table names and their columns.

    Returns:
        str: Validated condition key.
    """
    return get_table_column(key, all_columns)


def get_models_for_join(
        args_dict: Dict[str, str], get_model_func: Callable
) -> Dict[str, Callable]:
    """
        Builds a list of SQLAlchemy models to join based on request arguments.


    Args:
        args_dict (dict): Dictionary of request arguments.
        get_model_func (Callable): Function to get a model by name.

    Returns:
        A list of SQLAlchemy models to join.

    Raises:
        ValueError: If an invalid join model is supplied, a value error will be raised.

    """

    models = {}
    if args_dict.get("join"):
        for join in args_dict.get("join").split(","):
            model = get_model_func(join)
            models[join] = model

    return models


def create_aggregate_conditions(
        args_dict: Dict[str, str]
) -> Optional[Dict[str, Optional[str]]]:
    """
        Creates aggregate conditions based on request arguments and the model's columns.


    Args:
        args_dict: Dictionary of request arguments.

    Returns:
        A dictionary of aggregate conditions.

    """
    aggregate_conditions = {}

    for key, value in args_dict.items():
        for func_name in aggregate_funcs.keys():
            if f"__{func_name}" in key:
                key, label = get_key_and_label(key)
                aggregate_conditions[key] = label

    return aggregate_conditions


def get_table_and_column(value, main_model):
    """
        Get the table and column name from the value

    Args:
        value (str): The value from request arguments, e.g. "id__eq".
        main_model (Any): The base SQLAlchemy model.

    Returns:
        A tuple of table name and column name

    """
    if "." in value:
        table_name, column_name = value.split(".", 1)
    else:
        table_name = main_model.__name__
        column_name = value
    return table_name, column_name


def get_column_and_table_name_and_operator(
        key: str, main_model: DeclarativeBase
) -> Tuple[str, str, str]:
    """
        Get the column and table name from the key

    Args:
        key (str): The key from request arguments, e.g. "id__eq".
        main_model (Any): The base SQLAlchemy model.

    Returns:
        A tuple of column name and table name
    """
    # Check if key is in the format of <column_name>__<operator> if its no we assume its <column_name>=<value>

    field, operator_str = key.split("__")
    table_name, column_name = get_table_and_column(field, main_model)

    return column_name, table_name, operator_str


def get_check_table_columns(
        table_name: str, column_name: str, all_columns: Dict[str, Dict[str, Column]]
):
    """
        Get the column from the column dictionary

    Args:
        table_name (str): the table name
        column_name (str): the column name
        all_columns (Dict[str, Dict[str, Column]]): Dictionary of columns in the base model.

    Returns:
        The column

    """
    # Get column from the column dictionary
    all_models_columns = all_columns.get(table_name, {})
    if not all_models_columns:
        raise CustomHTTPException(400, f"Invalid table name: {table_name}")

    model_column = all_models_columns.get(column_name, None)
    if model_column is None:
        raise CustomHTTPException(400, f"Invalid column name: {column_name}")

    return model_column


def create_condition(
        table_name: str,
        column_name: str,
        operator: str,
        value: str,
        all_columns: Dict[str, Dict[str, Column]],
        base_model: Any,
) -> Callable:
    """
        Converts a key-value pair from request arguments to a condition.

        This version of the function accounts for joined tables.


    Args:
        table_name (str): The table name.
        column_name (str): The column name.
        operator (str): The operator.
        value (str): The value associated with the key.
        all_columns (Dict[str, Column]): Dictionary of columns in the base model.
        base_model (Any): The base SQLAlchemy model.

    Returns:
        Callable: A condition function.

    Raises:
        ValueError: If invalid operator or column is found in query params.
    """

    # # Determine if key contains joined table information
    # column_name, table_name, operator = get_column_and_table_name_and_operator(
    #     key, base_model
    # )

    # Get the column from the column dictionary
    model_column = get_check_table_columns(table_name, column_name, all_columns)

    # Check if it's a hybrid property
    is_hybrid = (
            hasattr(model_column, "extension_type")
            and model_column.extension_type == hybrid_property
    )

    # Attempt to convert value to the type of the column
    try:
        value = convert_value_to_type(value, model_column.type, is_hybrid)
    except ValueError as e:
        # Handle or propagate the error. For instance, you might add an error message to the response.
        pass

    # Get operator function from the OPERATORS dictionary
    operator_func = OPERATORS.get(operator)
    if operator_func is None:
        return

    if "in" in operator:
        value = value.split(",")
    if "like" in operator:
        value = f"%{value}%"

    return operator_func(model_column, value)


def convert_value_to_type(value: str, column_type: Any, is_hybrid: bool = False) -> Any:
    """
    Convert the given string value to its appropriate type based on the provided column_type.
    """
    if is_hybrid:
        # Do special handling here, e.g., return value without a conversion
        return value

    if isinstance(column_type, Integer):
        return int(value)

    elif isinstance(column_type, Float):
        return float(value)

    elif isinstance(column_type, Date):
        return datetime.strptime(value, "%Y-%m-%d").date()

    elif isinstance(column_type, Boolean):
        if value.lower() in ["true", "True", "TRUE", "1", 1, "yes", "y", "Yes", "YES"]:
            return True
        elif value.lower() in [
            "false",
            "False",
            "FALSE",
            0,
            "0",
            "n",
            "N",
            "no",
            "No",
            "NO",
        ]:
            return False
        else:
            raise CustomHTTPException(400, f"Invalid boolean value: {value}")
    # You can continue to add other types as needed.
    # If a type is unrecognised, return the original string value
    return value
