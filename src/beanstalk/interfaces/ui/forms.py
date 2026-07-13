"""Pydantic models for reviewer form submissions."""

from typing import Literal

from pydantic import BaseModel


class ReviewForm(BaseModel):
    verdict: Literal["approve", "decline"]
    note: str = ""

    @property
    def approves(self) -> bool:
        return self.verdict == "approve"
