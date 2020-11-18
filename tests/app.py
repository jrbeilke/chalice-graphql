from chalice import Chalice

from chalice_graphql import GraphQLView
from tests.schema import Schema

app = Chalice(app_name='helloworld')

@app.route('/')
def index():
    return {'hello': 'world'}

@app.route(
    '/graphql',
    methods=['GET', 'POST', 'PUT'],
    content_types=['application/graphql', 'application/json', 'application/x-www-form-urlencoded', 'text/plain']
)
def graphql():
    gql_view = GraphQLView(schema=Schema, graphiql=True)
    return gql_view.dispatch_request(app.current_request)

@app.route(
    '/graphql/batch',
    methods=['GET', 'POST'],
    content_types=['application/graphql', 'application/json', 'application/x-www-form-urlencoded', 'text/plain']
)
def graphql_batch():
    gql_view = GraphQLView(schema=Schema, batch=True)
    return gql_view.dispatch_request(app.current_request)
