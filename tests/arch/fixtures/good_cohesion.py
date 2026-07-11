"""Known-good fixture: cohesive classes the LCOM4 checker must accept."""


class Tab:
    """One component: every method touches self.entries."""

    def __init__(self) -> None:
        self.entries: list[float] = []

    def add(self, amount: float) -> None:
        self.entries.append(amount)

    def total(self) -> float:
        return sum(self.entries)

    def receipt(self) -> str:
        return f"{len(self.entries)} items: ${self.total():.2f}"


class MathHelpers:
    """No instance state at all: skipped, not flagged."""

    def double(self, x: float) -> float:
        return x * 2

    def halve(self, x: float) -> float:
        return x / 2
