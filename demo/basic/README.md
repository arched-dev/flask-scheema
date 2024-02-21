# Demo - Flask-Scheema

## Basic

To spin up your first API using flask-scheema, you need to change your flask app very little to get a fully functioning 
API along with an OpenAPI redoc documentation page.

1) Appy a few flask config values   [Example](https://github.com/arched-dev/sample-repo/blob/main/example.py#L10)
2) Add a `Meta` class to your sqlalchemy models.  [Example](https://github.com/user123/sample-repo/blob/main/example.py#L10)
3) Initialise the `FlaskScheema` class with your app  [Example](https://github.com/user123/sample-repo/blob/main/example.py#L10)

```python

Required flask Config values are:

    API_BASE_MODEL = db.Model
    API_TITLE = "Book Shop API"
    API_VERSION = "0.1.0"
