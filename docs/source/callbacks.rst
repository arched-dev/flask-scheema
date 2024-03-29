Callbacks
=========================================

While accessing and updating your models via the API **flask-schema** has created is great. Sometimes you need to
perform some additional logic before or after a model is returned, created, updated, deleted or if an error is raised.

You might need to log API calls in the database, or send out an email when an error is raised. Possibly you need to
perform some additional validation on the data before it is saved to the database.

**flask-schema** provides a way to do this by defining callbacks on your `SQLAlchemy`_ models or `Flask`_ configuration.

Callback Lifecycle
---------------------

Callbacks can fire at 3 different points in the API request lifecycle.

1. **Setup Callback** - This is called before any database operation is executed. This could be used to perform any
   additional validation or logging before the database operation is executed.

2. **Return Callback** - This is called before the completed API response is returned. Here you could intercept the
   response and perform any additional logic before the response is returned to the client.

3. **Error Callback** - This is called when an exception is raised. This could be used to log the error, send an email
   or perform any additional logic when an exception is raised.

Configuring Callbacks
---------------------------

**flask-schema** uses the `Flask`_ configuration to define global configuration values and these same configuration
values can be applied to specific `HTTP method`_'s or `SQLAlchemy`_ models.

.. note:: For comprehensive details on configuration, and where they can be applied visit our :doc:`configuration </configuration>` page.

Configuration Keys
^^^^^^^^^^^^^^^^^^^^^




`SETUP_CALLBACK <configuration.html#SETUP_CALLBACK>`_
    Called before the database operation is executed.

    Can be set in the `Flask`_ configuration or in `SQLAlchemy`_ models.

`RETURN_CALLBACK <configuration.html#RETURN_CALLBACK>`_
    Called before the completed API response is returned.

    Can be set in the `Flask`_ configuration or in `SQLAlchemy`_ models.

`ERROR_CALLBACK <configuration.html#ERROR_CALLBACK>`_
    Called when an exception is raised.

    Can only be set in the `Flask`_ configuration, not in models.

Configuration Placement
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. dropdown:: Flask Global Configuration


    These configuration values can be set in your `Flask`_ configuration and will apply to all endpoints unless a more
    specific value is set.

        Using the structure of ``API_{configuration_key}``

        i.e  API_SETUP_CALLBACK = my_setup_callback

    - `API_SETUP_CALLBACK <configuration.html#SETUP_CALLBACK>`_ - ``callable`` object to be executed before any database operation is executed.
    - `API_RETURN_CALLBACK <configuration.html#RETURN_CALLBACK>`_ - ``callable`` object to be executed before the completed API response is returned.
    - `API_ERROR_CALLBACK <configuration.html#ERROR_CALLBACK>`_ - ``callable`` object to be executed when an exception is raised.

.. dropdown:: Flask Method Based Configuration


    These methods will override any global configuration values for the specific `HTTP method`_ and are set in your `Flask`_
    configuration.

        Using the structure of ``API_{method}_{configuration_key}``

        i.e  API_GET_SETUP_CALLBACK = my_get_setup_callback

    - `API_GET_SETUP_CALLBACK <configuration.html#SETUP_CALLBACK>`_ - ``callable`` object to be executed before any `GET` database operation is executed.
    - `API_POST_RETURN_CALLBACK <configuration.html#RETURN_CALLBACK>`_ - ``callable`` object to be executed before a completed `POST` API response is returned.
    - `API_DELETE_ERROR_CALLBACK <configuration.html#ERROR_CALLBACK>`_ - ``callable`` object to be executed when a `DELETE` API call has an exception raised.

.. dropdown:: SQLAlchemy Model Configuration


    These override any of the previous configuration values, only overridden by method based model configuration. These
    functions will apply to ANY endpoint for the model.

        Using the structure of ``{configuration_key}`` in lower case.

        Applied to the ``Meta`` class of the model.

    i.e

    .. code:: python

        class MyModel(db.Model):
            class Meta:
                setup_callback = my_setup_callback

    Example Configuration Values:

    - `setup_callback <configuration.html#SETUP_CALLBACK>`_ - ``callable`` object to be executed before database operation is executed on the model.
    - `return_callback <configuration.html#RETURN_CALLBACK>`_ - ``callable`` object to be executed before a completed request for this model is returned by the API.
    - `error_callback <configuration.html#ERROR_CALLBACK>`_ - ``callable`` object to be executed when a API call has an exception raised for this models endpoint.


