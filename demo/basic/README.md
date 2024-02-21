# Demo - Flask-Scheema

## Basic

To spin up your first API using flask-scheema, you need to change your flask app very little to get a fully functioning 
API along with an OpenAPI redoc documentation page.

1) Appy a few flask config values   [Example](https://github.com/arched-dev/flask-scheema/blob/master/demo/basic/basic/config.py#L12-L14)
2) Add a `Meta` class to your sqlalchemy models.   [Example1](https://github.com/arched-dev/flask-scheema/blob/master/demo/basic/basic/models.py#L32-L36)
3) Initialise the `FlaskScheema` class with your apps `app_context` after all other extensions have been created and initialised [Example](https://github.com/arched-dev/flask-scheema/blob/master/demo/basic/basic/extensions.py#L26) [Example1](https://github.com/arched-dev/flask-scheema/blob/master/demo/basic/basic/__init__.py#L28)

```python

Required flask Config values are:

    API_BASE_MODEL = db.Model
    API_TITLE = "Book Shop API"
    API_VERSION = "0.1.0"
