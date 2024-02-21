.. _quickstart:

Quick Start
===========

.. currentmodule:: flask_scheema

Flask-scheema simplifies API creation and speeds up prototyping or development by automatically reading your SQLAlchemy
database models and generating schemas, flask routes with structured API output and API documentation powered by redoc.

This page will walk you through the basic use of Flask-Scheema. You can find more examples in the `demo` directory if
you want to dive straight into working examples.


Installation
------------

Flask-Scheema is available on `PyPI`_ and can be installed with various Python tools.
For example, to install or update the latest version using pip:

.. code-block:: text

    $ pip install -U Flask-SQLAlchemy

.. _PyPI: https://pypi.org/project/Flask-SQLAlchemy/


Basic Usage
------------

To create your first API with `flask-scheema` you need just make 3 changes to your normal flask pattern.


## SQLAlchemy Models

SQLAlchemy database models need to inherit from a base model that has a `get_session` method - this is needed to correctly
create routes gives the flexability to use `flask-sqlalchemy` or vanilla `SQLAlchemy`.

.. code-block:: python

    class BaseModel(DeclarativeBase):
        def get_session(*args):
            return db.session


## Flask Config

A few required flask config files are needed.

.. code-block:: python

    class Config:




.. _PyPI: https://pypi.org/project/Flask-SQLAlchemy/
