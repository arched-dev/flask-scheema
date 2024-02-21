from flask import Flask

from demo.model_extension.helpers import load_dummy_database
from demo.model_extension.models.config import Config
from demo.model_extension.models.extensions import db, scheema


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
        db.create_all()
        load_dummy_database(db)
        scheema.init_app(app)

    return app
