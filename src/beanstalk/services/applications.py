"""ApplicationService: the submit -> score -> decide -> persist workflow."""

from dataclasses import replace
from decimal import Decimal

from beanstalk.domain.application import CafeProfile, EquipmentItem, FinancingApplication
from beanstalk.domain.decision import Decision, DecisionOutcome, Reason
from beanstalk.domain.decisioning import decide
from beanstalk.model.predict import RiskModel
from beanstalk.services.repository import DecisionRepository
from beanstalk.services.scoring import ModelRiskScorer, RiskScorer
from beanstalk.services.settings import Settings
from beanstalk.utils.ids import new_id


def build_application_service(settings: Settings | None = None) -> "ApplicationService":
    """Composition root: wire the production service graph from settings."""
    settings = settings if settings is not None else Settings()
    repository = DecisionRepository(settings.database_path)
    scorer = ModelRiskScorer(RiskModel.load(settings.artifact_path))
    return ApplicationService(repository, scorer, settings)


class ReviewNotPendingError(Exception):
    """A review resolution was attempted on an application not awaiting review."""


class ApplicationService:
    """Coordinates the financing workflow; dependencies are passed explicitly."""

    def __init__(
        self, repository: DecisionRepository, scorer: RiskScorer, settings: Settings
    ) -> None:
        self._repository = repository
        self._scorer = scorer
        self._settings = settings

    def submit(
        self,
        cafe: CafeProfile,
        equipment: EquipmentItem,
        *,
        term_months: int,
        down_payment: Decimal,
    ) -> Decision:
        """Decision a new financing application and persist the result."""
        application = FinancingApplication(
            application_id=new_id("app"),
            cafe=cafe,
            equipment=equipment,
            term_months=term_months,
            down_payment=down_payment,
            annual_rate=self._settings.annual_rate,
        )
        risk_score = self._scorer.score(application)
        decision = decide(
            application,
            risk_score=risk_score,
            approve_risk_below=self._settings.approve_risk_below,
            decline_risk_at=self._settings.decline_risk_at,
        )
        self._repository.save(application, decision)
        return decision

    def get(self, application_id: str) -> tuple[FinancingApplication, Decision]:
        return self._repository.get(application_id)

    def list_all(self) -> list[tuple[FinancingApplication, Decision]]:
        return self._repository.list_all()

    def review_queue(self) -> list[tuple[FinancingApplication, Decision]]:
        return self._repository.list_by_outcome(DecisionOutcome.NEEDS_REVIEW)

    def resolve_review(self, application_id: str, *, approve: bool, reviewer_note: str) -> Decision:
        """Apply a human reviewer's approve/decline call to a NEEDS_REVIEW decision."""
        application, decision = self._repository.get(application_id)
        if decision.outcome is not DecisionOutcome.NEEDS_REVIEW:
            raise ReviewNotPendingError(
                f"Application {application_id!r} is {decision.outcome.value}, not awaiting review."
            )
        resolved = replace(
            decision,
            outcome=DecisionOutcome.APPROVED if approve else DecisionOutcome.DECLINED,
            reasons=(*decision.reasons, Reason(code="manual_review", message=reviewer_note)),
        )
        self._repository.save(application, resolved)
        return resolved
