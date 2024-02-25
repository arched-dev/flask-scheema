from flask import Flask

from demo.model_extension.model.config import Config
from demo.model_extension.model.extensions import db, scheema
from demo.model_extension.helpers import load_dummy_database


def create_app(config: dict = None):
    """
    Creates the flask app.
    Args:
        config (Optional[dict]): The configuration dictionary.

    Returns:

    """
    app = Flask(__name__)
    app.config.from_object(Config)
    if config:
        app.config.update(config)

    db.init_app(app)

    with app.app_context():
        from demo.basic.basic.models import Category, Book, Publisher, Author, Review
        db.create_all()
        load_dummy_database(db)
        scheema.init_app(app)

    return app
