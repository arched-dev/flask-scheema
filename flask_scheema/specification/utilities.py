import os

from jinja2 import Environment, FileSystemLoader


def generate_readme_html(file_path: str, *args, **kwargs):
    """
    Generate a readme.MD file in the parent directory of the html' folder.


    Args:
        file_path: The path to the Jinja2 template file.
        *args: Variable length argument list.
        **kwargs: Arbitrary keyword arguments.

    Returns:
        The path to the readme.MD file.

    """

    # Locate the template directory containing the file
    template_dir = os.path.abspath(os.path.split(file_path)[0])


    # Set up the Jinja2 environment and load the template
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template(os.path.split(file_path)[-1])

    # Fetch config data to be used in the template

    # Render the template with the data

    rendered_content = template.render(*args, **kwargs)

    # Write the rendered content to readme.MD in the parent directory of the html folder
    readme_path = os.path.join(os.path.dirname(template_dir), "readme.MD")
    with open(readme_path, "w") as file:
        file.write(rendered_content)

    return readme_path


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
