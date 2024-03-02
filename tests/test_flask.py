import pytest

from demo.basic_1.basic import create_app
from demo.model_extension_2.model import create_app as create_app_models


@pytest.fixture
def app_model_meta():
    app_model_meta = create_app({
        'API_TITLE': 'Automated test',
        'API_VERSION': '0.2.0',
        # Other configurations specific to this test
    })
    yield app_model_meta


@pytest.fixture
def client_meta_model(app_model_meta):
    return app_model_meta.test_client()


def test_model_block_methods(client_meta_model):
    app = create_app_models()

    client = app.test_client()
    resp = client.get("/api/books/1")

    assert len(resp.json["value"]["created"]) > 0

    client = app.test_client()
    resp_auth = client.get("/api/authors/1")

    resp_delete_fail = client.delete("/api/authors/1")
    resp_delete = client.delete("/api/authors/1?cascade_delete=1")
    resp_patch = client.patch("/api/authors", json=resp_auth.json["value"])
    resp_post = client.post("/api/authors", json=resp_auth.json["value"])

    assert resp_delete_fail.status_code == 500
    assert resp_patch.status_code == 200
    assert resp_post.status_code == 200
    assert resp_delete.status_code == 405

# def test_post_get_config_method():
#     def add_key_to_output(*args, **kwargs):
#         output = kwargs.get("output")
#         output.update({"foo": "bar"})
#         return output
#
#     class Meta:
#         API_POST_GET = add_key_to_output
#
#     from demo.basic_1.basic.models import Book
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
