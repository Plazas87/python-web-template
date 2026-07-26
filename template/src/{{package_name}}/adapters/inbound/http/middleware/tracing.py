import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from {{ package_name }}.adapters.outbound.observability.logging import trace_id_var


class TracingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        trace_id = request.headers.get("x-trace-id", str(uuid.uuid4()))
        token = trace_id_var.set(trace_id)
        try:
            response = await call_next(request)
            response.headers["x-trace-id"] = trace_id
            return response
        finally:
            trace_id_var.reset(token)
