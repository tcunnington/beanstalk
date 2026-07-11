"""SQLite persistence for applications and their decisions.

Domain objects are serialized with pydantic TypeAdapters (which understand
dataclasses, Decimal, and enums) so the domain layer itself stays
pydantic-free.
"""

import sqlite3
from pathlib import Path

from pydantic import TypeAdapter

from beanstalk.domain.application import FinancingApplication
from beanstalk.domain.decision import Decision, DecisionOutcome

_APPLICATION_ADAPTER = TypeAdapter(FinancingApplication)
_DECISION_ADAPTER = TypeAdapter(Decision)

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


class DecisionRepository:
    """Owns the sqlite connection; stores each application with its decision."""

    def __init__(self, database_path: Path | str) -> None:
        self._connection = sqlite3.connect(database_path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute(_SCHEMA)
        self._connection.commit()

    def save(self, application: FinancingApplication, decision: Decision) -> None:
        """Insert or replace the stored decision for this application."""
        self._connection.execute(
            "INSERT OR REPLACE INTO decisions"
            " (application_id, outcome, application_json, decision_json)"
            " VALUES (?, ?, ?, ?)",
            (
                application.application_id,
                decision.outcome.value,
                _APPLICATION_ADAPTER.dump_json(application).decode(),
                _DECISION_ADAPTER.dump_json(decision).decode(),
            ),
        )
        self._connection.commit()

    def get(self, application_id: str) -> tuple[FinancingApplication, Decision]:
        row = self._connection.execute(
            "SELECT * FROM decisions WHERE application_id = ?", (application_id,)
        ).fetchone()
        if row is None:
            raise ApplicationNotFoundError(f"No application with id {application_id!r}")
        return _from_row(row)

    def list_all(self) -> list[tuple[FinancingApplication, Decision]]:
        rows = self._connection.execute(
            "SELECT * FROM decisions ORDER BY created_at DESC, application_id"
        ).fetchall()
        return [_from_row(row) for row in rows]

    def list_by_outcome(
        self, outcome: DecisionOutcome
    ) -> list[tuple[FinancingApplication, Decision]]:
        rows = self._connection.execute(
            "SELECT * FROM decisions WHERE outcome = ? ORDER BY created_at DESC, application_id",
            (outcome.value,),
        ).fetchall()
        return [_from_row(row) for row in rows]

    def close(self) -> None:
        self._connection.close()


def _from_row(row: sqlite3.Row) -> tuple[FinancingApplication, Decision]:
    application = _APPLICATION_ADAPTER.validate_json(row["application_json"])
    decision = _DECISION_ADAPTER.validate_json(row["decision_json"])
    return application, decision
