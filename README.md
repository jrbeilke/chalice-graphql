# Chalice-GraphQL

Adds [GraphQL] support to your [Chalice] application.

Based on [flask-graphql] by [Syrus Akbary] and [aiohttp-graphql] by [Devin Fee].

[![travis][travis-image]][travis-url]
[![coveralls][coveralls-image]][coveralls-url]

[GraphQL]: http://graphql.org/
[Chalice]: https://aws.github.io/chalice/
[Syrus Akbary]: https://github.com/syrusakbary
[Devin Fee]: https://github.com/dfee
[travis-image]: https://travis-ci.org/jrbeilke/chalice-graphql.svg?branch=master
[travis-url]: https://travis-ci.org/jrbeilke/chalice-graphql
[coveralls-image]: https://coveralls.io/repos/github/jrbeilke/chalice-graphql/badge.svg?branch=master
[coveralls-url]: https://coveralls.io/github/jrbeilke/chalice-graphql?branch=master

## Usage

Add the `GraphQLView` from `chalice_graphql` to dispatch requests for your desired route(s)

```python
from chalice import Chalice
from chalice_graphql import GraphQLView

from schema import schema

app = Chalice(app_name='helloworld')

@app.route(
    '/graphql',
    methods=['GET', 'POST'],
    content_types=['application/graphql', 'application/json', 'application/x-www-form-urlencoded']
)
def graphql():
    gql_view = GraphQLView(schema=schema, graphiql=True)
    return gql_view.dispatch_request(app.current_request)

# Optional, for adding batch query support (used in Apollo-Client)
@app.route(
    '/graphql/batch',
    methods=['GET', 'POST'],
    content_types=['application/graphql', 'application/json', 'application/x-www-form-urlencoded']
)
def graphql_batch():
    gql_view = GraphQLView(schema=schema, batch=True)
    return gql_view.dispatch_request(app.current_request)
```

This will add `/graphql` endpoint to your app and enable the GraphiQL IDE.

### Supported options for GraphQLView

 * `schema`: The `GraphQLSchema` object that you want the view to execute when it gets a valid request.
 * `context`: A value to pass as the `context_value` to graphql `execute` function. By default is set to `dict` with request object at key `request`.
 * `root_value`: The `root_value` you want to provide to graphql `execute`.
 * `pretty`: Whether or not you want the response to be pretty printed JSON.
 * `graphiql`: If `True`, may present [GraphiQL](https://github.com/graphql/graphiql) when loaded directly from a browser (a useful tool for debugging and exploration).
 * `graphiql_version`: The graphiql version to load. Defaults to **"1.0.3"**.
 * `graphiql_template`: Inject a Jinja template string to customize GraphiQL.
 * `graphiql_html_title`: The graphiql title to display. Defaults to **"GraphiQL"**.
 * `batch`: Set the GraphQL view as batch (for using in [Apollo-Client](http://dev.apollodata.com/core/network.html#query-batching) or [ReactRelayNetworkLayer](https://github.com/nodkz/react-relay-network-layer))
 * `middleware`: A list of graphql [middlewares](http://docs.graphene-python.org/en/latest/execution/middleware/).
 * `encode`: the encoder to use for responses (sensibly defaults to `graphql_server.json_encode`).
 * `format_error`: the error formatter to use for responses (sensibly defaults to `graphql_server.default_format_error`.
 * `subscriptions`: The GraphiQL socket endpoint for using subscriptions in graphql-ws.
 * `headers`: An optional GraphQL string to use as the initial displayed request headers, if not provided, the stored headers will be used.
 * `default_query`: An optional GraphQL string to use when no query is provided and no stored query exists from a previous session. If not provided, GraphiQL will use its own default query.
* `header_editor_enabled`: An optional boolean which enables the header editor when true. Defaults to **false**.
* `should_persist_headers`:  An optional boolean which enables to persist headers to storage when true. Defaults to **false**.
