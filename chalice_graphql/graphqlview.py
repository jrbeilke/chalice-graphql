import copy
from collections.abc import MutableMapping
from functools import partial
from typing import List
from urllib.parse import parse_qsl

from chalice import Response
from graphql.error import GraphQLError
from graphql.type.schema import GraphQLSchema

from graphql_server import (
    GraphQLParams,
    HttpQueryError,
    encode_execution_results,
    format_error_default,
    json_encode,
    load_json_body,
    run_http_query,
)
from graphql_server.render_graphiql import (
    GraphiQLConfig,
    GraphiQLData,
    GraphiQLOptions,
    render_graphiql_sync,
)


class GraphQLView:
    schema = None
    root_value = None
    context = None
    pretty = False
    graphiql = False
    graphiql_version = None
    graphiql_template = None
    graphiql_html_title = None
    middleware = None
    batch = False
    subscriptions = None
    headers = None
    default_query = None
    header_editor_enabled = None
    should_persist_headers = None

    methods = ["GET", "POST", "PUT", "DELETE"]

    format_error = staticmethod(format_error_default)
    encode = staticmethod(json_encode)

    def __init__(self, **kwargs):
        super(GraphQLView, self).__init__()
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

        assert isinstance(
            self.schema, GraphQLSchema
        ), "A Schema is required to be provided to GraphQLView."

    def get_root_value(self):
        return self.root_value

    def get_context(self, request):
        context = (
            copy.copy(self.context)
            if self.context and isinstance(self.context, MutableMapping)
            else {}
        )
        if isinstance(context, MutableMapping) and "request" not in context:
            context.update({"request": request})
        return context

    def get_middleware(self):
        return self.middleware

    def dispatch_request(self, request):
        try:
            request_method = request.method.lower()
            data = self.parse_body(request)
            is_graphiql = self.is_graphiql(request)
            is_pretty = self.is_pretty(request)

            all_params: List[GraphQLParams]
            execution_results, all_params = run_http_query(
                self.schema,
                request_method,
                data,
                query_data=request.query_params,
                batch_enabled=self.batch,
                catch=is_graphiql,
                # Execute options
                root_value=self.get_root_value(),
                context_value=self.get_context(request),
                middleware=self.get_middleware(),
            )
            result, status_code = encode_execution_results(
                execution_results,
                is_batch=isinstance(data, list),
                format_error=self.format_error,
                encode=partial(self.encode, pretty=is_pretty),  # noqa
            )

            if is_graphiql:
                graphiql_data = GraphiQLData(
                    result=result,
                    query=getattr(all_params[0], "query"),
                    variables=getattr(all_params[0], "variables"),
                    operation_name=getattr(all_params[0], "operation_name"),
                    subscription_url=self.subscriptions,
                    headers=self.headers,
                )
                graphiql_config = GraphiQLConfig(
                    graphiql_version=self.graphiql_version,
                    graphiql_template=self.graphiql_template,
                    graphiql_html_title=self.graphiql_html_title,
                    jinja_env=None,
                )
                graphiql_options = GraphiQLOptions(
                    default_query=self.default_query,
                    header_editor_enabled=self.header_editor_enabled,
                    should_persist_headers=self.should_persist_headers,
                )
                source = render_graphiql_sync(
                    data=graphiql_data, config=graphiql_config, options=graphiql_options
                )
                return Response(source, headers={'Content-Type': 'text/html'})

            return Response(result, status_code=status_code, headers={'Content-Type': 'application/json'})

        except HttpQueryError as e:
            parsed_error = GraphQLError(e.message)
            headers = {}
            if e.headers is not None:
                headers.update(e.headers)
            return Response(
                self.encode(dict(errors=[self.format_error(parsed_error)])),
                status_code=e.status_code,
                headers=headers.update({'Content-Type': 'application/json'}),
            )

    @staticmethod
    def parse_body(request):
        content_type = request.headers.get('content-type', '')
        if "application/graphql" in content_type:
            return {"query": request.raw_body.decode("utf8")}

        elif "application/json" in content_type:
            return load_json_body(request.raw_body.decode("utf8"))

        elif "application/x-www-form-urlencoded" in content_type:
            return dict(parse_qsl(request.raw_body.decode("utf8")))

        # TODO: Chalice lacks support for multipart requests
        # https://github.com/aws/chalice/issues/796
#        elif content_type == "multipart/form-data":
#            return request.json_body

        return {}

    def is_graphiql(self, request):
        return all(
            [
                self.graphiql,
                request.method.lower() == "get",
                request.query_params is None or request.query_params.get('raw') is None,
                any(
                    [
                        "text/html" in request.headers.get("accept", {}),
                        "*/*" in request.headers.get("accept", {}),
                    ]
                ),
            ]
        )

    def is_pretty(self, request):
        return any(
            [
              self.pretty,
              self.is_graphiql(request),
              request.query_params is not None and request.query_params.get("pretty")
            ]
        )
