import pytest
from flask import session

from demo.basic_factory.basic_factory import create_app
from demo.model_extension.model import create_app as create_app_models


@pytest.fixture
def app():
    app = create_app(
        {
            "API_TITLE": "Automated test",
            "API_VERSION": "0.2.0",
            # Other configurations specific to this test
        }
    )
    yield app
    del app


@pytest.fixture
def client(app):
    return app.test_client()


# check to make sure that the title and version are changed
def test_basic_change_title_and_version(client):
    response = client.get("/swagger.json")

    assert response.json["info"]["title"] == "Automated test"
    assert response.json["info"]["version"] == "0.2.0"

    response = client.get("/docs")
    html = response.data.decode()
    assert "Automated test" in html
    assert "0.2.0" in html


@pytest.fixture
def app_meth():

    app_new = create_app(
        {
            "API_BLOCK_METHODS": ["POST", "PATCH", "DELETE"],
        }
    )

    yield app_new
    del app_new


@pytest.fixture
def client_meth(app_meth):

    return app_meth.test_client()


# block methods from the API
def test_block_methods(client_meth):

    resp = client_meth.get("/api/authors/1")

    assert len(resp.json["value"]["created"]) > 0

    resp_patch = client_meth.patch("/api/authors", json=resp.json["value"])
    resp_post = client_meth.post("/api/authors", json=resp.json["value"])
    resp_delete = client_meth.delete("/api/authors/10?cascade_delete=1")

    assert resp_patch.status_code == 405
    assert resp_post.status_code == 405
    assert resp_delete.status_code == 405


# check to make sure docs description changes
def test_change_spec_description_and_others():
    app = create_app(
        {
            "API_DESCRIPTION": "This is a test description",
            "API_LOGO_URL": "http://test.com/logo.png",
            "API_LOGO_BACKGROUND": "#010101",
            "API_CUSTOM_HEADERS": "<style>h1{color: red;}</style>",
        }
    )

    client = app.test_client()
    resp = client.get("/swagger.json")

    assert resp.json["info"]["description"] == "This is a test description"
    assert resp.json["info"]["x-logo"]["url"] == "http://test.com/logo.png"
    assert resp.json["info"]["x-logo"]["backgroundColor"] == "#010101"

    resp = client.get("/docs")
    html = resp.data.decode()
    assert "<style>h1{color: red;}</style>" in html


# check to make sure that read only is working
def test_read_only():
    app = create_app(
        {
            "API_READ_ONLY": True,
        }
    )

    client = app.test_client()
    resp = client.get("/api/books/1")

    assert len(resp.json["value"]["created"]) > 0

    resp_patch = client.patch("/api/books", json=resp.json["value"])
    resp_post = client.post("/api/books", json=resp.json["value"])
    resp_delete = client.delete("/api/books/1")

    assert resp_patch.status_code == 405
    assert resp_post.status_code == 405
    assert resp_delete.status_code == 405


# check to make sure that changing the docs url works
def test_docs_path():
    app = create_app(
        {"API_DOCUMENTATION_URL": "/my_docs", "API_TITLE": "Change docs url"}
    )

    client = app.test_client()
    resp = client.get("/my_docs")

    assert resp.status_code == 200
    assert "Change docs url" in resp.text


# check to make sure that contact details are working in the docs
def test_docs_extra_info():
    app = create_app(
        {
            "API_CONTACT_NAME": "Test User",
            "API_CONTACT_EMAIL": "help@test.com",
            "API_CONTACT_URL": "https://test.com/contact",
            "API_LICENCE_NAME": "MIT",
            "API_LICENCE_URL": "https://opensource.org/licenses/MIT",
            "API_SERVER_URLS": [
                {"url": "http://localhost:5000/api", "description": "Local server"},
                {
                    "url": "http://sandbox.localhost:5000/api",
                    "description": "sandbox server",
                },
            ],
        }
    )

    client = app.test_client()
    resp = client.get("/swagger.json")

    assert resp.json["info"]["contact"] == {
        "email": "help@test.com",
        "name": "Test User",
        "url": "https://test.com/contact",
    }
    assert resp.json["info"]["license"] == {
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    }
    assert resp.json["servers"] == [
        {"description": "Local server", "url": "http://localhost:5000/api"},
        {"description": "sandbox server", "url": "http://sandbox.localhost:5000/api"},
    ]


# check to make sure that the base response from the API contains the correct keys
def test_basic_no_change_api_output(client):
    books = client.get("/api/books").json

    assert "datetime" in books.keys()
    assert "api_version" in books.keys()
    assert "status_code" in books.keys()
    assert "total_count" in books.keys()
    assert "next_url" in books.keys()
    assert "previous_url" in books.keys()

    books_error = client.get("/api/books/0009999").json
    assert "errors" in books_error.keys()

    book = client.get("/api/books/1").json

    assert "datetime" in book.keys()
    assert "api_version" in book.keys()
    assert "status_code" in book.keys()
    assert "total_count" in book.keys()


