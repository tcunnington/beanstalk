"""A generic SQLite adapter: table-shaped operations, not raw SQL scattered around.

Knows nothing about the business — no "decisions", no "applications". Anything
above this file that wants to persist rows calls these functions with a table
and column names; the schema, serialization, and business meaning live one
level up (see services/decision_records.py). This is what "an adapter" means
at tier 4: a wrapper any project could reuse verbatim for a different table.
"""

import sqlite3
from pathlib import Path
from typing import Any


class SqliteAdapter:
    """Owns one sqlite3 connection; exposes CRUD as generic table operations.

    Table and column names are interpolated into SQL directly — safe here only
    because callers always pass literal strings from their own source, never
    user input. Values always go through parameterized placeholders.
    """

    def __init__(self, database_path: Path | str) -> None:
        self._connection = sqlite3.connect(database_path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row

    def ensure_schema(self, create_table_sql: str) -> None:
        """Run a `CREATE TABLE IF NOT EXISTS` statement and commit."""
        self._connection.execute(create_table_sql)
        self._connection.commit()

    def upsert(self, table: str, values: dict[str, Any]) -> None:
        """INSERT OR REPLACE a row; `values` keys become the row's columns."""
        columns = ", ".join(values)
        placeholders = ", ".join("?" for _ in values)
        self._connection.execute(
            f"INSERT OR REPLACE INTO {table} ({columns}) VALUES ({placeholders})",
            tuple(values.values()),
        )
        self._connection.commit()

    def find_one(self, table: str, *, column: str, value: Any) -> sqlite3.Row | None:
        """The first row where `column` equals `value`, or None."""
        return self._connection.execute(
            f"SELECT * FROM {table} WHERE {column} = ?", (value,)
        ).fetchone()

    def find_all(self, table: str, *, order_by: str | None = None) -> list[sqlite3.Row]:
        """Every row in `table`, optionally ordered."""
        query = f"SELECT * FROM {table}"
        if order_by:
            query += f" ORDER BY {order_by}"
        return self._connection.execute(query).fetchall()

    def find_where(
        self, table: str, *, column: str, value: Any, order_by: str | None = None
    ) -> list[sqlite3.Row]:
        """Every row where `column` equals `value`, optionally ordered."""
        query = f"SELECT * FROM {table} WHERE {column} = ?"
        if order_by:
            query += f" ORDER BY {order_by}"
        return self._connection.execute(query, (value,)).fetchall()

    def delete(self, table: str, *, column: str, value: Any) -> int:
        """Delete rows where `column` equals `value`; returns the number removed."""
        cursor = self._connection.execute(f"DELETE FROM {table} WHERE {column} = ?", (value,))
        self._connection.commit()
        return cursor.rowcount

    def close(self) -> None:
        self._connection.close()
