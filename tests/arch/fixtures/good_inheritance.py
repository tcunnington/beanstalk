"""Known-good fixture: every base here is sanctioned by the allow-list."""

from enum import StrEnum
from typing import Generic, NamedTuple, Protocol, TypeVar

from pydantic import BaseModel


class ParseError(Exception):
    pass


class NestedParseError(ParseError):  # allowed via the Error-suffix rule
    pass


class Species(StrEnum):
    COW = "cow"


class Payload(BaseModel):
    weight_kg: float


class Point(NamedTuple):
    x: int
    y: int


class Scorer(Protocol):
    def score(self) -> float: ...


ItemT = TypeVar("ItemT")


class Box(Generic[ItemT]):  # noqa: UP046 — the fixture proves a Generic *base* is allowed
    pass