.. dropdown:: SQLAlchemy Model Method Based Configuration

    These take the highest priority and will override all other configuration values, and are set directly in the models

        Using the structure of ``{method}_{configuration_key}`` in lower case.

        Applied to the ``Meta`` class of the model.

    i.e

    .. code:: python

        class MyModel(db.Model):
            class Meta:
                get_setup_callback = my_get_setup_callback
                post_error_callback = my_post_error_callback

    Example Configuration Values:

    - `get_setup_callback <configuration.html#SETUP_CALLBACK>`_ - ``callable`` object to be executed before any `GET` database operation is executed on the model.
    - `post_return_callback <configuration.html#RETURN_CALLBACK>`_ - ``callable`` object to be executed before a completed `POST` request for this model is returned by the API.
    - `delete_error_callback <configuration.html#ERROR_CALLBACK>`_ - ``callable`` object to be executed when a `DELETE` API call has an exception raised for this model's endpoint.


Callback Examples
--------------------------

To demonstrate how to use callbacks, please see the demo folder of our `repo`_ or view the demo code `here <https://github.com/arched-dev/flask-scheema/tree/master/demo/callbacks>`_.



Callback Signatures
--------------------------

It's probably best for your callback functions to accept `**kwargs` as the only argument. This will allow you to access
any data you need from the request, response or error.

A selection of data is passed to the callback functions (where possible), and this can differ depending on the
`HTTP method`_ or lifecycle position. *It's also possible the structure of this data could change in later versions.*


Setup callback signature
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The setup callback function's kwargs will accept data that could be needed to process the request.

.. code:: python

    {'model': "<class 'demo.model_extension.model.models.Author'>", 'id': 1, 'field': None, 'join_model': None, 'many': False, 'url': '/authors', 'name': 'author', 'output_schema': "<class 'abc.AuthorSchema'>", 'session': "<sqlalchemy.orm.scoping.scoped_session object at 0x7fbde078ae10>", 'input_schema': None, 'group_tag': 'People/Companies'}

The setup function should return the `kwargs` object with any changes made to the data.

.. code:: python

    def my_setup_callback(**kwargs):
        # Do some logic here
        return kwargs


Return callback signature
^^^^^^^^^^^^^^^^^^^^^^^^^^^^


The return callback function's kwargs will house the data that will be returned to the client. This may be the `SQLAlchemy`_
query object or a dictionary of data depending on the query made.

.. code:: python

    {'model': "<class 'demo.model_extension.model.models.Book'>", 'output': {'query': "<Book 137>"}, 'id': None, 'field': None, 'join_model': None, 'deserialized_data': {'title': 'The Crimson Beacon', 'isbn': '9782227215', 'publication_date': "datetime.date(2024, 4, 19)", 'author_id': 1, 'publisher_id': 12}}

The return function should return the `kwargs` object with any changes made to the data.

.. code:: python

    def my_return_callback(**kwargs):
        # Do some logic here
        return kwargs



Post dump callback signature
^^^^^^^^^^^^^^^^^^^^^^^^^^^^


The post dump callback function accepts two arguments, the data (the serialized model in ``dict`` form) and ``**kwargs``
passed to the schemas dump method.

You must return the data after any changes have been made or the api will return ``None``.


.. code:: python

    def my_dump_function_callback(data, **kwargs):
        if data.get("name") == "John":
            data["name"] = "Johnathon"
        return data


.. code:: python

    def my_dump_function_callback(data, **kwargs):
        if not validate.email(data.get("email")):
            raise CustomHTTPException(400, "Invalid email")
        return data



Error callback signature
^^^^^^^^^^^^^^^^^^^^^^^^^^^^


The error callback function accepts the exception and traceback as arguments. There is no need to return anything.

.. code:: python

    def error_callback(e, traceback):
        # Do some logic here



Custom Exceptions
---------------------------

Raising a custom exception in your callback will cause the API to return a custom error response. This can be useful
for following the same error response structure as the rest of your API.

