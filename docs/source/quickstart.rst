Quick Start
=========================================


Installation
-----------------------------------------

Install the package via pip

.. code:: bash

    pip install flask-scheema


Model Definition
-----------------------------------------

To enable **flask-scheema** to automatically generate API endpoints, it's necessary to provide it with a valid
`SQLAlchemy`_ session and ensure it can interact with the models designated for API exposure.

This requirement is fulfilled by establishing a base class from which all relevant models will derive.
Additionally, integrating a method named ``get_session`` is essential, as it will facilitate the retrieval of
a SQLAlchemy session.

.. tab-set::

    .. tab-item:: flask-sqlalchemy
        :sync: key1

        When using flask-sqlalchemy, you can return ``db.session`` in your base model.

        .. code:: python

            from sqlalchemy.ext.declarative import declarative_base

            class BaseModel(DeclarativeBase):
                def get_session(*args):
                    return db.session


        Make sure any model you want to expose has a class attribute called ``Meta`` with the following attributes:

        - ``tag``: The tag that will be used to identify the model in the API and documentation.
        - ``tag_group``: The tag group that the model will be placed in in the API Documentation.

        Don't inherit from your base model, but from ``db.Model`` as you normally would. When using `Flask-SQLAlchemy`_,
        you set the base model when initializing the extension.

        .. code:: python

            class Author(db.Model):
                __table__ = "author"
                class Meta:
                    tag = 'Author'
                    tag_group = "People/Companies"

                ...fields


    .. tab-item:: vanilla sqlalchemy
        :sync: key2

        When using sqlalchemy, you will have to create a session object and return this in your base model.

        .. code:: python

            from sqlalchemy import create_engine
            from sqlalchemy.ext.declarative import declarative_base
            from sqlalchemy.orm import sessionmaker

            # Define the SQLite engine to use a local file-based database
            engine = create_engine('sqlite:///example.db', echo=True)

            # Generate a base class for your class definitions
            Base = declarative_base()

            # Create a Session class bound to the engine
            Session = sessionmaker(bind=engine)

            # Now you can create a session instance
            session = Session()




        .. code:: python

            class BaseModel(DeclarativeBase):

                def get_session(*args):
                    return session

        Make sure any model you want to expose inherits from the correct base, and has a class attribute ``Meta`` with
        the following attributes:

        - ``tag``: The tag that will be used to identify the model in the API and documentation.
        - ``tag_group``: The tag group that the model will be placed in in the API Documentation.


        .. code:: python

            class Author(BaseModel):
                __table__ = "author"
                class Meta:
                    tag = 'Author'
                    tag_group = "People/Companies"

                ...fields

        Due to the default settings in ``flask-scheema`` being set to `Flask-SQLAlchemy`_'s ``db.session``, you will
        have to set a `Flask`_ config of ``API_BASE_MODEL`` with the name of your base model.

        i.e

        .. code:: python

            app.config['API_BASE_MODEL'] = 'BaseModel'


Extension Initialization
-----------------------------------------

To initialize the extension, it's necessary to provide it with a valid `Flask`_ application instance as with many other
`Flask`_ extensions.

The only other requirement's are two configuration values that need to be passed to `Flask`_.

- ``API_TITLE``: The title of the API that will be displayed in the documentation.
- ``API_VERSION``: The version of the API that will be displayed in the documentation.


.. code:: python

    from flask import Flask

    # Import your models
    from models import Author

    app = Flask(__name__)

    app.config['API_TITLE'] = 'My API
    app.config['API_VERSION'] = '1.0'

    from flask_scheema import Naan

    with app.app_context():
        db = SQLAlchemy(app=app, model_class=BaseModel)
        scheema = Naan(app)

    if __name__ == '__main__':

        app.run(debug=True)


API Documentation
-----------------------------------------

That's it! You should now have a fully functional API with documentation.

``GET`` /docs


Queries
-----------------------------------------

Writing API calls is simple, and can be done in the following way:

``GET`` /api/author - returns a list of paginated authors.

``GET`` /api/author/1 - returns the author with the id of 1.

``POST`` /api/author - creates a new author.

``PATCH`` /api/author/1 - updates the author with the id of 1.

``DELETE`` /api/author/1 - deletes the author with the id of 1.


While more advanced queries can be made by adding query parameters to the URL and is fully documented in the
documentation.
