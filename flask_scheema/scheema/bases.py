from contextlib import contextmanager

from flask import request
from marshmallow import fields, Schema, missing, ValidationError
from marshmallow.validate import Length
from sqlalchemy import Integer, String, Boolean, Float, Date, DateTime, Time, Text, Numeric, BigInteger, LargeBinary, \
    Enum, ARRAY, Interval
from sqlalchemy.dialects.postgresql import JSON, JSONB
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import class_mapper, RelationshipProperty, ColumnProperty

from flask_scheema.api.utils import endpoint_namer
from flask_scheema.logging import logger
from flask_scheema.scheema.utils import get_openapi_meta_data, get_input_output_from_model_or_make, convert_snake_to_camel
from flask_scheema.utilities import get_config_or_model_meta

type_mapping = {
    # Basic types
    Integer: fields.Int,
    String: fields.Str,
    Text: fields.Str,
    Boolean: fields.Bool,
    Float: fields.Float,
    Date: fields.Date,
    DateTime: fields.DateTime,
    Time: fields.Time,
    JSON: fields.Raw,
    JSONB: fields.Raw,
    Numeric: fields.Decimal,
    BigInteger: fields.Int,

    # Additional types
    LargeBinary: fields.Str,
    Enum: fields.Str,
    ARRAY: fields.List,
    Interval: fields.TimeDelta,

    # Python built-in types
    str: fields.Str,
    int: fields.Int,
    bool: fields.Bool,
    float: fields.Float,
    dict: fields.Dict,
    list: fields.List,
}



def find_matching_relations(model1, model2):
    """
    Find matching relation fields between two SQLAlchemy models.

    Args:
        model1: The first SQLAlchemy model class.
        model2: The second SQLAlchemy model class.

    Returns:
        A list of tuples, where each tuple contains the names of the matching relation fields
        (relation_in_model1, relation_in_model2).
    """
    matching_relations = []

    # Get the relationship properties of both models
    relationships1 = class_mapper(model1).relationships
    relationships2 = class_mapper(model2).relationships

    # Iterate through all relationships in model1
    for rel_name1, rel_prop1 in relationships1.items():
        # Check if this relationship points to model2
        if rel_prop1.mapper.class_ == model2:
            # Now, check for the reverse relationship in model2
            for rel_name2, rel_prop2 in relationships2.items():
                if rel_prop2.mapper.class_ == model1:
                    # If a reverse relationship is found, add the pair to the results
                    matching_relations.append((rel_name1, rel_name2))

    return matching_relations


def _get_relation_use_list_and_type(relationship_property):
    """
    Get the relation use_list property and the type of relationship for a given relationship_property.
    Args:
        relationship_property (RelationshipProperty): The relationship property

    Returns:
        tuple: A tuple containing the use_list property (bool) and relationship type (str)
    """
    if hasattr(relationship_property, "property"):
        relationship_property = relationship_property.property

    # Get the direction of the relationship
    direction = (
        relationship_property.direction.name
    )  # This will give you a string like 'MANYTOONE', 'ONETOMANY', or 'MANYTOMANY'

    return not relationship_property.uselist, direction

class DeleteSchema(Schema):
    complete = fields.Boolean(required=True, default=False)