# make sure camel case is and isn't used.
def test_change_to_camel_output():
    app_cam = create_app_models(
        {
            "API_ENDPOINT_CASE": "kebab",
            "API_FIELD_CASE": "snake",
            "API_SCHEMA_CASE": "camel",
        }
    )
    client_camel = app_cam.test_client()
    book = client_camel.get("/api/books/1").json
    assert "publication_date" in book["value"].keys()

    api_calls = client_camel.get("/api/api-calls").json
    assert api_calls["status_code"] == 200

    swagger_oas = client_camel.get("/swagger.json").json
    assert "apiCalls" in swagger_oas["components"]["schemas"].keys()


def test_change_to_pascal_output():
    app_pascal = create_app_models(
        {
            "API_ENDPOINT_CASE": "snake",
            "API_FIELD_CASE": "kebab",
            "API_SCHEMA_CASE": "pascal",
        }
    )
    client_pascal = app_pascal.test_client()

    book = client_pascal.get("/api/books/1").json
    assert "publication-date" in book["value"].keys()

    apiCalls = client_pascal.get("/api/api_calls").json
    assert apiCalls["status-code"] == 200

    swaggerOas = client_pascal.get("/swagger.json").json
    assert "ApiCalls" in swaggerOas["components"]["schemas"].keys()


def test_change_to_snake_output():
    app_snake = create_app_models(
        {
            "API_ENDPOINT_CASE": "camel",
            "API_FIELD_CASE": "pascal",
            "API_SCHEMA_CASE": "snake",
        }
    )
    client_snake = app_snake.test_client()

    book = client_snake.get("/api/books/1").json
    assert "PublicationDate" in book["Value"].keys()

    api_calls = client_snake.get("/api/apiCalls").json
    assert api_calls["StatusCode"] == 200

    swagger_oas = client_snake.get("/swagger.json").json
    assert "api_calls" in swagger_oas["components"]["schemas"].keys()


def test_change_to_screaming_snake_output():
    app_screaming_snake = create_app_models(
        {
            "API_ENDPOINT_CASE": "kebab",
            "API_FIELD_CASE": "camel",
            "API_SCHEMA_CASE": "screaming_snake",
        }
    )
    client_screaming_snake = app_screaming_snake.test_client()

    book = client_screaming_snake.get("/api/books/1").json
    assert "publicationDate" in book["value"].keys()

    api_calls = client_screaming_snake.get("/api/api-calls").json
    assert api_calls["statusCode"] == 200

    swagger_oas = client_screaming_snake.get("/swagger.json").json
    assert "API_CALLS" in swagger_oas["components"]["schemas"].keys()


def test_change_to_kebab_output():
    app_kebab = create_app_models(
        {
            "API_ENDPOINT_CASE": "pascal",
            "API_FIELD_CASE": "snake",
            "API_SCHEMA_CASE": "kebab",
        }
    )
    client_kebab = app_kebab.test_client()

    book = client_kebab.get("/api/Books/1").json
    assert "publication_date" in book["value"].keys()

    api_calls = client_kebab.get("/api/ApiCalls").json
    assert api_calls["status_code"] == 200

    swagger_oas = client_kebab.get("/swagger.json").json
    assert "api-calls" in swagger_oas["components"]["schemas"].keys()


def test_dump_hybrid_off():
    app = create_app(
        {
            "API_DUMP_HYBRID_PROPERTIES": False,
            "API_ADD_RELATIONS": False,
        }
    )

    client = app.test_client()
    resp = client.get("/api/authors/1")

    assert "full_name" not in resp.json["value"].keys()
    assert "books" not in resp.json["value"].keys()


def test_dump_hybrid_on(client):

    resp = client.get("/api/authors/1")

    assert "full_name" in resp.json["value"].keys()


# change the api base url prefix
def test_change_api_route():
    app_prefix = create_app(
        {
            "API_PREFIX": "/my_api",
        }
    )
    client_prefix = app_prefix.test_client()
    fail_book = client_prefix.get("/api/books/1")
    book = client_prefix.get("/my_api/books/1")

    assert fail_book.status_code == 404
    assert book.status_code == 200
    assert "title" in book.json["value"].keys()


