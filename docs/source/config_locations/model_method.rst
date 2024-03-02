Config by Method Models
==============================

    Global < Global Method < Model < **Model Method**

:bdg-dark-line:`Model Method`

These values are defined as Meta class attributes in you `SQLAlchemy`_ models, and configure specific behavior per
`HTTP method`_ for a specific model.

-  They should always be lowercase
-  They should always omit any ``API_`` prefix.
-  They should be prefixed with the http method you want to configure. i.e ``get_``, ``post_``, ``patch_``, ``delete_``

Values defined here will apply per model / http method and can not be overridden.

Example
--------------

.. code:: python

    class Author():

        __table__ = "author"

        class Meta:
            get_description = "Models an author of a book"
            post_rate_limit = "10 per minute"
            get_authenticate = True
            post_authenticate = False
            patch_authenticate = False