class AutoScheema(Schema):
    class Meta:
        model = None  # Default to None. Override this in subclasses if needed.
        add_hybrid_properties = True
        include_children = True

    def __init__(self, *args, render_nested=True, **kwargs):

        only_fields = kwargs.pop('only', None)

        if not hasattr(self, "depth"):
            self.depth = kwargs.pop('depth', 0)
        if not hasattr(self, "parent"):
            self.parent = kwargs.pop('parent', 0)

        super().__init__(*args, **kwargs)
        self.context = {"current_depth": 0}  # Initialize an empty context dictionary
        self.render_nested = render_nested  # Save the parameter to the instance
        if hasattr(self.Meta, "model"):
            logger.debug(1, f"Creating to mallow object |{self.__class__.__name__}|")
            self.model = self.Meta.model

            self.generate_fields()
            self.dump_fields.update(self.fields)
            self.load_fields.update(self.fields)

        if only_fields:
            self._apply_only(only_fields)

    def _apply_only(self, only_fields):
        # Your custom logic here.
        # For example:
        self.fields = {key: self.fields[key] for key in only_fields}
        self.dump_fields = {key: self.dump_fields[key] for key in only_fields}
        self.load_fields = {key: self.load_fields[key] for key in only_fields}

    def generate_fields(self):
        """
        Automatically add fields for each column and relationship in the SQLAlchemy model.
        Also adds fields for hybrid properties.
        Returns:
            None
        """
        # Check if model is None
        if self.Meta.model is None:
            print("Warning: self.Meta.model is None. Skipping field generation.")
            return

        mapper = class_mapper(self.Meta.model)
        for attribute, mapper_property in mapper.all_orm_descriptors.items():

            original_attribute = attribute
            if get_config_or_model_meta("API_CONVERT_TO_CAMEL_CASE", default=True):
                attribute = convert_snake_to_camel(attribute)

            if not attribute.startswith('_'):
                # relations
                if isinstance(mapper_property, RelationshipProperty):
                    self.add_relationship_field(attribute, original_attribute, mapper_property)
                elif (
                        hasattr(mapper_property, "property")
                        and mapper_property.property._is_relationship
                ):
                    logger.debug(4,
                                 f"Adding to mallow object |{self.__class__.__name__}| relationship field +{mapper_property}+")
                    self.add_relationship_field(attribute, original_attribute, mapper_property)
                # columns
                elif hasattr(mapper_property, "property") and isinstance(
                        mapper_property.property, ColumnProperty
                ):
                    logger.debug(4,
                                 f"Adding to mallow object |{self.__class__.__name__}| column field +{mapper_property}+")
                    self.add_column_field(
                        attribute, original_attribute, mapper_property
                    )
                elif hasattr(mapper_property, "columns"):
                    logger.debug(4,
                                 f"Adding to mallow object |{self.__class__.__name__}| column field +{mapper_property}+")
                    self.add_column_field(attribute, original_attribute, mapper_property.columns[0].type)
                # hybrid properties
                elif isinstance(mapper_property, hybrid_property):
                    logger.debug(4,
                                 f"Adding to mallow object |{self.__class__.__name__}| hybrid property field +{mapper_property.__name__}+")
                    self.add_hybrid_property_field(attribute, original_attribute,
                                                   mapper_property.__annotations__.get("return"))

    def add_hybrid_property_field(self, attribute, original_attribute, field_type):
        """
        Automatically add a field for a given hybrid property in the SQLAlchemy model.

        Args:
            attribute (str): The name of the attribute to add to the schema.
            original_attribute (str): The original attribute name from the SQLAlchemy model.
            field_type (str): The type of the hybrid property.

        Returns:
            None
        """
        # Skip attributes that start with an underscore
        if attribute.startswith("_"):
            return

        # You might need to determine the appropriate field type differently.
        if field_type:
            field_type = type_mapping.get(field_type, fields.Str)
        else:
            field_type = fields.Str

        # Initialize field arguments
        field_args = {}

        # Check if there is a setter method for the hybrid property
        hybrid_property_obj = getattr(self.Meta.model, original_attribute, None)
        if not hasattr(hybrid_property_obj, "fset") or hybrid_property_obj.fset is None:
            field_args["dump_only"] = True  # No setter, so set it to dump only

        # Add the field to the Marshmallow schema
        self.fields[original_attribute] = field_type(data_key=attribute, **field_args)

        # Update additional attributes like you did in add_column_field
        self.fields[original_attribute].parent = self
        self.fields[original_attribute].name = attribute
        # Assuming `get_openapi_meta_data` is a function you've defined
        self.fields[original_attribute].metadata.update(
            get_openapi_meta_data(self.fields[original_attribute])
        )

    def add_column_field(self, attribute, original_attribute, mapper):
        """
        Automatically add a field for a given column in the SQLAlchemy model, using the column type to determine the
        Marshmallow field type. The function will ignore any attributes that start with an underscore.

        Args:
            attribute (str): The name of the attribute to add to the schema.
            original_attribute (str): The original attribute name from the SQLAlchemy model.
            mapper: SQLAlchemy mapper property object.

        Returns:
            None
        """

        column_type = mapper.property.columns[0].type

        # Skip attributes that start with an underscore
        if attribute.startswith("_") and get_config_or_model_meta("API_IGNORE_UNDERSCORE_ATTRIBUTE", default=True):
            return

        # Determine the Marshmallow field type based on the SQLAlchemy column type
        field_type = type_mapping.get(type(column_type))
        if field_type is None:
            return

        # Collect additional field attributes from the SQLAlchemy column
        field_args = {}
        column = self.model.__table__.columns.get(original_attribute)
        is_pk = False
        if column is not None:
            if not column.nullable and (not column.primary_key and column.autoincrement and column.default is None):
                field_args["required"] = True
            if column.default is not None:
                field_args["default"] = (
                    column.default.arg if not callable(column.default.arg) else None
                )
            if hasattr(column_type, "length"):
                field_args["validate"] = Length(max=column_type.length)
            if column.unique or column.primary_key:
                # You can add more logic here to handle unique validation
                field_args["unique"] = True
            is_pk = column.primary_key
            # Add the field to the Marshmallow schema

        self.fields[original_attribute] = field_type(data_key=attribute, **field_args)

        # mark the field as dump_only if it is an auto incrementing primary key
        if mapper.autoincrement is True or mapper.default:
            self.fields[original_attribute].dump_only = True

        self.fields[original_attribute].dump_default = missing
        # this is set
        if is_pk:
            self.fields[original_attribute].metadata["is_pk"] = is_pk

        self.fields[original_attribute].parent = self
        self.fields[original_attribute].name = attribute
        self.fields[original_attribute].metadata.update(
            get_openapi_meta_data(self.fields[original_attribute])
        )

    def add_relationship_field(self, attribute, original_attribute, relationship_property):
        """
        Automatically add a field for a given relationship in the SQLAlchemy model.
        Args:
            attribute (str): The name of the attribute to add to the schema.
            original_attribute (str): The original attribute name from the SQLAlchemy model.
            relationship_property (RelationshipProperty): The SQLAlchemy relationship property object.

        Returns:

        """
        _, rel_type = _get_relation_use_list_and_type(relationship_property)


        serialization_type = get_config_or_model_meta("API_SERIALIZATION_TYPE", default="hybrid")
        nested_schema = get_input_output_from_model_or_make(relationship_property.mapper.class_)[1]
        matching = find_matching_relations(self.Meta.model, nested_schema.Meta.model)[0]

        if (serialization_type == "json" or (rel_type[-3:] == "ONE" and serialization_type == "hybrid")) and self.depth <= 1:

            # If within allowed depth, serialize fully
            logger.debug(3,f"Serialization type is `{serialization_type} - Serializing -{nested_schema.__name__}- relations to JSON`")
            # nested_schema.depth = self.depth + 1
            # nested_schema.parent = self

            if rel_type[-3:] == "ONE":
                self.fields[original_attribute] = fields.Nested(nested_schema, data_key=attribute, attribute=attribute, dump_only=True, many=False)
            else:
                self.fields[original_attribute] = fields.Nested(nested_schema, many=True,
                                                                data_key=attribute, attribute=attribute, dump_only=True)

        elif serialization_type == "url" or (rel_type[-4:] == "MANY" and serialization_type == "hybrid"):
            logger.debug(3,f"Serialization type is `{serialization_type} - Serializing -{nested_schema.__name__}- relations to URL`")
            def serialize_to_url(obj):
                # Your logic here

                namer = get_config_or_model_meta("API_ENDPOINT_NAMER", default=endpoint_namer)
                if hasattr(obj, namer(nested_schema.Meta.model) + "_to_url"):
                    return getattr(obj, namer(nested_schema.Meta.model) + "_to_url")()
                elif hasattr(obj, matching[0] + "to_url"):
                    return obj.to_url()
                return None

            self.fields[original_attribute] = fields.Function(serialize_to_url, data_key=attribute)

        if self.fields.get(original_attribute):
            self.fields[original_attribute].parent = self
            self.fields[original_attribute].name = attribute
            self.fields[original_attribute].metadata.update(get_openapi_meta_data(self.fields[original_attribute]))

    def _make_not_required(self):
        """Makes all fields optional except the primary key."""
        from flask_scheema.api.utils import get_primary_keys
        primary_key_field = get_primary_keys(self.Meta.model)
        for field_name, field_obj in self.fields.items():
            if field_name != primary_key_field:
                field_obj.required = False

    # def _update_instance(self, loaded_data):
    #     """Updates an existing SQLAlchemy model instance."""
    #     from flask_scheema.api.utils import get_primary_keys
    #     primary_key_column = get_primary_keys(self.Meta.model)
    #     primary_key_value = loaded_data.get(primary_key_column)
    #
    #     if primary_key_value is None:
    #         raise ValidationError(
    #             f"Primary key {primary_key_column} must be present for {request.method} operations.")
    #
    #     session = self.Meta.model.get_session()
    #     instance = session.query(self.Meta.model).first()
    #
    #     if instance is None:
    #         raise ValidationError(f"Resource with primary key {primary_key_value} not found.")
    #
    #     for key, value in loaded_data.items():
    #         setattr(instance, key, value)
    #
    #     return instance

    def dump(self, obj, *args, **kwargs):
        """Custom serialization for SQLAlchemy model instances."""
        kwargs.setdefault("many", isinstance(obj, list))
        return super().dump(obj, *args, **kwargs)

    def load(self, data, *args, **kwargs):
        """Custom deserialization for SQLAlchemy model instances."""
        output_as_dict = kwargs.pop("output_as_dict", False)
        is_update = request.method in ["PUT", "PATCH"]

        if hasattr(self.Meta, "model") and self.Meta.model:
            if is_update:
                self._make_not_required()

            loaded_data = super().load(data, *args, **kwargs)

            # if is_update:
            #     return self._update_instance(loaded_data)

            if not output_as_dict:
                return self.Meta.model(**loaded_data)

        return loaded_data
