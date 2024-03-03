import pytest

from demo.basic_factory.basic_factory import create_app


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


def test_get(client):
    get_resp = client.get('/api/books/1')
    get_resp_none = client.get('/api/books/99999')
    get_resp_child = client.get('/api/authors/1/books')

    assert get_resp.status_code == 200
    assert get_resp.json["value"]["id"] == 1

    assert get_resp_none.status_code == 404

    assert get_resp_child.status_code == 200
    assert len(get_resp_child.json["value"]) > 0


def test_delete(client):
    delete_response = client.delete('/api/books/1')
    delete_response_fail = client.delete('/api/books/99999999')
    get_response = client.get('/api/books/1')

    assert delete_response.status_code == 200
    assert get_response.json["value"] == None
    assert delete_response_fail.status_code == 404
    assert delete_response_fail.json["error"]["error"] == "Not Found"


def test_delete_with_cascade(client):
    books_pre_delete = client.get("/api/authors/1/books")

    resp_delete_fail = client.delete("/api/authors/1")
    resp_delete = client.delete("/api/authors/1?cascade_delete=1")
    books_post_delete = client.get("/api/authors/1/books")

    assert books_pre_delete.status_code == 200
    assert len(books_pre_delete.json["value"]) > 0

    assert resp_delete_fail.status_code == 500

    assert resp_delete.status_code == 200

    assert books_post_delete.status_code == 404
    assert books_post_delete.json["value"] is None


def test_patch(client):
    get_response = client.get('/api/books/1')
    data = get_response.json
    data["value"]["title"] = "New Title"
    patch_response = client.patch('/api/books/1', json=data["value"])
    new_get_response = client.get('/api/books/1')

    assert patch_response.status_code == 200
    assert new_get_response.json["value"]["title"] == "New Title"


def test_hybrid_and_patch(client):
    get_response = client.get('/api/authors/1')
    data = get_response.json
    data["value"]["firstName"] = "Foo"
    data["value"]["lastName"] = "Bar"
    patch_response = client.patch('/api/authors/1', json=data["value"])
    new_get_response = client.get('/api/authors/1')

    assert patch_response.status_code == 200
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


def test_basic_get_books(client):
    response = client.get('/api/books')
    assert isinstance(response.json["value"], list)
    assert "isbn" in response.json["value"][0]
    assert "title" in response.json["value"][0]


def test_patch_deleted(client):
    books_pre_delete = client.get("/api/books/1")
    resp_delete = client.delete("/api/books/1")

    book_data = books_pre_delete.json["value"]
    book_data["title"] = "New Title"

    resp_patch_fail = client.patch("/api/books/1", json=book_data)

    assert resp_delete.status_code == 200
    assert resp_patch_fail.status_code == 404
