Configuration
==============================

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: Config Locations:

   config_locations/global_
   config_locations/global_method
   config_locations/model
   config_locations/model_method


Intro
--------------------------------


In `Flask-Scheema`, configuration options play a crucial role in customizing the behavior of API and its accompanying
documentation. These configurations can be specified through `Flask`_ config values or directly within `SQLAlchemy`_ model
classes using `Meta` classes.

`Flask`_ config values are the most straightforward way to configure the API. Offering a standardized approach to modifying
the extension's behavior at a global or model level.


Config Hierarchy
--------------------------------

To offer flexibility and control, ``Flask-Scheema`` adheres to a hierarchy of configuration priorities.

- Lowest Priority - At the base of this hierarchy are the global `Flask`_ config options, applied globally to all requests. These values will
  be overridden by more specific configurations.

- Method based configurations can be applied to the global `Flask`_ config, allowing for more precise control over the
  behavior of the API in response to specific `HTTP method`_.

- Model based configurations can be embedded within `SQLAlchemy`_ model classes through `Meta` class attributes, allowing
  for more fine-grained control over the behavior of the API in response to specific models.

- Highest Priority - Finally the highest precedence is given to model-specific configurations suffixed with a `HTTP method`_, allowing for
  the most detailed customization of the API's behavior per model and `HTTP method`_.


.. note::

    When applying config values

    - Global `Flask`_ config values are prefixed with ``API_``.
    - Global `Flask`_ method based config values are prefixed with ``API_{method}_``.
    - `SQLAlchemy`_ Model config values omit the ``API_`` prefix and are lower case.
    - `SQLAlchemy`_ Model method based config values omit the ``API_`` prefix, are lower case and are prefixed with the method.

.. note::

    Each configuration value below is assigned a tag, which will define where the value can be used and which priority
    it takes.

    Pri 1. :bdg-dark-line:`Model Method` - :doc:`View here<config_locations/model_method>`

    Pri 2. :bdg-dark-line:`Model` - :doc:`View here<config_locations/model>`

    Pri 3. :bdg-dark-line:`Global Method` - :doc:`View here<config_locations/global_method>`

    Pri 4. :bdg-dark-line:`Global` - :doc:`View here<config_locations/global_>`



Config Value Structure
--------------------------------

Every configuration value has a specific structure that defines where it can be used and how it should be written.
These are defined by the the below badges which are listed in the configuration value tables next to each value.

Please take note of the badge for each configuration value, as this will define where the value can be used and how it
should be written.

.. tab-set::

    .. tab-item:: Global

        :bdg-dark-line:`Global`

        Global configuration values are the lowest priority and apply to all requests unless overridden by a more specific
        configuration.

        They are applied in the `Flask`_. config class and are prefixed with ``API_``.

        Example `Flask`_ config value:

        .. code:: python

            class Config():

                API_TITLE="My API"

        See the :doc:`Global <config_locations/global_>` page for more information.

    .. tab-item:: Global Method

        :bdg-dark-line:`Global Method`

        Global configuration values can apply globally to specific `HTTP method`_, ``GET``, ``POST``, ``PUT``, ``DELETE``,
        ``PATCH``.

        The method should be added after the ``API_`` prefix.

        Example `Flask`_ config value:

        .. code:: python

            class Config():

                API_GET_RATE_LIMIT="100 per minute"
                API_POST_RATE_LIMIT="10 per minute"
                API_PATCH_RATE_LIMIT="10 per minute"

        See the :doc:`Global Method<config_locations/global_method>` page for more information.

    .. tab-item:: Model

        :bdg-dark-line:`Model`

        Model configuration values override any `Flask`_ configuration.

        They are applied in the `SQLAlchemy`_ models Meta class, they should omit the prefix ``API_`` and be written in lower
        case.

        Example model.Meta config value:

        .. code:: python

            class MyModel(db.model):
                __table__ = "my_model"

                class Meta:
                    # config value is shown as API_RATE_LIMIT in flask config
                    rate_limit = "10 per second"
                    # config value is shown as API_BLOCK_METHODS in flask config
                    blocked_methods = ["DELETE", "POST"]

        See the :doc:`Model<config_locations/model>` page for more information.


    .. tab-item:: Model Method


        :bdg-dark-line:`Model Method`

        Model method configuration values have the highest priority and will override any other configuration.

        They are applied in the `SQLAlchemy`_ models Meta class, they should omit the prefix ``API_``, be written in lower
        case and be prefixed with the method.

        Example model.Meta config value:

        .. code:: python

            class MyModel(db.model):
                __table__ = "my_model"

                class Meta:
                    # config value is shown as API_RATE_LIMIT in flask config
                    get_rate_limit = "10 per minute"
                    post_rate_limit = "5 per minute"

        See the :doc:`Model Method<config_locations/model_method>` page for more information.


