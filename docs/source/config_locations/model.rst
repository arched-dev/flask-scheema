Config Models
==============================

    Global < Global Method < **Model** < Model Method

:bdg-dark-line:`Model`

These values are defined as Meta class attributes in you `SQLAlchemy`_ models.

-  They should always be lowercase
-  They should always omit any ``API_`` prefix.

Values defined here will apply per model and can only be overridden by the a :bdg-dark-line:`Model Method` config
values.

Overrides :bdg-dark-line:`Global`, :bdg-dark-line:`Global Method`

Example
--------------

.. code:: python

    class Author():

        __table__ = "author"

        class Meta:
            tag_group = "People"
            tag_group = "Author"
            description = "Models an author of a book"
            rate_limit = "10 per minute"
