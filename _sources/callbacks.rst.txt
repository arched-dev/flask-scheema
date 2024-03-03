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

SETUP_CALLBACK
    Called before the database operation is executed.

RETURN_CALLBACK
    Called before the completed API response is returned.

ERROR_CALLBACK
    Called when an exception is raised.

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
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To demonstrate how to use callbacks, please see the demo folder of our `repo`_ or view the demo code `here <>`_.
