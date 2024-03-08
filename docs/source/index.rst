Flask-Scheema
=========================================

.. toctree::
   :hidden:
   :maxdepth: 2
   :caption: Contents:

   installation
   quickstart
   models
   authentication
   callbacks
   configuration
   faq
   genindex


keema-naan == bread, flask-scheema.naan == api

.. image:: /_static/coverage.svg
   :alt: Coverage Report
   :width: 100px
   :align: center

.. image:: https://img.shields.io/github/license/arched-dev/flask-scheema
   :alt: GitHub License

.. image:: https://img.shields.io/pypi/dm/flask-scheema
   :alt: PyPI - Downloads

.. image:: https://badgen.net/static/Repo/Github/blue?icon=github&link=https%3A%2F%2Fgithub.com%2Farched-dev%2Fflask-scheema
   :alt: GitHub Repo
   :target: https://github.com/arched-dev/flask-scheema



--------------------------------------------



**Flask-Scheema** automatically creates rapid, production ready API's directly from `SQLAlchemy`_ models with
accompanying `Redoc`_ documentation, all with little to no effort.

By adding **flask-scheema** to your `Flask`_ application, you can be up and running in seconds, leaving you time to focus on
what really matters.

What can it do?

* Automatically detect and create endpoints, with model relationships & hybrid properties.

* Create detailed API outputs.

* Authenticate users with a variety of methods.

* Global or model based configuration including callbacks, rate limiting, caching & more.

* Automatically generated `Redoc`_ documentation.

All fully configurable through `Flask`_ config values all the way through to http method based configuration your models,
giving you fine grained control over the output of your API and accompanying documentation.

What are you waiting for...?

Turn this.

.. code:: python

    class Book(db.Model):

        id = db.Column(db.Integer, primary_key=True)
        title = db.Column(db.String(80), unique=True, nullable=False)
        author = db.Column(db.String(80), nullable=False)
        published = db.Column(db.DateTime, nullable=False)



Into this:

``GET /api/books``

.. code:: json

    {
      "datetime": "2024-01-01T00:00:00.0000+00:00",
      "apiVersion": "0.1.0",
      "statusCode": 200,
      "responseMs": 15,
      "totalCount": 10,
      "nextUrl": "/api/authors?limit=2&page=3",
      "previousUrl": "/api/authors?limit=2&page=1",
      "error": "null",
      "value": [
        {
          "author": "John Doe",
          "id": 3,
          "published": "2024-01-01T00:00:00.0000+00:00",
          "title": "The Book"
        },
        {
          "author": "Jane Doe",
          "id": 4,
          "published": "2024-01-01T00:00:00.0000+00:00",
          "title": "The Book 2"
        }
      ]
    }


Let's get started!

`Quick Start <link>`__

`View Demos <link>`__
