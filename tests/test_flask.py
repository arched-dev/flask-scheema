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
def client(app):
    return app.test_client()


# Configuration 2
# Test using Configuration 1
def test_basic_change_title_and_version(client):
    response = client.get('/swagger.json')

    assert response.json["info"]["title"] == "Automated test"
    assert response.json["info"]["version"] == "0.2.0"

    response = client.get('/docs')
    html = response.data.decode()
    assert "Automated test" in html
    assert "0.2.0" in html


def test_delete(client):
    delete_response = client.delete('/api/books/1')
    delete_response_fail = client.delete('/api/books/99999999')
    get_response = client.get('/api/books/1')

    assert delete_response.status_code == 200
    assert get_response.json["value"] == None
    assert delete_response_fail.status_code == 404
    assert delete_response_fail.json["error"]["error"] == "Not Found"

def test_put(client):
    get_response = client.get('/api/books/1')
    data = get_response.json
    data["value"]["title"] = "New Title"
    put_response = client.put('/api/books/1', json=data["value"])
    new_get_response = client.get('/api/books/1')

    assert put_response.status_code == 200
    assert new_get_response.json["value"]["title"] == "New Title"

def test_hybrid_and_put(client):
    get_response = client.get('/api/authors/1')
    data = get_response.json
    data["value"]["firstName"] = "Foo"
    data["value"]["lastName"] = "Bar"
    put_response = client.put('/api/authors/1', json=data["value"])
    new_get_response = client.get('/api/authors/1')

    assert put_response.status_code == 200
    assert new_get_response.json["value"]["fullName"] == "Foo Bar"


def test_post(client):
    data = {"biography": "Foo is a Baz",
    "dateOfBirth": "1900-01-01",
    "firstName": "Foo",
    "lastName": "Bar",
    "nationality": "Bazville",
    "website": "https://foobar.baz"}

    post_response = client.post('/api/authors', json=data)

    new_id = post_response.json["value"]["id"]

    get_response = client.get(f'/api/authors/{new_id}')

    assert post_response.status_code == 200
    assert post_response.json["value"]["fullName"] == "Foo Bar"

    assert get_response.status_code == 200
    assert get_response.json["value"]["fullName"] == "Foo Bar"



@pytest.fixture
def app_one():
    app = create_app({
        'API_TITLE': 'Automated test',
        'API_VERSION': '0.2.0',
        'API_SERIALIZE_RELATIONS': False,
        # Other configurations specific to this test
    })
    yield app


@pytest.fixture
def client_one(app_one):
    return app_one.test_client()


def test_basic_get_books(client_one):
    response = client_one.get('/api/books')
    assert isinstance(response.json["value"], list)
    assert "isbn" in response.json["value"][0]
    assert "title" in response.json["value"][0]


def test_basic_select(client_one):
    response = client_one.get('/api/books?fields=isbn,title')
    assert isinstance(response.json["value"], list)
    assert "isbn" in response.json["value"][0]
    assert "title" in response.json["value"][0]
    assert "publication_date" not in response.json["value"][0]


def test_basic_filter(client_one):
    book_id = client_one.get('/api/books/1').json["value"]["id"]
    filtered_books = client_one.get('/api/books?id__eq=1').json["value"]

    assert filtered_books[0]["id"] == book_id
    assert len(filtered_books) == 1


def test_basic_no_change_api_output(client_one):
    books = client_one.get('/api/books').json

    assert "datetime" in books.keys()
    assert "api_version" in books.keys()
    assert "status_code" in books.keys()
    assert "count" in books.keys()
    assert "next_url" in books.keys()
    assert "previous_url" in books.keys()
    assert "error" in books.keys()

    book = client_one.get('/api/books/1').json

    assert "datetime" in book.keys()
    assert "api_version" in book.keys()
    assert "status_code" in book.keys()
    assert "count" in book.keys()
    assert "error" in book.keys()

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

@pytest.fixture
def app_change_out():
    app = create_app({
        'API_DUMP_DATETIME': False,
        'API_DUMP_VERSION': False,
        'API_DUMP_STATUS_CODE': False,
        'API_DUMP_COUNT': False,
        'API_DUMP_RESPONSE_MS': False,
        'API_DUMP_NULL_NEXT_URL': False,
        'API_DUMP_NULL_PREVIOUS_URL': False,
        'API_DUMP_NULL_ERROR': False,
    })
    yield app

@pytest.fixture
def client_change_out(app_change_out):
    return app_change_out.test_client()


def test_basic_change_api_output(client_change_out):
    book = client_change_out.get('/api/books/1').json
    assert book.keys() == {"value"}


# def test_post_get_config_method():
#     def add_key_to_output(*args, **kwargs):
#         output = kwargs.get("output")
#         output.update({"foo": "bar"})
#         return output
#
#     class Meta:
#         API_POST_GET = add_key_to_output
#
#     from demo.basic.basic.models import Book
#
#     setattr(Book, "Meta", Meta)
#
#     get_app = create_app()
#
#     test_client = get_app.test_client()
#     book = test_client.get('/api/books/1').json
#     assert book.get("foo") == "bar"



#
# def test_post_get_model_method():
#     assert 1 == 2
#
#
# def test_post_post_config_method():
#     assert 1 == 2
#
#
# def test_post_post_model_method():
#     assert 1 == 2
#
#
# def test_post_put_config_method():
#     assert 1 == 2
#
#
# def test_post_put_model_method():
#     assert 1 == 2
#
#
# def test_post_delete_config_method():
#     assert 1 == 2
#
#
# def test_post_delete_model_method():
#     assert 1 == 2
