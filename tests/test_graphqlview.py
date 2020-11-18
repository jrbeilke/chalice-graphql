import json
from io import StringIO
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


def json_dump_kwarg(**kwargs):
    return json.dumps(kwargs)


def json_dump_kwarg_list(**kwargs):
    return json.dumps([kwargs])


def test_index(test_client):
    response = test_client.http.get('/')

    assert response.status_code == 200
    assert response.json_body == {'hello': 'world'}


def test_allows_get_with_query_param(test_client):
    response = test_client.http.get(url_string('/graphql', query="{test}"))

    assert response.status_code == 200
    assert response.json_body == {"data": {"test": "Hello World"}}


def test_allows_get_with_variable_values(test_client):
    response = test_client.http.get(
        url_string(
            '/graphql',
            query="query helloWho($who: String){ test(who: $who) }",
            variables=json.dumps({"who": "Dolly"}),
        )
    )

    assert response.status_code == 200
    assert response.json_body == {"data": {"test": "Hello Dolly"}}


def test_allows_get_with_operation_name(test_client):
    response = test_client.http.get(
        url_string(
            '/graphql',
            query="""
        query helloYou { test(who: "You"), ...shared }
        query helloWorld { test(who: "World"), ...shared }
        query helloDolly { test(who: "Dolly"), ...shared }
        fragment shared on QueryRoot {
          shared: test(who: "Everyone")
        }
        """,
            operationName="helloWorld",
        )
    )

    assert response.status_code == 200
    assert response.json_body == {
        "data": {"test": "Hello World", "shared": "Hello Everyone"}
    }


def test_reports_validation_errors(test_client):
    response = test_client.http.get(url_string('/graphql', query="{ test, unknownOne, unknownTwo }"))

    assert response.status_code == 400
    assert response.json_body == {
        "errors": [
            {
                "message": "Cannot query field 'unknownOne' on type 'QueryRoot'.",
                "locations": [{"line": 1, "column": 9}],
                "path": None,
            },
            {
                "message": "Cannot query field 'unknownTwo' on type 'QueryRoot'.",
                "locations": [{"line": 1, "column": 21}],
                "path": None,
            },
        ]
    }


def test_errors_when_missing_operation_name(test_client):
    response = test_client.http.get(
        url_string(
            '/graphql',
            query="""
        query TestQuery { test }
        mutation TestMutation { writeTest { test } }
        """,
        )
    )

    assert response.status_code == 400
    assert response.json_body == {
        "errors": [
            {
                "message": "Must provide operation name if query contains multiple operations.",  # noqa: E501
                "locations": None,
                "path": None,
            }
        ]
    }


def test_errors_when_sending_a_mutation_via_get(test_client):
    response = test_client.http.get(
        url_string(
            '/graphql',
            query="""
        mutation TestMutation { writeTest { test } }
        """,
        )
    )
    assert response.status_code == 405
    assert response.json_body == {
        "errors": [
            {
                "message": "Can only perform a mutation operation from a POST request.",
                "locations": None,
                "path": None,
            }
        ]
    }


def test_errors_when_selecting_a_mutation_within_a_get(test_client):
    response = test_client.http.get(
        url_string(
            '/graphql',
            query="""
        query TestQuery { test }
        mutation TestMutation { writeTest { test } }
        """,
            operationName="TestMutation",
        )
    )

    assert response.status_code == 405
    assert response.json_body == {
        "errors": [
            {
                "message": "Can only perform a mutation operation from a POST request.",
                "locations": None,
                "path": None,
            }
        ]
    }


def test_allows_mutation_to_exist_within_a_get(test_client):
    response = test_client.http.get(
        url_string(
            '/graphql',
            query="""
        query TestQuery { test }
        mutation TestMutation { writeTest { test } }
        """,
            operationName="TestQuery",
        )
    )

    assert response.status_code == 200
    assert response.json_body == {"data": {"test": "Hello World"}}


def test_allows_post_with_json_encoding(test_client):
    response = test_client.http.post(
        url_string('/graphql'),
        body=json_dump_kwarg(query="{test}"),
        headers={'Content-Type': 'application/json'},
    )

    assert response.status_code == 200
    assert response.json_body == {"data": {"test": "Hello World"}}


def test_allows_sending_a_mutation_via_post(test_client):
    response = test_client.http.post(
        url_string('/graphql'),
        body=json_dump_kwarg(query="mutation TestMutation { writeTest { test } }"),
        headers={'Content-Type': 'application/json'},
    )

    assert response.status_code == 200
    assert response.json_body == {"data": {"writeTest": {"test": "Hello World"}}}


def test_allows_post_with_url_encoding(test_client):
    response = test_client.http.post(
        url_string('/graphql'),
        body=urlencode(dict(query="{test}")),
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
    )

    assert response.status_code == 200
    assert response.json_body == {"data": {"test": "Hello World"}}


