import os
import pprint

from jinja2 import Environment, FileSystemLoader

from flask_scheema.api.utils import convert_case
from flask_scheema.scheema.utils import convert_snake_to_camel
from flask_scheema.utilities import get_config_or_model_meta


def search_all_keys(model, key):

    for model in model.__subclasses__():
        for method in ["GET", "POST", "PATCH", "DELETE"]:
            config = get_config_or_model_meta(key, model=model, method=method)
            if config:
                return True


def generate_readme_html(file_path: str, *args, **kwargs):
    """
    Generate a readme content from a Jinja2 template.

    Args:
        file_path: The path to the Jinja2 template file.
        *args: Variable length argument list.
        **kwargs: Arbitrary keyword arguments.

    Returns:
        The rendered content as a string.
    """

    # Locate the template directory containing the file
    template_dir = os.path.abspath(os.path.split(file_path)[0])

    # Set up the Jinja2 environment and load the template
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template(os.path.split(file_path)[-1])

    # Render the template with the data
    rendered_content = template.render(*args, **kwargs)

    # Return the rendered content
    return rendered_content


def read_readme_content_to_string(path: str):
    """
    Get the content of the readme.MD file, starting at the calling functions directory and moving up the directory tree
    until the file is found.


    Args:
        path: The path to the readme.MD file.

    Returns:
        The content of the readme.MD file.
    """

    # Get the path of the script that called this function

    # If found, read and return its content
    if os.path.exists(path):
        with open(path, "r") as f:
            return f.read()

    # If not found, return a default message or raise an error
    return "readme.MD not found."


def case_no_change(s):
    return s


def pretty_print_dict(d):
    return pprint.pformat(d, indent=2)


def make_base_dict():
    output = {"value": "..."}

    field_case = get_config_or_model_meta("API_FIELD_CASE", default="snake_case")

    dump_datetime = get_config_or_model_meta("API_DUMP_DATETIME", default=True)
    if dump_datetime:
        output.update(
            {convert_case("datetime", field_case): "2024-01-01T00:00:00.0000+00:00"}
        )

    dump_version = get_config_or_model_meta("API_DUMP_VERSION", default=True)
    if dump_version:
        output.update(
            {
                convert_case("api_version", field_case): get_config_or_model_meta(
                    "API_VERSION", default=True
                )
            }
        )

    dump_status_code = get_config_or_model_meta("API_DUMP_STATUS_CODE", default=True)
    if dump_status_code:
        output.update({convert_case("status_code", field_case): 200})

    dump_response_time = get_config_or_model_meta(
        "API_DUMP_RESPONSE_TIME", default=True
    )
    if dump_response_time:
        output.update({convert_case("response_ms", field_case): 15})

    dump_count = get_config_or_model_meta("API_DUMP_COUNT", default=True)
    if dump_count:
        output.update({convert_case("total_count", field_case): 10})

    dump_null_next_url = get_config_or_model_meta(
        "API_DUMP_NULL_NEXT_URL", default=True
    )
    if dump_null_next_url:
        output.update({convert_case("next_url", field_case): "/api/example/url"})

    dump_null_previous_url = get_config_or_model_meta(
        "API_DUMP_NULL_PREVIOUS_URL", default=True
    )
    if dump_null_previous_url:
        output.update({convert_case("previous_url", field_case): "null"})

    dump_null_error = get_config_or_model_meta("API_DUMP_NULL_ERRORS", default=False)
    if dump_null_error:
        output.update({convert_case("errors", field_case): "null"})

    return output
