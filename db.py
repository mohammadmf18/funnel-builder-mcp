"""
db.py
طبقة قاعدة البيانات (SQLite) لنظام بناء الفنلات التسويقية.
كل الجداول والاتصالات تمر من هنا فقط.
"""

import sqlite3
import json
import os
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone

DB_PATH = os.environ.get("FUNNEL_DB_PATH", os.path.join(os.path.dirname(__file__), "funnels.db"))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS funnels (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                goal TEXT,
                status TEXT NOT NULL DEFAULT 'draft',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS pages (
                id TEXT PRIMARY KEY,
                funnel_id TEXT NOT NULL REFERENCES funnels(id) ON DELETE CASCADE,
                type TEXT NOT NULL,              -- landing | optin | sales | checkout | upsell | thankyou
                order_index INTEGER NOT NULL,
                slug TEXT NOT NULL,
                headline TEXT,
                content_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(funnel_id, slug)
            );

            CREATE TABLE IF NOT EXISTS email_sequences (
                id TEXT PRIMARY KEY,
                funnel_id TEXT NOT NULL REFERENCES funnels(id) ON DELETE CASCADE,
                list_name TEXT NOT NULL,
                emails_json TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                funnel_id TEXT NOT NULL REFERENCES funnels(id) ON DELETE CASCADE,
                page_id TEXT REFERENCES pages(id) ON DELETE SET NULL,
                event_type TEXT NOT NULL,        -- visit | optin | purchase | upsell_purchase
                value REAL DEFAULT 0,
                created_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_pages_funnel ON pages(funnel_id);
            CREATE INDEX IF NOT EXISTS idx_events_funnel ON events(funnel_id);
            """
        )


def row_to_dict(row: sqlite3.Row) -> dict:
    return {k: row[k] for k in row.keys()}
