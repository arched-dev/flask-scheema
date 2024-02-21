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
add_relationship_route=True

    __tablename__ = "user"

# We do not accept input schemas on GET or DELETE requests. They are handled with query parameters,

# and not request bodies.

Actual KEys
    - CREATE_API_DOCS = True
    - API_DESCRIPTION
    {x} - API_TITLE
    {x} - API_VERSION
    - API_KEYWORDS
    - API_DESCRIPTION
    - API_LOGO_URL
    - API_LOGO_BACKGROUND
    - API_BASE_MODEL        db.Model
    - API_BASE_SCHEMA=     AutoSchema
    - AUTO_NAME_ENDPOINTS   # check what this does 
    - FULL_AUTO:                                Optional[callable] = True  # does the lot.
    - AUTO_NAME_ENDPOINTS:                       Optional[callable] = True
    {x} - API_CONVERT_TO_CAMEL_CASE:                 Optional[callable] = True  # Convert json output to camel case

    authenticate_route: Optional[bool, Callable] 
    base_model
    base_schema
    db_service   
        
    - API_IGNORE_UNDERSCORE_ATTRIBUTE:          Optional[boolean] = True #Ignore model fields that start with underscore
    
    - API_SERIALIZATION_TYPE                    Optional[str] = "json"  | "url" | "hybrid" | None   # json -> serialise all, url -> to_only url, hybrid -> serialise single items, url lists. None -> No serialisation of nested items 
    - API_SERIALIZATION_DEPTH                   Optional[int] = 1



[//]: # (    - AUTO_NAME_ENDPOINTS:                      Optional[bool, Callable] = True)
    - API_DOCUMENTATION_URL:                    Optional[callable] ="/docs"         Docuentation URL 
    - API_DOCUMENTATION_URL_PREFIX:             Optional[callable] = "/"      Flask route url prefex field
    - API_PREFIX:                               Optional[callable] = "/api"
    - API_VERBOSITY_LEVEL:                      Optional[int] = 0  # no 
    - API_USER_MODEL:                           Optional[callable] = User
Dual: 
    ENDPOINT_NAMER:                            Optional[callable] = endpoint_namer
    API_AUTHENTICATE:                          Optional[callable, bool] = False.   # must have a secret key in flask config 
    ALLOWED_SERIALIZATION_DEPTH                Optional[int] = 1
    {x} - API_ALLOW_SELECT_FIELDS:                               Optional[callable] = True # Allow aggregation
    - API_ALLOW_ORDERBY:                              Optional[callable] = True # Allow aggregation
    - API_ALLOW_JOIN:                                 Optional[callable] = True # Allow aggregation
    - API_ALLOW_GROUPBY:                              Optional[callable] = True # Allow aggregation
    - API_ALLOW_AGGREGATION:                          Optional[callable] = TRUE #Allow aggregation
- 
API OUTPUT: 

    {x} -  API_DUMP_DATETIME
    {x} -  API_DUMP_VERSION
    {x} -  API_DUMP_STATUS_CODE
    {x} -  API_DUMP_RESPONSE_TIME
    {x} -  API_DUMP_COUNT
    {x} -  API_DUMP_NULL_NEXT_URL
    {x} -  API_DUMP_NULL_PREVIOUS_URL
    {x} -  API_DUMP_NULL_ERROR

{x} 
Model meta: 
    block_methods: Optional[List[str]] = None   i.e ["POST"]


Needs implementing
    - MAKE_RELATIONS = True # adds extra routes for each relation, needs backref on parent models
    - API_PRE_GET                               optional[callable] = None  # per app, model or method   
    - API_POST_GET                              optional[callable] = None  # per app, model or method 
    - API_PRE_POST                              optional[callable] = None  # per app, model or method 
    - API_POST_POST                             optional[callable] = None  # per app, model or method 
    - API_PRE_DELETE                            optional[callable] = None  # per app, model or method 
    - API_POST_DELETE                           optional[callable] = None  # per app, model or method 
    - API_PRE_PUT                               optional[callable] = None  # per app, model or method 
    - API_POST_PUT                              optional[callable] = None  # per app, model or method 


current_user    IMPLEMENTED 


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
