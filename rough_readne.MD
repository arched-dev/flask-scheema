# creates OpenAPI 3.0+ api specification

    - Takes an optional(input) and and output schema, which will be used to load (deserialise) and dump (serialise) data -> models & models -> data.
    - Automatically generates applicable marshmallow schema fields, including

# creates a fully working API from sqlalchemy models.

# schemas

for custom models you must subclass with AutoSchema
for custom input models you must add the dump = False

# models

use:

class User(Base):
class Meta
docs_description="This represents a user"

    __tablename__ = "user"

# We do not accept input schemas on GET or DELETE requests. They are handled with query parameters,

# and not request bodies.

Documentation

xxx {x} - API_CREATE_DOCS = True
xxx {x} - API_DOCUMENTATION_URL
xxx {x} - API_TITLE is a required string that sets the title of your API in the generated ReDoc documentation. This title
  is a crucial piece of your API's identity, succinctly conveying the essence of your service to consumers. It appears
  prominently in the documentation, serving as a headline for users exploring your API.
xxx  {x} - API_VERSION
xxx - API_LOGO_URL
xxx - API_LOGO_BACKGROUND
- API_KEYWORDS
- 
xxx - API_DESCRIPTION accepts a string or a filepath string, with a default behavior that auto-generates a comprehensive
  documentation description. If a filepath is provided, it can point to a Jinja template that dynamically accesses the
  Flask configuration via {config.xxxx} placeholders. This flexible approach allows for a rich, context-aware
  description in your ReDoc documentation.
- 
xxx - API_DOCS_FONT = configures the font style for your ReDoc documentation, with jetbrains_mono as the default. Options
  include jetbrains_mono, sourcecode_pro, roboto, montserrat, and lato. This setting allows for visual customization to
  match your documentation's aesthetic preferences.
- 
xxx {X} - API_CONTACT_NAME = None (str) Specifies the contact name for inquiries and support in the redoc documentation. If not
  provided, the field name will not be displayed in the docs.
xxx {X} - API_CONTACT_EMAIL = None (str) Specifies the contact email for inquiries and support in the redoc documentation. If
  not provided, the field name will not be displayed in the docs.
xxx {X}- API_CONTACT_URL = None (str) Specifies the contact web address for inquiries and support in the redoc documentation.
  If not provided, the field name will not be displayed in the docs.
xxx {X}- API_LICENCE_NAME = None (str) Specifies the licence type for the API in the redoc documentation. If not provided, the
  field name will not be displayed in the docs.
xxx {X}- API_LICENCE_URL = None (str) Specifies a url to the licence type for the API in the redoc documentation. If not
  provided, the field name will not be displayed in the docs.
xxx {X}- API_SERVER_URLS = List[Dict[str, str]] default None,
  example: [{"url": "http://localhost:5000", "description": "Local server"}...]  Specifies the server(s) used for
  calling the API in the redoc documentation. If not provided, the field name will not be displayed in the docs.


xxx - API_PRINT_EXCEPTIONS = True Defines whether to print exceptions to console when they occur.
    - API_BASE_MODEL db.Model
xxx - API_BASE_SCHEMA = AutoSchema
    - AUTO_NAME_ENDPOINTS # check what this does
    - FULL_AUTO:                                 Optional[callable] = True # does the lot.
    - AUTO_NAME_ENDPOINTS:                       Optional[callable] = True
xxx  {x}   - API_CONVERT_TO_CAMEL_CASE:             Optional[callable] = False # Convert json output to camel case
xxx  {x}   - API_ALLOW_CASCADE_DELETE:                   Optional[callable] = True # When True, will not cascade delete on

    -
    -
        -
            - Optional[callable] = True # Weather to add GET relationship routes to each model i.e /books/1/authors    
              base_model
              base_schema
              db_service


xxx  {x}  - API_IGNORE_UNDERSCORE_ATTRIBUTE:          Optional[boolean] = When enabled model or schema fields that start with an
  underscore will be ignored from all documentation and api outputs.

{x} - API_SERIALIZATION_TYPE Optional[str] = "json"  | "url" | "hybrid" | False # json -> serialise all, url -> to_only
url, hybrid -> serialise single items, url lists. None -> No serialisation of nested items

- API_SERIALIZATION_DEPTH Optional[int] = 1
  {x} - API_PAGINATION_SIZE_DEFAULT Optional[int] = 20 Sets the default number of items returned in a single page of API
  results, with a default value of 20. This configuration optimizes data retrieval by limiting the number of items
  fetched.
  {x} - API_PAGINATION_SIZE_MAX Optional[int] = 100 Sets the maximum allowed number of items returned in a single page
  of API results  (specified with the url param ?limit=100)
-
API_DUMP_HYBRID_PROPERTIES     True

