"""The machine_recommender feature's single entry point.

`load_recommender()` builds the recommender; the returned object satisfies the
coordination tier's `Recommender` protocol, handing back a core `EquipmentItem`.
The selection logic here is a deliberately simple stand-in for a real model.
"""

from beanstalk.core.application import CafeProfile, EquipmentItem
from beanstalk.features.machine_recommender.catalog import CATALOG, MachineOption


def load_recommender() -> "CatalogRecommender":
    """Build the catalog-backed recommender."""
    return CatalogRecommender()


class CatalogRecommender:
    """Suggests the largest catalog machine a cafe's seating can justify."""

    def recommend(self, cafe: CafeProfile) -> EquipmentItem:
        option = _best_fit(cafe.seats)
        return EquipmentItem(
            category=option.category,
            description=f"{option.model_name} — {option.blurb}",
            price=option.price,
        )


def _best_fit(seats: int) -> MachineOption:
    """The biggest machine whose seating floor the cafe clears."""
    eligible = [option for option in CATALOG if seats >= option.min_seats]
    return max(eligible, key=lambda option: option.min_seats) if eligible else CATALOG[0]
