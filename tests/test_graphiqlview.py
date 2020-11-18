from urllib.parse import urlencode

from chalice.test import Client
import pytest

from .app import app


@pytest.fixture
def test_client():
    with Client(app) as client:
        yield client


def url_string(path, **url_params):
    if url_params:
        path += "?" + urlencode(url_params)

    return path


def test_graphiql_is_enabled(test_client):
    response = test_client.http.get('/graphql', headers={"Accept": "text/html"})
    assert response.status_code == 200


def test_graphiql_renders_pretty(test_client):
    response = test_client.http.get(
        url_string('/graphql', query="{test}"),
        headers={"Accept": "text/html"}
    )
    assert response.status_code == 200
    pretty_response = (
        "{\n"
        '  "data": {\n'
        '    "test": "Hello World"\n'
        "  }\n"
        "}".replace('"', '\\"').replace("\n", "\\n")
    )

    assert pretty_response in response.body.decode("utf-8")


def test_graphiql_default_title(test_client):
    response = test_client.http.get('/graphql', headers={"Accept": "text/html"})
    assert "<title>GraphiQL</title>" in response.body.decode("utf-8")
