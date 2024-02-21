import os.path

from demo.model_extension.models import db
from flask_scheema.specification.utilities import (
    read_readme_content_to_string, generate_readme_html,
)


class Config:
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    API_BASE_MODEL = db.Model  # if you are using flask-sqlalchemy then use db.model
    API_TITLE = "Book Shop API"
    API_VERSION = "0.1.0"
    API_VERBOSITY_LEVEL = 4
    API_AUTHENTICATE = False
    SECRET_KEY = "8Kobns1_vnmg3rxnr0RZpkF4D1s"
