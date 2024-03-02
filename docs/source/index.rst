Flask-Scheema
=========================================

.. toctree::
   :hidden:
   :maxdepth: 2
   :caption: Contents:

   installation
   quickstart
   models
   configuration
   authentication
   callbacks
   genindex

keema-naan == bread, flask-scheema == api

--------------------------------------------


**Flask-Scheema** automatically creates rapid, production ready API's directly from `SQLAlchemy`_ models with
accompanying ``redoc`` documentation, with little to no effort.

By adding this extension to your `Flask`_ application, you can be up and running in seconds, leaving you time to focus on
what really matters.

Complete with; detailed API output, authentication methods, rate limiting, caching, `Redoc`_ documentation.

Fully configurable through `Flask`_ config values or Meta classes in your models, meaning you have fine grained control over
the output of your API and accompanying documentation.

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
