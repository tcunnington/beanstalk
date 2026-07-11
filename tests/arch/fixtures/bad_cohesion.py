"""Known-bad fixture: a class that is really two classes glued together."""


class KitchenSink:
    def __init__(self) -> None:
        self.flour_kg = 1.0
        self.invoices: list[str] = []

    # component 1: baking
    def knead(self) -> float:
        return self.flour_kg * 2

    def bake(self) -> float:
        return self.flour_kg + 1

    # component 2: billing — shares nothing with baking
    def bill(self) -> int:
        return len(self.invoices)

    def remind(self) -> str:
        return f"{len(self.invoices)} invoices due"
