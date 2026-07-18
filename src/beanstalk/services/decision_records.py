"""Persists financing applications together with their decisions.

Owns the schema and the (de)serialization of core objects via pydantic
TypeAdapters (so core itself stays pydantic-free). The generic SQL mechanics
come from adapters/sqlite.py, kept deliberately business-agnostic.
"""

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from pydantic import TypeAdapter

from beanstalk.core.application import FinancingApplication
from beanstalk.core.decision import Decision, DecisionOutcome
from beanstalk.services.adapters.sqlite import SqliteAdapter

_APPLICATION_ADAPTER = TypeAdapter(FinancingApplication)
_DECISION_ADAPTER = TypeAdapter(Decision)

_TABLE = "decisions"
_SCHEMA = """
CREATE TABLE IF NOT EXISTS decisions (
    application_id TEXT PRIMARY KEY,
    outcome TEXT NOT NULL,
    application_json TEXT NOT NULL,
    decision_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
)
"""


class ApplicationNotFoundError(Exception):
    """No stored application matches the requested id."""


class DecisionRecordStore:
    """Persists (FinancingApplication, Decision) pairs, keyed by application_id."""

    def __init__(self, database_path: Path | str) -> None:
        self._sqlite = SqliteAdapter(database_path)
        self._sqlite.ensure_schema(_SCHEMA)

    def save(self, application: FinancingApplication, decision: Decision) -> None:
        """Insert or replace the stored decision for this application."""
        self._sqlite.upsert(
            _TABLE,
            {
                "application_id": application.application_id,
                "outcome": decision.outcome.value,
                "application_json": _APPLICATION_ADAPTER.dump_json(application).decode(),
                "decision_json": _DECISION_ADAPTER.dump_json(decision).decode(),
            },
        )

    def get(self, application_id: str) -> tuple[FinancingApplication, Decision]:
        row = self._sqlite.find_one(_TABLE, column="application_id", value=application_id)
        if row is None:
            raise ApplicationNotFoundError(f"No application with id {application_id!r}")
        return _from_row(row)

    def list_all(self) -> list[tuple[FinancingApplication, Decision]]:
        rows = self._sqlite.find_all(_TABLE, order_by="created_at DESC, application_id")
        return [_from_row(row) for row in rows]

    def list_by_outcome(
        self, outcome: DecisionOutcome
    ) -> list[tuple[FinancingApplication, Decision]]:
        rows = self._sqlite.find_where(
            _TABLE,
            column="outcome",
            value=outcome.value,
            order_by="created_at DESC, application_id",
        )
        return [_from_row(row) for row in rows]

    def delete(self, application_id: str) -> None:
        """Remove a stored application. Not reachable from any interface by design."""
        deleted = self._sqlite.delete(_TABLE, column="application_id", value=application_id)
        if deleted == 0:
            raise ApplicationNotFoundError(f"No application with id {application_id!r}")

    def close(self) -> None:
        self._sqlite.close()


def _from_row(row: Mapping[str, Any]) -> tuple[FinancingApplication, Decision]:
    application = _APPLICATION_ADAPTER.validate_json(row["application_json"])
    decision = _DECISION_ADAPTER.validate_json(row["decision_json"])
    return application, decision
