from __future__ import annotations

import sqlite3
from datetime import date, timedelta
from pathlib import Path

from app.core.config import settings


ANCHOR_DATE = date(2026, 8, 24)
BASE_AUDIENCE_SIZE = 12_684
RECENTLY_CONTACTED_SIZE = 1_812
FINAL_AUDIENCE_SIZE = 10_872
TOTAL_USERS = 14_000


def connect() -> sqlite3.Connection:
    connection = sqlite3.connect(settings.DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialise_database(force: bool = False) -> Path:
    path = settings.DATABASE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not force:
        return path
    if path.exists():
        path.unlink()

    with sqlite3.connect(path) as connection:
        connection.executescript(
            """
            CREATE TABLE users (
                user_id TEXT PRIMARY KEY,
                vip_level INTEGER NOT NULL,
                lifecycle_status TEXT NOT NULL,
                churn_score REAL NOT NULL,
                region TEXT NOT NULL,
                marketing_consent INTEGER NOT NULL
            );
            CREATE TABLE orders (
                order_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                paid_at TEXT NOT NULL,
                paid_amount REAL NOT NULL,
                order_status TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );
            CREATE TABLE campaign_touch_logs (
                touch_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                channel TEXT NOT NULL,
                variant_id TEXT,
                sent_at TEXT NOT NULL,
                opened INTEGER NOT NULL DEFAULT 0,
                clicked INTEGER NOT NULL DEFAULT 0,
                converted INTEGER NOT NULL DEFAULT 0,
                unsubscribe INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );
            """
        )
        user_rows: list[tuple] = []
        order_rows: list[tuple] = []
        touch_rows: list[tuple] = []
        for index in range(1, TOTAL_USERS + 1):
            user_id = f"U{index:06d}"
            eligible = index <= BASE_AUDIENCE_SIZE
            user_rows.append((
                user_id,
                5 + (index % 3) if eligible else 2 + (index % 3),
                "churn_warning" if eligible else "active",
                0.72 + (index % 20) / 100 if eligible else 0.25,
                ["SH_011", "BJ_003", "GZ_008"][index % 3],
                1 if eligible else int(index % 4 != 0),
            ))
            paid_at = ANCHOR_DATE - timedelta(days=60 + index % 90 if eligible else index % 20)
            amount = 680 + index % 650 if eligible else 120 + index % 250
            order_rows.append((f"O{index:07d}", user_id, paid_at.isoformat(), amount, "paid"))
            if index <= RECENTLY_CONTACTED_SIZE:
                sent_at = ANCHOR_DATE - timedelta(days=index % 6)
                touch_rows.append((f"T{index:07d}", user_id, "wechat", "HIST", sent_at.isoformat(), 1, 0, 0, 0))

        connection.executemany("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)", user_rows)
        connection.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?)", order_rows)
        connection.executemany("INSERT INTO campaign_touch_logs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", touch_rows)
        connection.execute("CREATE INDEX idx_orders_user ON orders(user_id)")
        connection.execute("CREATE INDEX idx_touch_user_sent ON campaign_touch_logs(user_id, sent_at)")
        connection.commit()
    return path


def table_columns() -> dict[str, set[str]]:
    initialise_database()
    result: dict[str, set[str]] = {}
    with connect() as connection:
        for table in ("users", "orders", "campaign_touch_logs"):
            rows = connection.execute(f"PRAGMA table_info({table})").fetchall()
            result[table] = {row[1] for row in rows}
    return result