def test_supports_post_json_query_with_string_variables(test_client):
    response = test_client.http.post(
        url_string('/graphql'),
        body=json_dump_kwarg(
            query="query helloWho($who: String){ test(who: $who) }",
            variables=json.dumps({"who": "Dolly"}),
        ),
        headers={'Content-Type': 'application/json'},
    )

    assert response.status_code == 200
    assert response.json_body == {"data": {"test": "Hello Dolly"}}


def test_supports_post_json_query_with_json_variables(test_client):
    response = test_client.http.post(
        url_string('/graphql'),
        body=json_dump_kwarg(
            query="query helloWho($who: String){ test(who: $who) }",
            variables={"who": "Dolly"},
        ),
        headers={'Content-Type': 'application/json'},
    )

    assert response.status_code == 200
    assert response.json_body == {"data": {"test": "Hello Dolly"}}


def test_supports_post_url_encoded_query_with_string_variables(test_client):
    response = test_client.http.post(
        url_string('/graphql'),
        body=urlencode(
            dict(
                query="query helloWho($who: String){ test(who: $who) }",
                variables=json.dumps({"who": "Dolly"}),
            )
        ),
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
    )

    assert response.status_code == 200
    assert response.json_body == {"data": {"test": "Hello Dolly"}}


def test_supports_post_json_quey_with_get_variable_values(test_client):
    response = test_client.http.post(
        url_string('/graphql', variables=json.dumps({"who": "Dolly"})),
        body=json_dump_kwarg(query="query helloWho($who: String){ test(who: $who) }",),
        headers={'Content-Type': 'application/json'},
    )

    assert response.status_code == 200
    assert response.json_body == {"data": {"test": "Hello Dolly"}}


def test_post_url_encoded_query_with_get_variable_values(test_client):
    response = test_client.http.post(
        url_string('/graphql', variables=json.dumps({"who": "Dolly"})),
        body=urlencode(dict(query="query helloWho($who: String){ test(who: $who) }",)),
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
    )

    assert response.status_code == 200
    assert response.json_body == {"data": {"test": "Hello Dolly"}}


def test_supports_post_raw_text_query_with_get_variable_values(test_client):
    response = test_client.http.post(
        url_string('/graphql', variables=json.dumps({"who": "Dolly"})),
        body="query helloWho($who: String){ test(who: $who) }",
        headers={'Content-Type': 'application/graphql'},
    )

    assert response.status_code == 200
    assert response.json_body == {"data": {"test": "Hello Dolly"}}


def test_allows_post_with_operation_name(test_client):
    response = test_client.http.post(
        url_string('/graphql'),
        body=json_dump_kwarg(
            query="""
        query helloYou { test(who: "You"), ...shared }
        query helloWorld { test(who: "World"), ...shared }
        query helloDolly { test(who: "Dolly"), ...shared }
        fragment shared on QueryRoot {
          shared: test(who: "Everyone")
        }
        """,
            operationName="helloWorld",
        ),
        headers={'Content-Type': 'application/json'},
    )

    assert response.status_code == 200
    assert response.json_body == {
        "data": {"test": "Hello World", "shared": "Hello Everyone"}
    }


def test_allows_post_with_get_operation_name(test_client):
    response = test_client.http.post(
        url_string('/graphql', operationName="helloWorld"),
        body="""
    query helloYou { test(who: "You"), ...shared }
    query helloWorld { test(who: "World"), ...shared }
    query helloDolly { test(who: "Dolly"), ...shared }
    fragment shared on QueryRoot {
      shared: test(who: "Everyone")
    }
    """,
        headers={'Content-Type': 'application/graphql'},
    )

    assert response.status_code == 200
    assert response.json_body == {
        "data": {"test": "Hello World", "shared": "Hello Everyone"}
    }


def test_not_pretty_by_default(test_client):
    response = test_client.http.get(url_string('/graphql', query="{test}"))

    assert response.body.decode() == '{"data":{"test":"Hello World"}}'


def test_supports_pretty_printing_by_request(test_client):
    response = test_client.http.get(url_string('/graphql', query="{test}", pretty="1"))

    assert response.body.decode() == (
        "{\n" '  "data": {\n' '    "test": "Hello World"\n' "  }\n" "}"
    )


def test_handles_field_errors_caught_by_graphql(test_client):
    response = test_client.http.get(url_string('/graphql', query="{thrower}"))
    assert response.status_code == 200
    assert response.json_body == {
        "errors": [
            {
                "locations": [{"column": 2, "line": 1}],
                "path": ["thrower"],
                "message": "Throws!",
            }
        ],
        "data": None,
    }


def test_handles_syntax_errors_caught_by_graphql(test_client):
    response = test_client.http.get(url_string('/graphql', query="syntaxerror"))
    assert response.status_code == 400
    assert response.json_body == {
        "errors": [
            {
                "locations": [{"column": 1, "line": 1}],
                "message": "Syntax Error: Unexpected Name 'syntaxerror'.",
                "path": None,
            }
        ]
    }


