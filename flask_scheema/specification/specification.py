import os
from typing import Optional

from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from flask import Blueprint, Flask

from flask_scheema.specification.doc_generation import (
    register_routes_with_spec,
)
from flask_scheema.specification.utilities import read_readme_content_to_string, generate_readme_html
from flask_scheema.utilities import (
    AttributeInitializerMixin,
    get_config_or_model_meta,
    find_child_from_parent_dir,
    manual_render_absolute_template,
)


class CurrySpec(APISpec, AttributeInitializerMixin):
    """
    This is a subclass of APISpec that allows for the specification of the tag groups.
    """

    app: Flask
    naan: "Naan"  # The naan object

    spec_groups: dict = {"x-tagGroups": []}  # Dictionary to hold tag groups
    api_title: Optional[str] = ""  # The title of the api
    api_version: Optional[str] = ""  # The version of the api
    api_description: Optional[str] = None  # The description of the api
    api_logo_url: Optional[str] = None  # The url of the API logo
    api_logo_background: Optional[
        str
    ] = None  # The background colour of the API logo (in hex) if the logo is transparent
    api_keywords: Optional[list] = []  # The keywords for the api
    create_api_docs: Optional[bool] = True  # Whether to create the api docs
    documentation_url_prefix: Optional[str] = "/"  # The url prefix for the docs
    documentation_url: Optional[str] = "/docs"

    def __init__(self, app: Flask, naan: "Naan", *args, **kwargs):
        """
                Initializes the api spec object.

        Args:
                    naan (Naan): The naan object.
                    **kwargs (dict): Dictionary of keyword arguments that are passed to the APISpec object.
        """
        self.app = app
        self.naan = naan
        AttributeInitializerMixin.__init__(self, app=naan.app, *args, **kwargs)

        if self.create_api_docs:
            # Set the naan object, the main flask_scheema object

            # Validate the api spec arguments
            self.validate_init_apispec_args()

            # Initialize parent classes
            super().__init__(
                *args,
                **{**self.make_api_spec_data(), **kwargs},
            )

            # Create the api spec blueprint and routes to serve the docs
            self.create_specification_blueprint()

            self.naan.api_spec = self
            register_routes_with_spec(
                self.naan,
                self.naan.route_spec,
            )

    def to_dict(self) -> dict:
        """
        Returns the api spec object as a dictionary.
        Returns:
            dict: The api spec object as a dictionary.
        """
        spec_dict = super().to_dict()
        spec_dict.update(self.spec_groups)
        return spec_dict

    def make_api_spec_data(self) -> dict:
        """
        Creates the data for the api spec object.

        Returns:
            dict: The data for the api spec object.

        """
        api_description = self.api_description or get_config_or_model_meta("API_DESCRIPTION", default=os.path.abspath("./basic/templates/readme.MD.j2"))
        if os.path.isfile(api_description):
            api_description = read_readme_content_to_string(generate_readme_html(api_description, config=self.naan.app.config))

        api_spec_data = {
            "openapi_version": "3.0.2",
            "plugins": [MarshmallowPlugin()],
            "title": self.api_title
            or get_config_or_model_meta("API_TITLE", default="My API"),
            "version": self.api_version
            or get_config_or_model_meta("API_VERSION", default="1.0.0"),
            "info": {"description": api_description},
        }

        if self.api_logo_url:
            api_spec_data["info"]["x-logo"] = {
                "url": self.api_logo_url or get_config_or_model_meta("API_LOGO_URL"),
                "backgroundColor": self.api_logo_background
                or get_config_or_model_meta("API_LOGO_BACKGROUND", "#ffffff"),
                "altText": self.api_title + " logo.",
            }

        return api_spec_data

    def validate_init_apispec_args(self):
        """
                Validates the arguments for the api spec object.

        Args:
                    **kw
        Args:
        """
        # Add your validation logic here
        # For example, to ensure 'title' is a string and not empty
        if not isinstance(self.api_title, str):
            raise ValueError("Title must be a string.")
        if self.api_title == "":
            raise ValueError("Title must not be empty.")
        if not isinstance(self.api_version, str):
            raise ValueError("Version must be a string.")
        if self.api_version == "":
            raise ValueError("Version must not be empty.")

    def set_xtags_group(self, tag_name: str, group_name: str):
        """
                Adds endpoint tag to a tag-group, creating the group if it doesn't exist.

                This is used to group endpoint tags in the docs.


        Args:
                    tag_name (str): Name of the tag to add, this should have already been registered.
                    group_name (str): Name of the group to add the tag to.

                Returns:
                    None

                Examples:
                    >>> spec.set_xtags_group("Users", "Authentication")
                    >>> spec.set_xtags_group("Users", "Profile")
                    >>> spec.set_xtags_group("Users", "Address")

                Documentation:
                    https://redocly.com/docs/api-reference-docs/specification-extensions/x-tag-groups/
        """

        # Initialize x-tagGroups if it doesn't exist
        if "x-tagGroups" not in self.spec_groups:
            self.spec_groups["x-tagGroups"] = []

        # Check if the group already exists
        existing_group = None
        for group in self.spec_groups["x-tagGroups"]:
            if group["name"] == group_name:
                existing_group = group
                break

        if existing_group:
            # Add the tag to the existing group, checking for duplicates
            if tag_name not in existing_group["tags"]:
                existing_group["tags"].append(tag_name)
        else:
            # Create a new group with the current tag
            new_group = {"name": group_name, "tags": [tag_name]}
            self.spec_groups["x-tagGroups"].append(new_group)

    def create_specification_blueprint(self, url_prefix=None):
        """
                Sets up the blueprint for the api specification and to serve the redoc docs.

        Args:
                    url_prefix (str): The url prefix for the blueprint.

                Returns:
                    Blueprint: The blueprint for the api specification.

        """
        current_path = os.path.split(os.path.abspath(__file__))[0]

        html_path = find_child_from_parent_dir(
            "src",
            "html",
            current_dir=current_path,
        )
        # Set the url prefix if it is specified
        url_prefix = url_prefix or get_config_or_model_meta(
            "DOCUMENTATION_URL_PREFIX", default="/"
        )

        # Create the blueprint
        specification = Blueprint(
            "specification",
            __name__,
            static_folder=html_path,
            url_prefix=url_prefix,
        )

        documentation_url = get_config_or_model_meta(
            "API_DOCUMENTATION_URL", default="/docs"
        )

        @specification.route("swagger.json")
        def get_swagger_spec():
            """
            Returns the swagger spec json object.
            Returns:
                dict: The swagger spec json object.

            """
            return self.naan.to_api_spec()

        @specification.route(documentation_url)
        @specification.route(documentation_url + "/")
        def get_docs():
            """
            Returns the docs page.
            Returns:
                str: The docs page.
            """
            return manual_render_absolute_template(
                os.path.join(
                    self.naan.get_templates_path(),
                    "apispec.html",
                ),
                config=self.app.config
            )

        self.naan.app.register_blueprint(specification)
