"""The risk-scoring seam: what coordination needs from the risk_scorer feature.

The protocol is stated purely in Core terms; the feature's entrypoint conforms
structurally, so services never import the feature's internals — only its
`entrypoint.load_scorer` at the composition root.
"""

from typing import Protocol

from beanstalk.core.application import FinancingApplication


class RiskScorer(Protocol):
    """Anything that can put a default-risk number on an application."""

    def score(self, application: FinancingApplication) -> float: ...