# change the api base output
@pytest.fixture
def app_change_out():
    app = create_app(
        {
            "API_DUMP_DATETIME": False,
            "API_DUMP_VERSION": False,
            "API_DUMP_STATUS_CODE": False,
            "API_DUMP_TOTAL_COUNT": False,
            "API_DUMP_RESPONSE_MS": False,
            "API_DUMP_NULL_NEXT_URL": False,
            "API_DUMP_NULL_PREVIOUS_URL": False,
            "API_DUMP_NULL_ERRORS": False,
        }
    )
    yield app


@pytest.fixture
def client_change_out(app_change_out):
    return app_change_out.test_client()


def test_basic_change_api_base_output(client_change_out):
    book = client_change_out.get("/api/books/1").json
    assert book.keys() == {"value"}


# check the different types of serialization   "json" | "url" | "hybrid" | None
def test_serialize_url_only():
    app = create_app({"API_SERIALIZATION_TYPE": "url"})
    client = app.test_client()
    resp = client.get("/api/books/1")

    assert resp.json["value"]["author"] == "/api/books/1/authors"
    assert resp.json["value"]["categories"] == "/api/books/1/categories"
    assert resp.json["value"]["reviews"] == "/api/books/1/reviews"


def test_serialize_hybrid():
    app = create_app({"API_SERIALIZATION_TYPE": "hybrid"})
    client = app.test_client()
    resp = client.get("/api/books/1")

    assert isinstance(resp.json["value"]["author"], dict)
    assert resp.json["value"]["categories"] == "/api/books/1/categories"
    assert resp.json["value"]["reviews"] == "/api/books/1/reviews"


def test_serialize_json():
    app = create_app({"API_SERIALIZATION_TYPE": "json"})
    client = app.test_client()
    resp = client.get("/api/books/1")

    assert isinstance(resp.json["value"]["author"], dict)
    assert isinstance(resp.json["value"]["categories"], list)
    assert isinstance(resp.json["value"]["reviews"], list)


def test_serialize_none():
    app = create_app({"API_SERIALIZATION_TYPE": False})
    client = app.test_client()
    resp = client.get("/api/books/1")

    assert "author" not in resp.json["value"]
    assert "categories" not in resp.json["value"]
    assert "reviews" not in resp.json["value"]


def test_switch_off_url_params():
    app_filters = create_app(
        {
            "API_ALLOW_ORDER_BY": False,
            "API_ALLOW_FILTER": False,
            "API_ALLOW_SELECT_FIELDS": False,
        }
    )
    client_filters = app_filters.test_client()

    resp = client_filters.get("/api/books")
    resp_order = client_filters.get("/api/books?order_by=-id")
    resp_filter = client_filters.get("/api/books?id__in=(20,21,22)")
    resp_select = client_filters.get("/api/books?fields=title")

    assert resp.status_code == 200
    assert 21 not in [x["id"] for x in resp_order.json["value"]]
    assert resp_filter.json["value"][0]["id"] == 1
    assert "created" in resp_select.json["value"][0].keys()


def test_rate_limit():
    app_rl = create_app({"API_RATE_LIMIT": "1 per 2 seconds"})
    client_rl = app_rl.test_client()
    resp = client_rl.get("/api/books/1")
    resp_limited = client_rl.get("/api/books/1")

    assert resp.status_code == 200
    assert resp_limited.status_code == 429
    assert resp_limited.json["errors"][0]["error"] == "Too Many Requests"
    assert resp_limited.json["errors"][0]["reason"] == "1 per 2 second"


def test_disable_docs():
    app_docs = create_app({"API_CREATE_DOCS": False})
    client_docs = app_docs.test_client()
    docs = client_docs.get("/docs")
    swagger = client_docs.get("/swagger.json")
    books = client_docs.get("/api/books")

    assert docs.status_code == 404
    assert swagger.status_code == 404
    assert books.status_code == 200


@pytest.fixture
def app_one():
    app_one = create_app_models(
        {
            "API_TITLE": "Automated test",
            "API_VERSION": "0.2.0",
            "API_IGNORE_UNDERSCORE_ATTRIBUTES": False,
            "API_ALLOW_CASCADE_DELETE": True,
            # Other configurations specific to this test
        }
    )
    yield app_one


@pytest.fixture
def client_one(app_one):
    return app_one.test_client()


def test_show_underscore_attributes(client_one):
    authors_response = client_one.get("/api/authors").json
    assert "_hiddenField" in authors_response["value"][0].keys()


def test_cascade_delete(client_one):

    authors = client_one.get("/api/authors").json["value"]
    author_id = authors[0]["id"]

    response = client_one.delete(f"/api/authors/{author_id}")
    assert response.status_code == 500


hooks = {
    "setup_hook": False,
    "return_hook": False,
    "patch_setup_hook": False,
    "get_return_hook": False,
}


def setup_hook(*args, **kwargs):
    global hooks
    hooks["setup_hook"] = True
    return kwargs


