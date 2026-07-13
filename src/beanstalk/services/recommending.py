"""The recommendation seam: what coordination needs from the machine_recommender feature.

Like `RiskScorer`, this protocol speaks only Core types — the feature's
entrypoint returns a core `EquipmentItem`, so no feature internals leak up here.
"""

from typing import Protocol

from beanstalk.core.application import CafeProfile, EquipmentItem


class Recommender(Protocol):
    """Anything that can suggest an espresso machine for a cafe."""

    def recommend(self, cafe: CafeProfile) -> EquipmentItem: ...
