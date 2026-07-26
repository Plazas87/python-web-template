from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI
from prometheus_client import make_asgi_app

from {{ package_name }}.adapters.inbound.http import health, router
from {{ package_name }}.adapters.inbound.http.middleware.logging import LoggingMiddleware
from {{ package_name }}.adapters.inbound.http.middleware.metrics import MetricsMiddleware
from {{ package_name }}.adapters.inbound.http.middleware.tracing import TracingMiddleware
from {{ package_name }}.adapters.outbound.observability.logging import configure_logging
from {{ package_name }}.adapters.outbound.observability.tracing import configure_tracing
from {{ package_name }}.config import settings
from {{ package_name }}.container import Container


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure_logging(settings)
    app.state.container = Container.build(settings)
    configure_tracing(app, settings)
    yield


def create_app() -> FastAPI:
    if settings.sentry_dsn:
        sentry_sdk.init(dsn=settings.sentry_dsn, environment=settings.app_env)

    app = FastAPI(title="{{ project_name }}", lifespan=lifespan)

    # Outermost first: tracing must bind trace_id before logging/metrics run.
    app.add_middleware(MetricsMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(TracingMiddleware)

    app.include_router(health.router)
    app.include_router(router.router)
    app.mount("/metrics", make_asgi_app())

    return app


app = create_app()
