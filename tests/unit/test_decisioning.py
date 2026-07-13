from decimal import Decimal

from beanstalk.core.decision import DecisionOutcome
from beanstalk.core.decisioning import decide
from tests.unit.builders import healthy_application, healthy_cafe


def test_low_risk_healthy_application_is_approved():
    decision = decide(healthy_application(), risk_score=0.10)
    assert decision.outcome == DecisionOutcome.APPROVED
    assert decision.reasons == ()
    assert decision.monthly_payment == Decimal("318.86")


def test_borderline_risk_goes_to_human_review():
    decision = decide(healthy_application(), risk_score=0.40)
    assert decision.outcome == DecisionOutcome.NEEDS_REVIEW
    assert [reason.code for reason in decision.reasons] == ["borderline_risk"]


def test_high_risk_is_declined():
    decision = decide(healthy_application(), risk_score=0.75)
    assert decision.outcome == DecisionOutcome.DECLINED
    assert [reason.code for reason in decision.reasons] == ["high_risk"]


def test_hard_rule_failure_declines_even_at_low_risk():
    application = healthy_application(cafe=healthy_cafe(months_in_business=2))
    decision = decide(application, risk_score=0.05)
    assert decision.outcome == DecisionOutcome.DECLINED
    assert [reason.code for reason in decision.reasons] == ["too_new"]


def test_custom_risk_bands_are_respected():
    decision = decide(healthy_application(), risk_score=0.40, approve_risk_below=0.50)
    assert decision.outcome == DecisionOutcome.APPROVED
