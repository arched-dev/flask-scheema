Config Globals
==============================

    **Global** < Global Method < Model < Model Method

:bdg-dark-line:`Global`

These are the global configuration variables which are assigned in `Flask`_.

-  They should always be uppercase
-  They should always start with ``API_``

Values defined here will apply globally unless a more specific value is defined.

Will be overridden by any other config value type;  :bdg-dark-line:`Global Method`, :bdg-dark-line:`Model`, :bdg-dark-line:`Model Method`.

Example
--------------

.. code:: python

    class Config():
        # the rate limit across all endpoints in your API
        # If any other, more specific, rate limit is defined, it will
        # override this one for the particular endpoint / method / model.
        API_RATE_LIMIT = "1 per minute"