Documentation Configuration Values
------------------------------------------


.. list-table::

    *
        - .. data:: CREATE_DOCS

          :bdg:`default:` ``True``

          :bdg:`type` ``bool``

          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Controls whether the `Redoc`_ documentation is created and served by the API. When disabled, the API will
          not serve documentation. If true, the API will serve documentation at the url specified by `DOCUMENTATION_URL <configuration.html#DOCUMENTATION_URL>`_.
    *
        - .. data:: DOCUMENTATION_URL

          :bdg:`default:` ``/docs``

          :bdg:`type` ``str``

          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - The url for accessing the `ReDoc`_ documentation.
    *
        - .. data:: TITLE

          :bdg:`default:` ``None``

          :bdg:`type` ``str``

          :bdg-danger:`Required` :bdg-dark-line:`Global`

        - Sets the title of your API in the generated ReDoc documentation. It appears prominently in the
          documentation, serving as a headline for users exploring your API.
    *
        - .. data:: VERSION

          :bdg:`default:` ``None``

          :bdg:`type` ``str``

          :bdg-danger:`Required` :bdg-dark-line:`Global`

        - Sets the version number of your API. This value will appear in the generated ReDoc documentation and in api
          responses when `API_DUMP_VERSION` is enabled.

          Example:
            ``0.1.0``
    *
        - .. data:: LOGO_URL

          :bdg:`default:` ``None``

          :bdg:`type` ``str``

          :bdg-secondary:`Optional` :bdg-dark-line:`Global`


        - When defined, a logo will be displayed in the ReDoc documentation. This should be be valid image URL
    *
        - .. data:: LOGO_BACKGROUND

          :bdg:`default:` ``None``

          :bdg:`type` ``str``

          :bdg-secondary:`Optional` :bdg-dark-line:`Global`


        - Paired with `API_LOGO_URL <configuration.html#API_LOGO_URL>`_, this value sets the background color of the logo in the ReDoc documentation.
          This value should be a valid CSS color value.

    *
        - .. data:: DESCRIPTION

          :bdg:`default:` ``./flask_scheema/html/base_readme.MD``

          :bdg:`type` ``str``

          :bdg-secondary:`Optional` :bdg-dark-line:`Global`


        - The main description of the API in the generated ReDoc documentation. This value should be a valid markdown
          string or a path to a markdown file. The file will be rendered with `Jinja`_ and you can access the `Flask`_
          config with the ``{{ config }}`` variable.

          -----------------------------------------------------------------

          View the template file `here <https://github.com/arched-dev/flask-scheema/blob/master/flask_scheema/html/base_readme.MD>`_
    *
        - .. data:: DOCS_FONT

          :bdg:`default:` ``jetbrains_mono``

          :bdg:`type` ``str``

          :bdg-secondary:`Optional` :bdg-dark-line:`Global`


        - Configures the font style for your ReDoc documentation, with ``jetbrains_mono`` as the default. Options
          include ``jetbrains_mono``, ``sourcecode_pro``, ``roboto``, ``montserrat``, ``lato`` or any valid css font.

          This setting allows for visual customization to match your documentation's aesthetic preferences.
    *
        - .. data:: CONTACT_NAME

          :bdg:`default:` ``None``

          :bdg:`type` ``str``

          :bdg-secondary:`Optional` :bdg-dark-line:`Global`


        - Specifies the contact name for inquiries and support in the `ReDoc`_ documentation. If not provided, the field name will not be displayed in the docs.
    *
        - .. data:: CONTACT_EMAIL

          :bdg:`default:` ``None``

          :bdg:`type` ``str``

          :bdg-secondary:`Optional` :bdg-dark-line:`Global`


        - Specifies the contact email for inquiries and support in the `ReDoc`_ documentation. If not provided, the field name will not be displayed in the docs.
    *
        - .. data:: CONTACT_URL

          :bdg:`default:` ``None``

          :bdg:`type` ``str``

          :bdg-secondary:`Optional` :bdg-dark-line:`Global`


        - Specifies the contact web address for inquiries and support in the `ReDoc`_ documentation. If not provided, the field name will not be displayed in the docs.
    *
        - .. data:: LICENCE_NAME

          :bdg:`default:` ``None``

          :bdg:`type` ``str``

          :bdg-secondary:`Optional` :bdg-dark-line:`Global`


        - Specifies the licence type for the API in the `ReDoc`_ documentation. If not provided, the field name will not be displayed in the docs.
    *
        - .. data:: LICENCE_URL

          :bdg:`default:` ``None``

          :bdg:`type` ``str``

          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Specifies a url to the licence type for the API in the `ReDoc`_ documentation. If not provided, the field name will not be displayed in the docs.
    *
        - .. data:: SERVER_URLS

          :bdg:`default:` ``None``

          :bdg:`type` ``list[dict]``

          :bdg-secondary:`Optional` :bdg-dark-line:`Global`


        - Specifies the server(s) used for calling the API in the `ReDoc`_ documentation. If not provided, the field name will not be displayed in the docs.

          Example structure:

            [{"url": "https://api.example.com", "description": "Main server"}, ...]




