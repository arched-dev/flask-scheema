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


# block methods from the API
def test_block_methods():
    app_new = create_app(
        {
            "API_BLOCK_METHODS": ["POST", "PATCH", "DELETE"],
        }
    )

    client_new = app_new.test_client()
    resp = client_new.get("/api/books/1")

    assert len(resp.json["value"]["created"]) > 0

    resp_patch = client_new.patch("/api/books", json=resp.json["value"])
    resp_post = client_new.post("/api/books", json=resp.json["value"])
    resp_delete = client_new.delete("/api/books/1")

    assert resp_patch.status_code == 405
    assert resp_post.status_code == 405
    assert resp_delete.status_code == 405


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
    assert "apiVersion" in books.keys()
    assert "statusCode" in books.keys()
    assert "totalCount" in books.keys()
    assert "nextUrl" in books.keys()
    assert "previousUrl" in books.keys()
    assert "error" in books.keys()

    book = client.get("/api/books/1").json

    assert "datetime" in book.keys()
    assert "apiVersion" in book.keys()
    assert "statusCode" in book.keys()
    assert "totalCount" in book.keys()
    assert "error" in book.keys()


# make sure camel case is and isn't used.
def test_change_to_camel_output():
    app_cam = create_app(
        {
            "API_CONVERT_TO_CAMEL_CASE": True,
        }
    )
    client_camel = app_cam.test_client()
    book = client_camel.get("/api/books/1").json

    assert "publicationDate" in book["value"].keys()

    app_snake = create_app(
        {
            "API_CONVERT_TO_CAMEL_CASE": False,
        }
    )
    client_snake = app_snake.test_client()
    book = client_snake.get("/api/books/1").json

    assert "publication_date" in book["value"].keys()


def test_convert_camel(app):
    app = create_app(
        {
            "API_CONVERT_TO_CAMEL_CASE": False,
        }
    )

    client = app.test_client()
    resp = client.get("/api/books/1")

    assert "publication_date" in resp.json["value"].keys()
    assert "total_count" in resp.json.keys()

    app = create_app(
        {
            "API_CONVERT_TO_CAMEL_CASE": True,
        }
    )

    client = app.test_client()
    resp = client.get("/api/books/1")

    assert "publicationDate" in resp.json["value"].keys()
    assert "totalCount" in resp.json.keys()


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



def setup_hook(*args, **kwargs):

    session["setup_hook"] = True
    return kwargs

def return_hook(*args, **kwargs):

    session["return_hook"] = True
    return kwargs

def patch_setup_hook(*args, **kwargs):

    session["patch_setup_hook"] = True
    return kwargs

def get_return_hook(*args, **kwargs):

    session["get_return_hook"] = True
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
            "API_ADDITIONAL_QUERY_PARAMS": [{
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
            }],
            "API_POST_ADDITIONAL_QUERY_PARAMS": [{
                "name": "log_one",
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
            # Other configurations specific to this test
        }
    )
    yield app_two


@pytest.fixture
def client_two(app_two):
    return app_two.test_client()


def test_hide_underscore_attributes(client_two):
    authors_response = client_two.get("/api/authors").json
    assert "_hiddenField" in authors_response["value"][0].keys()

def test_callbacks(client_two):

    with client_two.application.test_request_context():

        book_error = client_two.get("/api/books/9999999").json
        book_one = client_two.get("/api/books/1").json["value"]
        book_new = client_two.post("/api/books", json=book_one).json["value"]
        book_update = client_two.patch("/api/books/" + str(book_one["id"]), json=book_one).json["value"]

        assert session.get("setup_hook")
        assert session.get("patch_setup_hook")
        assert session.get("get_return_hook")
        assert session.get("return_hook")

def test_global_query_param(client_two):
    swagger = client_two.get("/swagger.json").json

    params = [x["name"] for x in swagger["paths"]["/api/books"]["post"]["parameters"]]
    assert "log" in params
def test_post_specific_query_param(client_two):

    swagger = client_two.get("/swagger.json").json

    post_params = [x["name"] for x in swagger["paths"]["/api/books"]["post"]["parameters"]]
    get_params = [x["name"] for x in swagger["paths"]["/api/books"]["get"]["parameters"]]

    assert "log_one" in post_params
    assert not "log_one" in get_params


def test_cascade_delete(client_two):
    assert 1 == 2
