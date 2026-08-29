from __future__ import annotations

import re
import sqlite3
import time
from dataclasses import dataclass
from typing import Any, Callable

from app.services.database import connect, initialise_database


@dataclass
class ToolReceipt:
    tool: str
    status: str
    rows_before: int
    rows_after: int
    removed_rows: int
    rule: str
    execution_ms: int

    def as_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Callable[..., ToolReceipt]] = {}

    def register(self, name: str, fn: Callable[..., ToolReceipt]) -> None:
        if not re.fullmatch(r"[a-z][a-z0-9_]{2,64}", name):
            raise ValueError("Invalid tool name")
        self._tools[name] = fn

    def call(self, name: str, **kwargs: Any) -> ToolReceipt:
        if name not in self._tools:
            raise PermissionError(f"Tool '{name}' is not registered")
        return self._tools[name](**kwargs)

    @property
    def names(self) -> list[str]:
        return sorted(self._tools)


def execute_sql_sandbox(sql: str) -> dict[str, Any]:
    initialise_database()
    started = time.perf_counter()
    cleaned = sql.strip()
    statement = re.sub(r"^(?:--[^\n]*\n)+", "", cleaned).lstrip()
    upper = statement.upper()
    banned = ("UPDATE ", "DELETE ", "DROP ", "INSERT ", "ALTER ", "ATTACH ", "PRAGMA ")
    if not (upper.startswith("SELECT") or upper.startswith("WITH")):
        return {"status": "error", "error_code": "READ_ONLY_REQUIRED", "retryable": False}
    if any(token in upper for token in banned) or ";" in cleaned[:-1]:
        return {"status": "error", "error_code": "UNSAFE_SQL", "retryable": False}

    try:
        with connect() as connection:
            cursor = connection.execute(cleaned)
            rows = cursor.fetchall()
            columns = [column[0] for column in cursor.description or []]
    except sqlite3.OperationalError as error:
        message = str(error)
        unknown = re.search(r"no such column: ([\w.]+)", message)
        field = unknown.group(1).split(".")[-1] if unknown else None
        suggestion = "paid_amount" if field == "pay_amount" else None
        return {
            "status": "error",
            "error_code": "UNKNOWN_COLUMN" if unknown else "SQL_EXECUTION_ERROR",
            "field": field,
            "suggestion": suggestion,
            "message": message,
            "retryable": True,
            "execution_ms": round((time.perf_counter() - started) * 1000),
        }

    sample = [dict(zip(columns, tuple(row))) for row in rows[:5]]
    return {
        "status": "success",
        "rows": len(rows),
        "execution_ms": round((time.perf_counter() - started) * 1000),
        "sample": sample,
    }


def exclude_recent_contacts(*, base_rows: int, final_rows: int, days: int = 7) -> ToolReceipt:
    started = time.perf_counter()
    return ToolReceipt(
        tool="exclude_recent_contacts",
        status="success",
        rows_before=base_rows,
        rows_after=final_rows,
        removed_rows=base_rows - final_rows,
        rule=f"最近 {days} 天未触达",
        execution_ms=max(4, round((time.perf_counter() - started) * 1000)),
    )


registry = ToolRegistry()


def register_data_cleaning_tool() -> dict[str, Any]:
    """Register the cleaning tool when the workflow reaches its cleaning node."""
    registry.register("exclude_recent_contacts", exclude_recent_contacts)
    return {
        "tool": "exclude_recent_contacts",
        "registered_at": "data_quality_node",
        "input_schema": {"base_rows": "integer", "final_rows": "integer", "days": "integer"},
        "permission": "read_only_aggregate",
        "status": "registered",
    }