API Configuration Values
------------------------------------------


.. list-table::

    *
        - .. data:: DUMP_DATETIME

          :bdg:`default:` ``True``

          :bdg:`type` ``bool``

          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - When enabled, the API will include a ``datetime`` field in the response data. This field will contain the
          current date and time of the response.
    *
        - .. data:: DUMP_VERSION

          :bdg:`default:` ``True``

          :bdg:`type` ``bool``

          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - When enabled, the API will include a ``version`` field in the response data. This field will contain the
          version number of the API.
    *
        - .. data:: DUMP_STATUS_CODE

          :bdg:`default:` ``True``

          :bdg:`type` ``bool``

          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - When enabled, the API will include a ``statusCode`` field in the response data. This field will contain the
          status code of the response.

          The output key will either be camelCase or snake_case depending on the value of `CONVERT_TO_CAMEL_CASE <configuration.html#CONVERT_TO_CAMEL_CASE>`_.
    *
        - .. data:: DUMP_RESPONSE_TIME

          :bdg:`default:` ``True``

          :bdg:`type` ``bool```

          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - When enabled, the API will include a ``responseTime`` field in the response data. This field will contain the
          time taken to process the request in ms.

          The output key will either be camelCase or snake_case depending on the value of `CONVERT_TO_CAMEL_CASE <configuration.html#CONVERT_TO_CAMEL_CASE>`_.



    *
        - .. data:: DUMP_COUNT

          :bdg:`default:` ``True``

          :bdg:`type` ``bool``

          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - When enabled, the API will include a ``totalCount`` field in the response data. This field will contain the
          total number of records available to be queried with pagination (not the number of records returned in the
          response).

          The output key will either be camelCase or snake_case depending on the value of `CONVERT_TO_CAMEL_CASE <configuration.html#CONVERT_TO_CAMEL_CASE>`_.

    *
        - .. data:: DUMP_NULL_NEXT_URL

          :bdg:`default:` ``True``

          :bdg:`type` ``bool``

          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - When enabled, the API will include a ``nextUrl`` field in the response data if null. When disabled the
          ``nextUrl`` field will not be included in the response data if null.

          The output key will either be camelCase or snake_case depending on the value of `CONVERT_TO_CAMEL_CASE <configuration.html#CONVERT_TO_CAMEL_CASE>`_.


    *
        - .. data:: DUMP_NULL_PREVIOUS_URL

          :bdg:`default:` ``True``

          :bdg:`type` ``bool``

          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - When enabled, the API will include a ``previousUrl`` field in the response data if null. When disabled the
          ``previousUrl`` field will not be included in the response data if null.

          The output key will either be camelCase or snake_case depending on the value of `CONVERT_TO_CAMEL_CASE <configuration.html#CONVERT_TO_CAMEL_CASE>`_.
    *
        - .. data:: DUMP_NULL_ERRORS

          :bdg:`default:` ``False``

          :bdg:`type` ``bool``

          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - When enabled, the API will include a ``error`` field in the response data if null. When disabled the
          ``error`` field will not be included in the response data if null.

    *
        - .. data:: PRINT_EXCEPTIONS

          :bdg:`default:` ``True``

          :bdg:`type` ``bool``

          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - When enabled, the API will print exceptions to the console when they occur. This is useful for debugging
          purposes.

    *
        - .. data:: CONVERT_TO_CAMEL_CASE

          :bdg:`default:` ``True``

          :bdg:`type` ``bool``

          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - When enabled, the API will print exceptions to the console when they occur. This is useful for debugging
          purposes.


    *
        - .. data:: BASE_MODEL

          :bdg:`default:` ``None``

          :bdg:`type` ``DeclarativeBase``

          :bdg-danger:`Required` :bdg-dark-line:`Global`

        - The base class for all models in the API, and a required configuration value. Used by **flask-scheema** to
          correctly analyse models and automatically create endpoints.

            This value should be a valid base model (`see here <https://docs.sqlalchemy.org/en/20/orm/quickstart.html#declare-models>`_).

          When using `Flask-SQLAlchemy`_ you must subclass your models with ``db.Model`` as normal, and also
          populate this field with ``db.Model``. You will, however, have to pass your actual base model to the
          ``SQLAlchemy.init_app(base_clas=YourBase)``

            View the :doc:`Quickstart <quickstart>` docs for more information on how to use this value.

    *
        - .. data:: ALLOW_CASCADE_DELETE

          :bdg:`default:` ``True``

          :bdg:`type` ``bool``

          :bdg-secondary:`Optional` :bdg-dark-line:`Model Method`

        - When enabled, the API will allow cascade delete operations on models when the query parameter

          ``?cascade_delete=1``

          is added to the request. If this parameter is not added, the API will return a 400 response

          (when the model has dependent relationships).

          When disabled, the API will not allow cascade delete operations on models and will return a 400 response

          (when the model has dependent relationships).

    *
        - .. data:: SETUP_CALLBACK

          :bdg:`default:` ``None``

          :bdg:`type` ``callable``

          :bdg-secondary:`Optional` :bdg-dark-line:`Model Method`

        - When a function is assigned to this value, the API will call the function prior to the model being queried.
          This is useful for adding custom logic to the API, such as adding additional query parameters/modifying the
          query or logging request to the database.

            View an example function & its signature `here <callbacks.html#setup-function-signature>`_.

    *
        - .. data:: RETURN_CALLBACK

          :bdg:`default:` ``None``

          :bdg:`type` ``callable``

          :bdg-secondary:`Optional` :bdg-dark-line:`Model Method`

        - When a function is assigned to this value, the API will call the function post database call and pre returning
          the data to the client. This is useful for adding custom logic to the API, such as modifying the response data
          or logging the response to the database.

            View an example function & its signature `here <callbacks.html#return-function-signature>`_.

    *
        - .. data:: ERROR_CALLBACK

          :bdg:`default:` ``None``

          :bdg:`type` ``callable``

          :bdg-secondary:`Optional` :bdg-dark-line:`Global Method`

        - When a function is assigned to this value, the API will call the function when an error occurs. This is useful
          for adding custom logic to the API, such as logging the error to the database or sending an email to the
          developer.

            View an example function & its signature `here <callbacks.html#error-function-signature>`_.

    *
        - .. data:: ADDITIONAL_QUERY_PARAMS

          :bdg:`default:` ``None``

          :bdg:`type` ``list[dict]``

          :bdg-secondary:`Optional` :bdg-dark-line:`Model Method`

        - If you are hoping to extend the default query parameters of the API using callbacks, you may also want to add
          these to the `ReDoc`_ documentation. This value allows you to add additional query parameters per model or
          globally to the API.

            View an example of its use and expected value here `Example of its use here <configuration.html#extending-query-params>`_.
