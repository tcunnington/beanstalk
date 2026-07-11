"""App factory for the reviewer UI.

Run with `just ui` (uvicorn --factory). Same explicit-composition style as
the API: the service graph is built once and handed to the router.
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.templating import Jinja2Templates

from beanstalk.services.applications import ApplicationService, build_application_service
from beanstalk.ui.routes import create_router

_TEMPLATES_DIR = Path(__file__).parent / "templates"


def create_app(service: ApplicationService | None = None) -> FastAPI:
    app = FastAPI(title="Beanstalk review queue")
    templates = Jinja2Templates(directory=_TEMPLATES_DIR)
    app.include_router(
        create_router(service if service is not None else build_application_service(), templates)
    )
    return app
