"""Reviewer UI routes: the NEEDS_REVIEW queue and approve/decline actions."""

from typing import Annotated

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from beanstalk.interfaces.ui.forms import ReviewForm
from beanstalk.services.applications import ApplicationService, ReviewNotPendingError
from beanstalk.services.repository import ApplicationNotFoundError


def create_router(service: ApplicationService, templates: Jinja2Templates) -> APIRouter:
    router = APIRouter()

    @router.get("/", response_class=HTMLResponse)
    def review_queue(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            request,
            "queue.html",
            {"queue": service.review_queue(), "all_decisions": service.list_all()},
        )

    @router.get("/applications/{application_id}", response_class=HTMLResponse)
    def application_detail(request: Request, application_id: str) -> HTMLResponse:
        try:
            application, decision = service.get(application_id)
        except ApplicationNotFoundError as err:
            raise HTTPException(status_code=404, detail=str(err)) from err
        return templates.TemplateResponse(
            request,
            "detail.html",
            {"application": application, "decision": decision},
        )

    @router.post("/applications/{application_id}/review")
    def resolve_review(
        application_id: str,
        verdict: Annotated[str, Form()],
        note: Annotated[str, Form()] = "",
    ) -> RedirectResponse:
        try:
            form = ReviewForm.model_validate({"verdict": verdict, "note": note})
        except ValidationError as err:
            raise HTTPException(status_code=422, detail=str(err)) from err
        try:
            service.resolve_review(
                application_id,
                approve=form.approves,
                reviewer_note=form.note or f"Manually {form.verdict}d by reviewer.",
            )
        except ApplicationNotFoundError as err:
            raise HTTPException(status_code=404, detail=str(err)) from err
        except ReviewNotPendingError as err:
            raise HTTPException(status_code=409, detail=str(err)) from err
        return RedirectResponse(url="/", status_code=303)

    return router
