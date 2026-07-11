"""App factory for the partner API.

Run with `just api` (uvicorn --factory). Tests pass a service with a stub
scorer instead of the production graph.
"""

from fastapi import FastAPI

from beanstalk.api.routes import create_router
from beanstalk.services.applications import ApplicationService, build_application_service


def create_app(service: ApplicationService | None = None) -> FastAPI:
    app = FastAPI(title="Beanstalk partner API")
    app.include_router(
        create_router(service if service is not None else build_application_service())
    )
    return app
