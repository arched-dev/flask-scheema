.. rst-class:: hide-header

flask-scheema
================


.. image:: _static/logo.png
    :align: center
    :width: 50%

Flask-schema is a powerful extension designed for `Flask`_, `SQLAlchemy`_ and `Marshmallow`_ , which offers an innovative
solution for rapidly developing APIs and API documentation.

This extension leverages your existing database schema to automatically generate a functional API, complete with
comprehensive documentation using `Redoc`_.

Whether you're aiming to build a prototype or develop a full-scale API, this tool significantly reduces development time
and effort. It scans your database schema and constructs an API that aligns perfectly with your data structures,
ensuring consistency and efficiency.

A title
-------

This is another section,This is another section, This is another section, This is another section, This is another
section, This is another section, This is another section, This is another section,This is another section, This is
another section, This is another section, This is another section, This is another section, This is another section,
This is another section,This is another section, This is another section, This is another section, This is another
section, This is another section, This is another section, This is another section,This is another section, This is
another section, This is another section, This is another section, This is another section, This is another section,
This is another section,This is another section, This is another section, This is another section, This is another
section, This is another section, This is another section, This is another section,This is another section, This is
another section, This is another section, This is another section, This is another section, This is another section,
This is another section,This is another section, This is another section, This is another section, This is another
section, This is another section, This is another section, This is another section,This is another section, This is
another section, This is another section, This is another section, This is another section, This is another section,
This is another section,This is another section, This is another section, This is another section, This is another
section, This is another section, This is another section, This is another section,This is another section, This is
another section, This is another section, This is another section, This is another section, This is another section,

A second title
--------------
This is another section,This is another section, This is another section, This is another section, This is another
section, This is another section, This is another section, This is another section,This is another section, This is
another section, This is another section, This is another section, This is another section, This is another section,
This is another section,This is another section, This is another section, This is another section, This is another
section, This is another section, This is another section, This is another section,This is another section, This is
another section, This is another section, This is another section, This is another section, This is another section,
This is another section,This is another section, This is another section, This is another section, This is another
section, This is another section, This is another section, This is another section,This is another section, This is
another section, This is another section, This is another section, This is another section, This is another section,
This is another section,This is another section, This is another section, This is another section, This is another
section, This is another section, This is another section, This is another section,This is another section, This is
another section, This is another section, This is another section, This is another section, This is another section,
This is another section,This is another section, This is another section, This is another section, This is another
section, This is another section, This is another section, This is another section,This is another section, This is
another section, This is another section, This is another section, This is another section, This is another section,

This is the thing.

It refers to the section title, see :ref:`A title`.

.. tip::
   This is a tip.

.. important::
   This is important information.

.. hint::
   This is a hint.

.. note::
   This is a note.

.. admonition:: Example Model

    Basic SQLAlchemy model

.. note::
   This is a note that will stand out from the rest of the text.

    This is a block quote.

.. code-block:: python

    def hello_world():
        print("Hello, world!")

    hello_world()


.. code-block:: python

    def hello_world():
        print("Hello, world!")

    hello_world()


.. class:: Naan

Moreover, Flask-schema is highly customizable. It integrates seamlessly with Flask's configuration system and supports
the use of meta-classes. This flexibility allows developers to fine-tune the API's behavior and output, ensuring that
the final product aligns with specific project requirements and standards.

Generated API documentation is a key feature of Flask-schema. Utilizing `Redoc`_, it produces clear,
interactive, and user-friendly documentation.

Flask-schema can be an indispensable tool for developers working with `Flask`_ and `SQLAlchemy`_. It offers a blend
of automation, customization, and documentation, making it an ideal choice for both rapid prototyping and the
development of robust, fully-functional APIs.


.. admonition:: Note on initialization order

    Flask-SQLAlchemy **must** be initialized before Flask-Marshmallow.


:menuselection:`Start --> Programs`


+------------------------+------------+----------+----------+
| Header row, column 1   | Header 2   | Header 3 | Header 4 |
| (header rows optional) |            |          |          |
+========================+============+==========+==========+
| body row 1, column 1   | column 2   | column 3 | column 4 |
+------------------------+------------+----------+----------+
| body row 2             | ...        | ...      |          |
+------------------------+------------+----------+----------+


.. _SQLAlchemy: https://www.sqlalchemy.org/
.. _Flask: https://flask.palletsprojects.com/
.. _SQLAlchemy documentation: https://docs.sqlalchemy.org/
.. _Marshmallow: https://github.com/marshmallow-code/marshmallow/
.. _Redoc: https://github.com/Redocly/redoc/


User Guide
----------

.. toctree::
    :maxdepth: 2

    quickstart


API Reference
-------------

.. toctree::
   :maxdepth: 2
   :glob:

   api/*

Additional Information
----------------------

.. toctree::
    :maxdepth: 2

    licence
    changes
