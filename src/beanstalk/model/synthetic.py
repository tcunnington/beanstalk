"""Synthetic training data: plausible cafes with default labels.

Labels come from a hidden linear rule plus noise, so a linear model can
recover real signal — enough for an honest AUC sanity check.
"""

import numpy as np

EXISTING_FINANCING_SHARE = 0.30


def generate_training_data(
    n_samples: int = 2000, *, seed: int = 7
) -> tuple[np.ndarray, np.ndarray]:
    """Return (features, default_labels) with columns in FEATURE_COLUMNS order."""
    rng = np.random.default_rng(seed)

    months_in_business = rng.integers(3, 240, n_samples)
    monthly_revenue = rng.lognormal(mean=10.3, sigma=0.5, size=n_samples)
    seats = rng.integers(6, 80, n_samples)
    has_existing_financing = rng.random(n_samples) < EXISTING_FINANCING_SHARE
    financed_amount = rng.uniform(3_000, 40_000, n_samples)
    # Rough 36-month payment ratio; mirrors the payment_to_revenue feature.
    payment_to_revenue = financed_amount * 0.033 / monthly_revenue

    default_probability = _sigmoid(
        -1.2
        - 0.008 * months_in_business
        + 15.0 * payment_to_revenue
        + 0.8 * has_existing_financing
        - 0.00001 * (monthly_revenue - 30_000)
    )
    default_labels = (rng.random(n_samples) < default_probability).astype(int)

    features = np.column_stack(
        [
            months_in_business,
            monthly_revenue,
            seats,
            has_existing_financing,
            financed_amount,
            payment_to_revenue,
        ]
    )
    return features, default_labels


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))
