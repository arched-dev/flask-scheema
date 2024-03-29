# Quick Start Guide for Flask-Schema

## Introduction

Jumpstart your API development with `flask-scheema` by integrating it into your Flask application. This guide walks you
through setting up a robust API complete with an automatically generated OpenAPI documentation page, all with minimal
changes to your existing Flask setup.

## Getting Started

Follow these steps to integrate `flask-scheema` into your Flask application and enjoy a fully functional API alongside
comprehensive OpenAPI Redoc documentation.

## Implementing DeclarativeBase for Flask-SQLAlchemy Integration

Ensure your models derive from a base class that provides a get_session method for database access. This setup is
crucial for the API's ability to generate accurate schemas and perform database queries.

- Extend DeclarativeBase and utilize `flask-SQLAlchemy` for seamless
  integration. [View Example](https://github.com/arched-dev/flask-scheema/blob/master/demo/basic/basic/extensions.py#L10-L25)

For `flask-SQLAlchemy` users, the following implementation is recommended:

```python
from sqlalchemy.orm import DeclarativeBase

class BaseModel(DeclarativeBase):
    def get_session(*args):
        # Your base model must include a 'get_session' method returning a SQLAlchemy session.
        return db.session
    
db = SQLAlchemy(model_class=BaseModel)
```

All models should inherit from `db.Model` as usual, with model_class handling the necessary integration.

## Flask Configuration Requirements

Introduce a few configuration values to Flask to enable `flask-scheema` functionalities.

- Set necessary Flask configuration
  values.  [View Example](https://github.com/arched-dev/flask-scheema/blob/master/demo/basic/basic/config.py#L6-L8)

Your application's Flask configuration must specify the following values:

```python
API_BASE_MODEL = db.Model  # Use your base model here. Flask-SQLAlchemy users should specify db.Model.
API_TITLE = "Your API Title"
API_VERSION = "Your API Version"
```

## Initialize Flask-Scheema

With all extensions set up, instantiate `flask-scheema` using your app's `app_context`. This step should follow the
initialization of other extensions.

Examples:

- Initialize `flask-scheema` in your extensions'
  setup. [View Example](https://github.com/arched-dev/flask-scheema/blob/master/demo/basic/basic/extensions.py#L26)
- Further initialization within your app's
  context. [View Example](https://github.com/arched-dev/flask-scheema/blob/master/demo/basic/basic/__init__.py#L28)

## Model Meta Class Attributes

Enhance your `SQLAlchemy` models by adding a Meta class to organize documentation tags effectively
specifying `tag_group` and `tag`:

```python
class Meta:
    tag_group = "Descriptive Group Name"
    tag = "Specific Tag"
```

-----------------------------

With these steps completed, run your application and navigate to the `/docs` route to explore your API's documentation.

This refined approach clarifies the setup process, emphasizing essential steps and configurations for
integrating `flask-scheema` into your Flask application.