API_ADD_RELATIONS
-
[//]: # (    - AUTO_NAME_ENDPOINTS:                      Optional[bool, Callable] = True)

    - API_DOCUMENTATION_URL:                    Optional[callable] ="/docs"         Docuentation URL 
    - API_DOCUMENTATION_URL_PREFIX:             Optional[callable] = "/"      Flask route url prefex field
    - API_PREFIX:                               Optional[callable] = "/api"
    - API_VERBOSITY_LEVEL:                      Optional[int] = 0  # no 
    - API_USER_MODEL:                           Optional[callable] = User
    - API_RATE_LIMIT_STORAGE_URI                Optional[str] = "memory"  or   "memcached://127.0.0.1:{port}" | "redis://127.0.0.1:{port}" | "mongodb://127.0.0.1:{port}"  # attempts to gather the suitable backend for you.

- API_ENDPOINT_NAMER:                            Optional[callable] = endpoint_namer
- API_ENDPOINT_CASE:                            Optional[callable] = camelCase,PascalCase,snake_case,SCREAMING_SNAKE_CASE, kebab-case,SCREAMING-KEBAB-CASE  |   endpoint_namer


Dual only:

- API_READ_ONLY = False When set to true, the API will not allow POST, PUT, PATCH, DELETE requests.
- API_ALLOW_ORDER_BY:                              Optional[callable] = True # Allow aggregation
- API_ALLOW_JOIN:                                 Optional[callable] = True # Allow aggregation
- API_ALLOW_GROUPBY:                              Optional[callable] = True # Allow aggregation
- API_ALLOW_AGGREGATION:                          Optional[callable] = TRUE #Allow aggregation
- API_ALLOW_SELECT_FIELDS
- API_block_methods:                               Optional[callable] = [] # Allow aggregation

Dual with methods:

API_AUTHENTICATE:                          Optional[callable, bool] = False. # must have a secret key in flask config
API_AUTHENTICATE_METHOD:                   Optional[str] =  "api_key" | "jwt" | "basic"
{x} - API_ALLOW_SELECT_FIELDS:                               Optional[callable] = True # Allow aggregation

xxx {x} - API_SETUP_CALLBACK
xxx {x} - API_RETURN_CALLBACK
xxx {x} - API_ERROR_CALLBACK
xxx {x} - API_ADDITIONAL_QUERY_PARAMS

{x} \- API_RATE_LIMIT:                               Optional[callable] = "1 per second"
- API_RATE_LIMIT_CALLBACK:                      Optional[callable] = None # a function that is called on rate limit
  being breached.
API_RATE_LIMIT_STORAGE_URI need to add

API OUTPUT:


xxx    {x} -  API_DUMP_DATETIME
xxx    {x} -  API_DUMP_VERSION
xxx    {x} -  API_DUMP_STATUS_CODE
xxx    {x} -  API_DUMP_RESPONSE_TIME
xxx    {x} -  API_DUMP_COUNT
xxx    {x} -  API_DUMP_NULL_NEXT_URL
xxx    {x} -  API_DUMP_NULL_PREVIOUS_URL
xxx    {x} -  API_DUMP_NULL_ERROR

IGNORE_FIELDS = ["password", "email"] # fields to ignore in the API output
IGNORE_OUTPUT_FIELDS = ["password", "email"] # fields to ignore in the API output
IGNORE_INPUT_FIELDS = ["password", "email"] # fields to ignore in the API output


{x}
Model meta:

block_methods: Optional[List[str]] = None i.e ["POST"]
get_single_description: Optional[str] = None
get_many_description: Optional[str] = None
post_description: Optional[str] = None
put_description: Optional[str] = None
delete_description: Optional[str] = None

Needs implementing

- MAKE_RELATIONS = True # adds extra routes for each relation, needs backref on parent models


current_user IMPLEMENTED

If you put

flask config:

    - CREATE_MARSHMALLOW_SCHEMA = False
    - CREATE_MARSHMALLOW_FIELDS = True
    - CREATE_BASE_ROUTES = True
    - CREATE_RELATED_ROUTES = True
    - SERIALISE_DEPTH = 1


    - AUTHENTICATION_ON = True
    - WRITE_ROLES = []
    - READ_ROLES = []


    - API_BLUEPRINT_NAME = "api"
    

    - MAKE_RELATIONS = True # adds extra routes for each relation, needs backref on parent models 
    - API_AUTHENTICATE = False
    - API_FILTER = True  # Allow aggregation

    - API_OUTPUT_MS = True   # outputs the MS taken in the API reponse.
    - API_VERBOSITY > print how much?          #NOT IMPLEMENTED YET
    - API_HANDLE_EXCEPTION = True         #NOT IMPLEMENTED YET
    - API_USER_MODEL = User        #NOT IMPLEMENTED YET
    - API_DOCUMENTATION_URL = "/docs"        #NOT IMPLEMENTED YET


    - load_only (default False) - this is needed to avoid the generator picking up an incoming schema as a dump model)
    - API_SERIALIZATION_DEPTH (default 1) - sets the serialisation depth for the schema
    - API_SERIALIZE_ONE_TO_ONE (default True) - defines if the schema should always serialise one-to-one relationships
    - API_SERIALIZE_ONE_TO_MANY (default False) - defines if the schema should always serialise one-to-many relationships
    - API_DUMP_HYBRID_PROPERTIES (default True) - adds hybrid properties to the schema            #NOT IMPLEMENTED YET

    models or config

    - API_ENDPOINT_NAMER = endpoint_namer
    - API_SCHEMA_BASE = AutoSchema
    - API_IGNORE_UNDERSCORE_ATTRIBUTE (default True) - ignore model fields that start with underscore

    models only

    tag_group = "Authentication"
    description = {"GET": "Return a single `user`"}
    block = ["GET", "PUT", "DELETE"]


    _attribute_name are ignored.
