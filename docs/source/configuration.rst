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

    1. :bdg-dark-line:`Model Method` - :doc:`View here<config_locations/model_method>`
    2. :bdg-dark-line:`Model` - :doc:`View here<config_locations/model>`
    3. :bdg-dark-line:`Global Method` - :doc:`View here<config_locations/global_method>`
    4. :bdg-dark-line:`Global` - :doc:`View here<config_locations/global_>`



Config Value Structure
--------------------------------

Every configuration value has a specific structure that defines where it can be used and how it should be written.
These are defined by the the below badges which are listed in the configuration value tables next to each value.

Please take note of the badge for each configuration value, as this will define where the value can be used and how it
should be written.

.. tab-set::

    .. tab-item:: Global

        Global configuration values are the lowest priority and apply to all requests unless overridden by a more specific
        configuration.

        They are applied in the `Flask`_. config class and are prefixed with ``API_``.

        Example `Flask`_ config value:

        .. code:: python

            class Config():

                API_TITLE="My API"

        See the :doc:`Global <config_locations/global_>` page for more information.

    .. tab-item:: Global Method

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
                    # config value is shown as API_BLOCKED_METHODS in flask config
                    blocked_methods = ["DELETE", "POST"]3

        See the :doc:`Model<config_locations/model>` page for more information.


    .. tab-item:: Model Method

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
        - .. data:: DOCUMENTATION_URL

          :bdg:`default:` ``/docs``

          :bdg:`type` ``str``

          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - The url for accessing the redoc documentation.
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


        - Paired with ``API_LOGO_URL``, this value sets the background color of the logo in the ReDoc documentation.
          This value should be a valid CSS color value.

    *
        - .. data:: API_DESCRIPTION

          :bdg:`default:` ``{library_dir}/flask_scheema/html/base_readme.MD``

          :bdg:`type` ``str``

          :bdg-secondary:`Optional` :bdg-dark-line:`Global`


        - Paired with ``API_LOGO_URL``, this value sets the background color of the logo in the ReDoc documentation.
          This value should be a valid CSS color value.



API Configuration Values
------------------------------------------


.. list-table::

    *
        - .. data:: DUMP_DATETIME

          :bdg:`default:` ``None``

          :bdg:`type` ``str``

          :bdg-secondary:`Optional` :bdg-dark-line:`Model`

        - to add to add to add to add to add to add to add to add to add to add to add to add to add to add to add to
          add to add to add to add to add to add to add to add to add to add to add to add to add to add to add to add
          to add to add to add to add
    *
        - .. data:: DUMP_VERSION

          :bdg:`default:` ``None``

          :bdg:`type` ``List[str]``

          :bdg-secondary:`Optional` :bdg-dark-line:`Model`

        - to add to add to add to add to add to add to add to add to add to add to add to add to add to add to add to
          add to add to add to add to add to add to add to add to add to add to add to add to add to add to add to add
          to add to add to add to add
    *
        - .. data:: DUMP_STATUS_CODE

          :bdg:`default:` ``None``

          :bdg:`type` ``str``

          :bdg-secondary:`Optional` :bdg-dark-line:`Model Method`

        - to add to add to add to add to add to add to add to add to add to add to add to add to add to add to add to
          add to add to add to add to add to add to add to add to add to add to add to add to add to add to add to add
          to add to add to add to add
    *
        - .. data:: DUMP_RESPONSE_TIME

          :bdg:`default:` ``None``

          :bdg:`type` ``List[str]``

          :bdg-secondary:`Optional` :bdg-dark-line:`Model Method`

        - to add to add to add to add to add to add to add to add to add to add to add to add to add to add to add to
          add to add to add to add to add to add to add to add to add to add to add to add to add to add to add to add
          to add to add to add to add

    *
        - .. data:: DUMP_COUNT

          :bdg:`default:` ``None``

          :bdg:`type` ``List[str]``

          :bdg-secondary:`Optional` :bdg-dark-line:`Model Method`

        - to add to add to add to add to add to add to add to add to add to add to add to add to add to add to add to
          add to add to add to add to add to add to add to add to add to add to add to add to add to add to add to add
          to add to add to add to add

    *
        - .. data:: DUMP_NULL_NEXT_URL

          :bdg:`default:` ``None``

          :bdg:`type` ``List[str]``

          :bdg-secondary:`Optional` :bdg-dark-line:`Model Method`

        - to add to add to add to add to add to add to add to add to add to add to add to add to add to add to add to
          add to add to add to add to add to add to add to add to add to add to add to add to add to add to add to add
          to add to add to add to add

    *
        - .. data:: DUMP_NULL_PREVIOUS_URL

          :bdg:`default:` ``None``

          :bdg:`type` ``List[str]``

          :bdg-secondary:`Optional` :bdg-dark-line:`Model Method`

        - to add to add to add to add to add to add to add to add to add to add to add to add to add to add to add to
          add to add to add to add to add to add to add to add to add to add to add to add to add to add to add to add
          to add to add to add to add
    *
        - .. data:: DUMP_NULL_ERROR

          :bdg:`default:` ``None``

          :bdg:`type` ``List[str]``

          :bdg-secondary:`Optional` :bdg-dark-line:`Model Method`

        - to add to add to add to add to add to add to add to add to add to add to add to add to add to add to add to
          add to add to add to add to add to add to add to add to add to add to add to add to add to add to add to add
          to add to add to add to add
