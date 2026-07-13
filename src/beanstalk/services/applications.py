"""ApplicationService: the submit -> score -> decide -> persist workflow.

The coordination tier (tier 4): a thin broker that wires the risk_scorer and
machine_recommender features to the core decision policy and persistence. It
reaches each feature only through that feature's entrypoint.
"""

from dataclasses import replace
from decimal import Decimal

from beanstalk.core.application import CafeProfile, EquipmentItem, FinancingApplication
from beanstalk.core.decision import Decision, DecisionOutcome, Reason
from beanstalk.core.decisioning import decide
from beanstalk.features.machine_recommender.entrypoint import load_recommender
from beanstalk.features.risk_scorer.entrypoint import load_scorer
from beanstalk.services.decision_records import DecisionRecordStore
from beanstalk.services.recommending import Recommender
from beanstalk.services.scoring import RiskScorer
from beanstalk.services.settings import Settings
from beanstalk.utils.ids import new_id


def build_application_service(settings: Settings | None = None) -> "ApplicationService":
    """Composition root: wire the production service graph from settings."""
    settings = settings if settings is not None else Settings()
    records = DecisionRecordStore(settings.database_path)
    scorer = load_scorer(settings.artifact_path)
    recommender = load_recommender()
    return ApplicationService(
        records=records, scorer=scorer, recommender=recommender, settings=settings
    )


class ReviewNotPendingError(Exception):
    """A review resolution was attempted on an application not awaiting review."""


class ApplicationService:
    """Coordinates the financing workflow; dependencies are passed explicitly."""

    def __init__(
        self,
        *,
        records: DecisionRecordStore,
        scorer: RiskScorer,
        recommender: Recommender,
        settings: Settings,
    ) -> None:
        self._records = records
        self._scorer = scorer
        self._recommender = recommender
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
        self._records.save(application, decision)
        return decision

    def recommend_machine(self, application_id: str) -> EquipmentItem:
        """Suggest an espresso machine for a stored applicant's cafe.

        Coordinates two features' worth of state — the persisted application and
        the machine_recommender — which is exactly the tier-4 broker's job.
        """
        application, _decision = self._records.get(application_id)
        return self._recommender.recommend(application.cafe)

    def get(self, application_id: str) -> tuple[FinancingApplication, Decision]:
        return self._records.get(application_id)

    def list_all(self) -> list[tuple[FinancingApplication, Decision]]:
        return self._records.list_all()

    def review_queue(self) -> list[tuple[FinancingApplication, Decision]]:
        return self._records.list_by_outcome(DecisionOutcome.NEEDS_REVIEW)

    def resolve_review(self, application_id: str, *, approve: bool, reviewer_note: str) -> Decision:
        """Apply a human reviewer's approve/decline call to a NEEDS_REVIEW decision."""
        application, decision = self._records.get(application_id)
        if decision.outcome is not DecisionOutcome.NEEDS_REVIEW:
            raise ReviewNotPendingError(
                f"Application {application_id!r} is {decision.outcome.value}, not awaiting review."
            )
        resolved = replace(
            decision,
            outcome=DecisionOutcome.APPROVED if approve else DecisionOutcome.DECLINED,
            reasons=(*decision.reasons, Reason(code="manual_review", message=reviewer_note)),
        )
        self._records.save(application, resolved)
        return resolved
