import pytest
from demo.basic.basic import create_app


@pytest.fixture
def app():
    app = create_app({
        'API_TITLE': 'Automated test',
        'API_VERSION': '0.2.0',
        # Other configurations specific to this test
    })
    yield app


@pytest.fixture
def client_one(app_one):
    return app_one.test_client()


# check to make sure that the title and version are changed
def test_basic_change_title_and_version(client):
    response = client.get('/swagger.json')

    assert response.json["info"]["title"] == "Automated test"
    assert response.json["info"]["version"] == "0.2.0"

    response = client.get('/docs')
    html = response.data.decode()
    assert "Automated test" in html
    assert "0.2.0" in html


# block methods from the API
def test_block_methods():
    app = create_app({
        'API_BLOCK_METHODS': ["POST", "PUT", "DELETE"],
    })

    client = app.test_client()
    resp = client.get("/api/books/1")

    assert len(resp.json["value"]["created"]) > 0

    resp_put = client.put("/api/books", json=resp.json["value"])
    resp_post = client.post("/api/books", json=resp.json["value"])
    resp_delete = client.delete("/api/books/1")

    assert resp_put.status_code == 405
    assert resp_post.status_code == 405
    assert resp_delete.status_code == 405


# check to make sure that read only is working
def test_read_only():
    app = create_app({
        'API_READ_ONLY': True,
    })

    client = app.test_client()
    resp = client.get("/api/books/1")

    assert len(resp.json["value"]["created"]) > 0

    resp_put = client.put("/api/books", json=resp.json["value"])
    resp_post = client.post("/api/books", json=resp.json["value"])
    resp_delete = client.delete("/api/books/1")

    assert resp_put.status_code == 405
    assert resp_post.status_code == 405
    assert resp_delete.status_code == 405


# check to make sure that the base response from the API contains the correct keys
def test_basic_no_change_api_output(client_one):
    books = client_one.get('/api/books').json

    assert "datetime" in books.keys()
    assert "apiVersion" in books.keys()
    assert "statusCode" in books.keys()
    assert "totalCount" in books.keys()
    assert "nextUrl" in books.keys()
    assert "previousUrl" in books.keys()
    assert "error" in books.keys()

    book = client_one.get('/api/books/1').json

    assert "datetime" in book.keys()
    assert "apiVersion" in book.keys()
    assert "statusCode" in book.keys()
    assert "totalCount" in book.keys()
    assert "error" in book.keys()


# make sure camel case is and isn't used.
def test_change_to_camel_output():
    app_cam = create_app({
        'API_CONVERT_TO_CAMEL_CASE': True,
    })
    client_camel = app_cam.test_client()
    book = client_camel.get('/api/books/1').json

    assert "publicationDate" in book["value"].keys()

    app_snake = create_app({
        'API_CONVERT_TO_CAMEL_CASE': False,
    })
    client_snake = app_snake.test_client()
    book = client_snake.get('/api/books/1').json

    assert "publication_date" in book["value"].keys()


def test_convert_camel(app):
    app = create_app({
        'API_CONVERT_TO_CAMEL_CASE': False,
    })

    client = app.test_client()
    resp = client.get("/api/books/1")

    assert "publication_date" in resp.json["value"].keys()
    assert "total_count" in resp.json.keys()

    app = create_app({
        'API_CONVERT_TO_CAMEL_CASE': True,
    })

    client = app.test_client()
    resp = client.get("/api/books/1")

    assert "publicationDate" in resp.json["value"].keys()
    assert "totalCount" in resp.json.keys()


# change the api base url prefix
def test_change_api_route():
    app_prefix = create_app({
        'API_PREFIX': "/my_api",
    })
    client_prefix = app_prefix.test_client()
    fail_book = client_prefix.get('/api/books/1')
    book = client_prefix.get('/my_api/books/1')

    assert fail_book.status_code == 404
    assert book.status_code == 200
    assert "title" in book.json["value"].keys()


# change the api base output
@pytest.fixture
def app_change_out():
    app = create_app({
        'API_DUMP_DATETIME': False,
        'API_DUMP_VERSION': False,
        'API_DUMP_STATUS_CODE': False,
        'API_DUMP_TOTAL_COUNT': False,
        'API_DUMP_RESPONSE_MS': False,
        'API_DUMP_NULL_NEXT_URL': False,
        'API_DUMP_NULL_PREVIOUS_URL': False,
        'API_DUMP_NULL_ERROR': False,
    })
    yield app


@pytest.fixture
def client_change_out(app_change_out):
    return app_change_out.test_client()


def test_basic_change_api_base_output(client_change_out):
    book = client_change_out.get('/api/books/1').json
    assert book.keys() == {"value"}


# check the different types of serialization   "json" | "url" | "hybrid" | None
def test_serialize_url_only():
    app = create_app({'API_SERIALIZATION_TYPE': "url"})
    client = app.test_client()
    resp = client.get("/api/books/1")

    assert resp.json["value"]["author"] == '/api/books/1/authors'
    assert resp.json["value"]["categories"] == '/api/books/1/categories'
    assert resp.json["value"]["reviews"] == '/api/books/1/reviews'


def test_serialize_hybrid():
    app = create_app({'API_SERIALIZATION_TYPE': "hybrid"})
    client = app.test_client()
    resp = client.get("/api/books/1")

    assert isinstance(resp.json["value"]["author"], dict)
    assert resp.json["value"]["categories"] == '/api/books/1/categories'
    assert resp.json["value"]["reviews"] == '/api/books/1/reviews'


def test_serialize_json():
    app = create_app({'API_SERIALIZATION_TYPE': "json"})
    client = app.test_client()
    resp = client.get("/api/books/1")

    assert isinstance(resp.json["value"]["author"], dict)
    assert isinstance(resp.json["value"]["categories"], list)
    assert isinstance(resp.json["value"]["reviews"], list)


def test_serialize_none():
    app = create_app({'API_SERIALIZATION_TYPE': False})
    client = app.test_client()
    resp = client.get("/api/books/1")

    assert "author" not in resp.json["value"]
    assert "categories" not in resp.json["value"]
    assert "reviews" not in resp.json["value"]
