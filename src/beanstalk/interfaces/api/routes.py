"""API routes. Built as a factory so the service graph is composed explicitly."""

from fastapi import APIRouter, HTTPException

from beanstalk.interfaces.api.schemas import ApplicationDetail, ApplicationRequest, DecisionResponse
from beanstalk.services.applications import ApplicationService
from beanstalk.services.decision_records import ApplicationNotFoundError


def create_router(service: ApplicationService) -> APIRouter:
    router = APIRouter()

    @router.post("/applications", status_code=201)
    def submit_application(request: ApplicationRequest) -> DecisionResponse:
        decision = service.submit(
            request.cafe.to_domain(),
            request.equipment.to_domain(),
            term_months=request.term_months,
            down_payment=request.down_payment,
        )
        return DecisionResponse.from_domain(decision)

    @router.get("/applications")
    def list_applications() -> list[ApplicationDetail]:
        return [
            ApplicationDetail.from_domain(application, decision)
            for application, decision in service.list_all()
        ]

    @router.get("/applications/{application_id}")
    def get_application(application_id: str) -> ApplicationDetail:
        try:
            application, decision = service.get(application_id)
        except ApplicationNotFoundError as err:
            raise HTTPException(status_code=404, detail=str(err)) from err
        return ApplicationDetail.from_domain(application, decision)

    return router
