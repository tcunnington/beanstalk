"""Combine hard rules, affordability, and the risk score into a Decision."""

from beanstalk.domain.affordability import affordability_failure, monthly_payment_for
from beanstalk.domain.application import FinancingApplication
from beanstalk.domain.decision import Decision, DecisionOutcome, Reason
from beanstalk.domain.eligibility import eligibility_failures

DEFAULT_APPROVE_RISK_BELOW = 0.25
DEFAULT_DECLINE_RISK_AT = 0.60


def decide(
    application: FinancingApplication,
    *,
    risk_score: float,
    approve_risk_below: float = DEFAULT_APPROVE_RISK_BELOW,
    decline_risk_at: float = DEFAULT_DECLINE_RISK_AT,
) -> Decision:
    """Decision policy: hard-rule failures decline outright; otherwise the
    risk score approves below the low band, declines at the high band, and
    routes the middle band to human review.
    """
    rule_failures = eligibility_failures(application)
    if (affordability := affordability_failure(application)) is not None:
        rule_failures += (affordability,)

    outcome, reasons = _outcome_from_risk(
        rule_failures,
        risk_score,
        approve_risk_below=approve_risk_below,
        decline_risk_at=decline_risk_at,
    )
    return Decision(
        application_id=application.application_id,
        outcome=outcome,
        reasons=reasons,
        risk_score=risk_score,
        monthly_payment=monthly_payment_for(application),
    )


def _outcome_from_risk(
    rule_failures: tuple[Reason, ...],
    risk_score: float,
    *,
    approve_risk_below: float,
    decline_risk_at: float,
) -> tuple[DecisionOutcome, tuple[Reason, ...]]:
    if rule_failures:
        return DecisionOutcome.DECLINED, rule_failures
    if risk_score >= decline_risk_at:
        reason = Reason(
            code="high_risk",
            message=f"Predicted default risk {risk_score:.0%} is at or above the decline band.",
        )
        return DecisionOutcome.DECLINED, (reason,)
    if risk_score < approve_risk_below:
        return DecisionOutcome.APPROVED, ()
    reason = Reason(
        code="borderline_risk",
        message=f"Predicted default risk {risk_score:.0%} needs a human look.",
    )
    return DecisionOutcome.NEEDS_REVIEW, (reason,)