def test_handles_errors_caused_by_a_lack_of_query(test_client):
    response = test_client.http.get(url_string('/graphql'))

    assert response.status_code == 400
    assert response.json_body == {
        "errors": [
            {"message": "Must provide query string.", "locations": None, "path": None}
        ]
    }


def test_handles_batch_correctly_if_is_disabled(test_client):
    response = test_client.http.post(url_string('/graphql'), body="[]", headers={'Content-Type': 'application/json'})

    assert response.status_code == 400
    assert response.json_body == {
        "errors": [
            {
                "message": "Batch GraphQL requests are not enabled.",
                "locations": None,
                "path": None,
            }
        ]
    }


def test_handles_incomplete_json_bodies(test_client):
    response = test_client.http.post(
        url_string('/graphql'), body='{"query":', headers={'Content-Type': 'application/json'}
    )

    assert response.status_code == 400
    assert response.json_body == {
        "errors": [
            {"message": "POST body sent invalid JSON.", "locations": None, "path": None}
        ]
    }


def test_handles_plain_post_text(test_client):
    response = test_client.http.post(
        url_string('/graphql', variables=json.dumps({"who": "Dolly"})),
        body="query helloWho($who: String){ test(who: $who) }",
        headers={'Content-Type': 'text/plain'},
    )
    assert response.status_code == 400
    assert response.json_body == {
        "errors": [
            {"message": "Must provide query string.", "locations": None, "path": None}
        ]
    }


def test_handles_poorly_formed_variables(test_client):
    response = test_client.http.get(
        url_string(
            '/graphql',
            query="query helloWho($who: String){ test(who: $who) }",
            variables="who:You",
        )
    )
    assert response.status_code == 400
    assert response.json_body == {
        "errors": [
            {"message": "Variables are invalid JSON.", "locations": None, "path": None}
        ]
    }


def test_handles_unsupported_http_methods(test_client):
    response = test_client.http.put(url_string('/graphql', query="{test}"))
    assert response.status_code == 405
    # TODO: Add this back in once Chalice supports returning the Allow header
    # https://github.com/aws/chalice/issues/1583
#    assert response.headers["Allow"] in ["GET, POST", "HEAD, GET, POST, OPTIONS"]
    assert response.json_body == {
        "errors": [
            {
                "message": "GraphQL only supports GET and POST requests.",
                "locations": None,
                "path": None,
            }
        ]
    }


def test_passes_request_into_request_context(test_client):
    response = test_client.http.get(url_string('/graphql', query="{request}", q="testing"))

    assert response.status_code == 200
    assert response.json_body == {"data": {"request": "testing"}}


# TODO: Chalice lacks support for multipart requests
# https://github.com/aws/chalice/issues/796
#def test_post_multipart_data(test_client):
#    query = "mutation TestMutation { writeTest { test } }"
#    response = test_client.http.post(
#        url_string('/graphql'),
#        body={"query": query, "file": (StringIO(), "text1.txt")},
#        headers={'Content-Type': 'multipart/form-data'},
#    )
#
#    assert response.status_code == 200
#    assert response.json_body == {
#        "data": {u"writeTest": {u"test": u"Hello World"}}
#    }


def test_batch_allows_post_with_json_encoding(test_client):
    response = test_client.http.post(
        url_string('/graphql/batch'),
        body=json_dump_kwarg_list(
            # id=1,
            query="{test}"
        ),
        headers={'Content-Type': 'application/json'},
    )

    assert response.status_code == 200
    assert response.json_body == [
        {
            # 'id': 1,
            "data": {"test": "Hello World"}
        }
    ]


def test_batch_supports_post_json_query_with_json_variables(test_client):
    response = test_client.http.post(
        url_string('/graphql/batch'),
        body=json_dump_kwarg_list(
            # id=1,
            query="query helloWho($who: String){ test(who: $who) }",
            variables={"who": "Dolly"},
        ),
        headers={'Content-Type': 'application/json'},
    )

    assert response.status_code == 200
    assert response.json_body == [
        {
            # 'id': 1,
            "data": {"test": "Hello Dolly"}
        }
    ]


def test_batch_allows_post_with_operation_name(test_client):
    response = test_client.http.post(
        url_string('/graphql/batch'),
        body=json_dump_kwarg_list(
            # id=1,
            query="""
            query helloYou { test(who: "You"), ...shared }
            query helloWorld { test(who: "World"), ...shared }
            query helloDolly { test(who: "Dolly"), ...shared }
            fragment shared on QueryRoot {
              shared: test(who: "Everyone")
            }
            """,
            operationName="helloWorld",
        ),
        headers={'Content-Type': 'application/json'},
    )

    assert response.status_code == 200
    assert response.json_body == [
        {
            # 'id': 1,
            "data": {"test": "Hello World", "shared": "Hello Everyone"}
        }
    ]
