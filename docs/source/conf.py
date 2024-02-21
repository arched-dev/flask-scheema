# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
import os
import sys

from pallets_sphinx_themes import ProjectLink

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project_dir = os.path.abspath("../../flask_scheema/")
sys.path.insert(0, project_dir)
sys.path.insert(0, os.path.abspath("../../"))

project = "flask-scheema"
copyright = "2024, Lewis Morris"
author = "Lewis Morris"
release = "0.1.1"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "pallets_sphinx_themes",
    "sphinx.ext.autodoc",  # Include documentation from docstrings
    "sphinx.ext.viewcode",  # Add links to highlighted source code
    "sphinx.ext.todo",
    "sphinx.ext.napoleon",
    "sphinx_copybutton",
    "sphinx.ext.autosectionlabel",
]

templates_path = ["_templates"]
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "flask"
html_static_path = ["_static"]
html_title = "flask-scheema"

html_context = {
    "project_links": [
        ProjectLink("PyPI Releases", "https://pypi.org/project/flask-scheema/"),
        ProjectLink("Source Code", "https://github.com/lewis-morris/flask-scheema/"),
        ProjectLink(
            "Issue Tracker", "https://github.com/lewis-morris/flask-scheema/issues/"
        ),
    ]
}

html_sidebars = {
    "index": ["project.html", "localtoc.html", "searchbox.html"],
    "**": ["localtoc.html", "relations.html", "searchbox.html"],
}
singlehtml_sidebars = {"index": ["project.html", "localtoc.html"]}


napoleon_google_docstring = True

autodoc_typehints = "description"

# Don't show class signature with the class' name.
autodoc_class_signature = "separated"