def return_hook(*args, **kwargs):
    global hooks
    hooks["return_hook"] = True
    return kwargs


def postdump_hook(data, **kwargs):
    if "title" in data:
        data["title"] = "Test postdump hook"
    return data


def patch_setup_hook(*args, **kwargs):
    global hooks
    hooks["patch_setup_hook"] = True
    return kwargs


def get_return_hook(*args, **kwargs):
    global hooks
    hooks["get_return_hook"] = True
    return kwargs


@pytest.fixture
def app_two():
    app_two = create_app_models(
        {
            "API_TITLE": "Automated test",
            "API_VERSION": "0.2.0",
            "API_IGNORE_UNDERSCORE_ATTRIBUTES": True,
            "API_ALLOW_CASCADE_DELETE": False,
            "API_GET_RETURN_CALLBACK": get_return_hook,
            "API_PATCH_SETUP_CALLBACK": patch_setup_hook,
            "API_SETUP_CALLBACK": setup_hook,
            "API_RETURN_CALLBACK": return_hook,
            "API_ERROR_CALLBACK": return_hook,
            "API_POSTDUMP_CALLBACK": postdump_hook,
            "API_ADDITIONAL_QUERY_PARAMS": [
                {
                    "name": "log",
                    "in": "query",
                    "description": "Log call into the database",  # optional
                    "required": False,  # optional
                    "deprecated": False,  # optional
                    "schema": {
                        "type": "string",  # see below for options available
                        "format": "password",  # see below for options available ... optional
                        "example": 1,  # optional
                    },
                }
            ],
            "API_POST_ADDITIONAL_QUERY_PARAMS": [
                {
                    "name": "log_one",
                    "in": "query",
                    "description": "Log call into the database",  # optional
                    "required": False,  # optional
                    "deprecated": False,  # optional
                    "schema": {
                        "type": "string",  # see below for options available
                        "format": "password",  # see below for options available ... optional
                        "example": 1,  # optional
                    },
                }
            ],
            # Other configurations specific to this test
        }
    )
    yield app_two


@pytest.fixture
def client_two(app_two):
    return app_two.test_client()


def test_hide_underscore_attributes(client_two):
    authors_response = client_two.get("/api/authors").json
    assert "_hiddenField" not in authors_response["value"][0].keys()


def test_show_underscore_attributes(client_two):

    app_under = create_app_models({"API_IGNORE_UNDERSCORE_ATTRIBUTES": False})
    client_under = app_under.test_client()

    authors_response = client_under.get("/api/authors").json
    assert "_hidden_field" in authors_response["value"][0].keys()


def test_callbacks(client_two):

    book_one = client_two.get("/api/books/1").json["value"]
    book_new = client_two.post("/api/books", json=book_one).json["value"]
    book_error = client_two.get("/api/books/9999999").json
    book_update = client_two.patch(
        "/api/books/" + str(book_one["id"]), json=book_one
    ).json["value"]
    global hooks
    assert hooks.get("setup_hook")
    assert hooks.get("patch_setup_hook")
    assert hooks.get("get_return_hook")
    assert hooks.get("return_hook")
    assert book_one["title"] == "Test postdump hook"


def test_global_query_param(client_two):
    swagger = client_two.get("/swagger.json").json

    params = [x["name"] for x in swagger["paths"]["/api/books"]["get"]["parameters"]]
    assert "log" in params


def test_post_specific_query_param(client_two):

    swagger = client_two.get("/swagger.json").json

    post_params = [
        x["name"] for x in swagger["paths"]["/api/books"]["post"]["parameters"]
    ]
    get_params = [
        x["name"] for x in swagger["paths"]["/api/books"]["get"]["parameters"]
    ]

    assert "log_one" in post_params
    assert not "log_one" in get_params


def test_cascade_delete(client_two):
    app_cascade_delete = create_app_models(
        {
            "API_ALLOW_CASCADE_DELETE": True,
        }
    )
    client_cascade_delete = app_cascade_delete.test_client()

    books = client_cascade_delete.get("/api/authors/1/books").json["value"]
    delete_response = client_cascade_delete.delete("/api/authors/1")
    assert "?cascade_delete=1" in delete_response.json["errors"][0]["reason"]
    delete_response_happy = client_cascade_delete.delete(
        "/api/authors/1?cascade_delete=1"
    )
    assert delete_response_happy.status_code == 200
    deleted_books = client_cascade_delete.get(
        "/api/books?id__in=" + str(tuple([x["id"] for x in books]))
    ).json["value"]
    deleted_author = client_cascade_delete.get("/api/authors/1").json["value"]
    assert len(deleted_books) == 0
    assert deleted_author is None
