import pytest

from demo.basic.basic import create_app
from demo.basic.basic.models import Author

from demo.model_extension.model import create_app as create_app_models

@pytest.fixture
def app():
    app = create_app({
        'API_TITLE': 'Automated test',
        'API_VERSION': '0.2.0',
    })
    yield app


@pytest.fixture
def client(app):
    return app.test_client()



def test_basic_select(client):
    response = client.get('/api/books?fields=isbn,title')
    assert isinstance(response.json["value"], list)
    assert "isbn" in response.json["value"][0]
    assert "title" in response.json["value"][0]
    assert "publication_date" not in response.json["value"][0]


def test_basic_filter(client):
    book_id = client.get('/api/books/1').json["value"]["id"]
    filtered_books = client.get('/api/books?id__eq=1').json["value"]

    assert filtered_books[0]["id"] == book_id
    assert len(filtered_books) == 1


def test_basic_pagination(client, app):
    books = client.get('/api/books?order_by=id').json
    assert len(books["value"]) == 20

    app.config["API_PAGE_SIZE"] = 5
    books = client.get('/api/books?order_by=id').json
    assert len(books["value"]) == 5

    books = client.get('/api/books?order_by=id&limit=10').json
    assert len(books["value"]) == 10

    books = client.get(books["nextUrl"]).json
    assert len(books["value"]) == 10
    assert books["value"][0]["id"] == 11

    books_error = client.get('/api/books?order_by=id&limit=d')
    assert books_error.status_code == 400

    books_error = client.get('/api/books?order_by=id&page-=d&limit=d')
    assert books_error.status_code == 400


def test_basic_sort(client):
    books = client.get('/api/books?order_by=id').json
    assert books["value"][0]["id"] == 1
    books = client.get('/api/books?order_by=-id').json
    assert books["value"][0]["id"] == books["totalCount"]