This is simple and can be achieved with the custom exception class provided by **flask-schema**.

.. code:: python

    from flask_schema import CustomHTTPException

    def my_error_callback(**kwargs):
        raise CustomHTTPException(400, "My custom error message")

    class MyModel(db.Model):
        class Meta:
            error_callback = my_error_callback


Extending Query Params
---------------------------

If you are hoping to extend a endpoints by adding additional ``query params`` to your endpoints defining the function is
beyond the scope of ``flask-scheema``.

.. note::
    If you are looking to add aditional filters...

    The `return callback <configuration.html#RETURN_CALLBACK>`_ is the best place to handle this, as it will have
    access to the `SQLAlchemy`_ ``Query`` object when in the kwargs passed to the function.

    From here you can quite easily add additional filters.

    .. code:: python

        def my_return_callback(**kwargs):
            query = kwargs.get("output")
            query = query.filter_by(my_field=kwargs.get("my_query_param"))
            kwargs["output"] = query
            return kwargs

However, you'll like want to document any changes to the available query params in `Redoc`_. This can be achieved with the
`ADDITIONAL_QUERY_PARAMS <configuration.html#ADDITIONAL_QUERY_PARAMS>`_ configuration key.

This key can be set in the `Flask`_ configuration or in `SQLAlchemy`_ models (globally or by `Http method`_).
This means you can apply new query params to specific models, or across the API as a whole.

The expected value is a ``list[dict]`` of the query params you want to add to the endpoint. Please use the below code
examples as a guide for the expected structure.

Consider the below example where we add a new query param to the `Flask`_ configuration (which is applied globally) to
every model and endpoint in the documentation.

.. code:: python

    class Config:

        API_ADDITIONAL_QUERY_PARAMS = [{
            "name": "log",
            "in": "query",
            "description": "Log call into the database", # optional
            "required": False, # optional
            "deprecated": False, # optional
            "schema": {
                "type": "string", # see below for options available
                "format": "password", # see below for options available ... optional
                "example": 1  # optional
            }
        }]


Or set to a specific `HTTP method`_ - ``GET`` on the model level.

.. code:: python

    class Author(db.Model):
        class Meta:
            get_additional_query_params = [{
                    "name": "log",
                    "in": "query",
                    "description": "Log call into the database", # optional
                    "required": False, # optional
                    "deprecated": False, # optional
                    "schema": {
                        "type": "string", # see below for options available
                        "format": "password", # see below for options available ... optional
                        "example": 1  # optional
                    }
                }]


Acceptable Types
^^^^^^^^^^^^^^^^^^

Below is a list of acceptable types for the `schema` key in the `ADDITIONAL_QUERY_PARAMS <configuration.html#ADDITIONAL_QUERY_PARAMS>`_ configuration key.


    ``string``: For string values.

    ``number``: For floating-point numbers.

    ``integer``: For whole numbers.

    ``boolean``: For true or false values.

    ``array``: For arrays or lists of values.

    ``object``: For JSON objects.

Acceptable Formats
^^^^^^^^^^^^^^^^^^^

Below is a list of acceptable formats for the `schema` key in the `ADDITIONAL_QUERY_PARAMS <configuration.html#ADDITIONAL_QUERY_PARAMS>`_ configuration key.

string formats
    ``date``: Full-date according to RFC3339 (e.g., 2020-01-01).

    ``date-time``: The date-time notation as defined by RFC 3339, section 5.6 (e.g., 2020-01-01T12:00:00Z).

    ``password``: A hint to UIs to mask the input.

    ``byte``: Base64-encoded characters, for binary data carried in JSON strings.

    ``binary``: Binary data not encoded in a string, used for file uploads.

    ``email``: String must be in email format.

    ``uuid``: String must be a UUID.

    ``uri``: String must be a URI.

    ``hostname``: String must be a hostname.

    ``ipv4``: String must be an IPv4.

    ``ipv6``: String must be an IPv6.


integer formats
    ``int32``: Signed 32-bit integers.

    ``int64``: Signed 64-bit integers (long).

number formats
    ``float``: Floating-point numbers.

    ``double``: Double-precision floating-point numbers.
