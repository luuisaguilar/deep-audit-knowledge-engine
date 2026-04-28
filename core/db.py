"""Central persistence layer for the Deep Audit Knowledge Engine.

Provides a unified SQLite database (`knowledge.db`) to record every ingestion
across all source types (YouTube, GitHub, Web, RSS, Chef).  This enables
deduplication, analytics, and historical queries without changing the existing
analyzer APIs.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "knowledge.db"

# ---------------------------------------------------------------------------
# Schema bootstrap
# ---------------------------------------------------------------------------

_SCHEMA = """
CREATE TABLE IF NOT EXISTS ingestions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source_type     TEXT    NOT NULL,
    source_url      TEXT    UNIQUE NOT NULL,
    title           TEXT,
    processed_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    model_used      TEXT    DEFAULT 'gemini-2.0-flash',
    tokens_estimated INTEGER,
    vault_path      TEXT,
    status          TEXT    DEFAULT 'success',
    error_message   TEXT,
    metadata_json   TEXT
);
"""


def _connect():
    """Return a new connection with row-factory enabled."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create the ingestions table if it doesn't exist yet."""
    conn = _connect()
    conn.executescript(_SCHEMA)
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Write operations
# ---------------------------------------------------------------------------

def record_ingestion(
    source_type: str,
    source_url: str,
    title: str | None = None,
    *,
    model_used: str = "gemini-2.0-flash",
    tokens_estimated: int | None = None,
    vault_path: str | None = None,
    status: str = "success",
    error_message: str | None = None,
    metadata: dict | None = None,
) -> int | None:
    """Insert a new ingestion record.  Returns the row id or None on conflict."""
    conn = _connect()
    try:
        cur = conn.execute(
            """
            INSERT INTO ingestions
                (source_type, source_url, title, model_used,
                 tokens_estimated, vault_path, status, error_message, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                source_type,
                source_url,
                title,
                model_used,
                tokens_estimated,
                vault_path,
                status,
                error_message,
                json.dumps(metadata) if metadata else None,
            ),
        )
        conn.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError:
        # URL already exists – caller should treat as duplicate
        return None
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Read operations
# ---------------------------------------------------------------------------

def has_been_processed(source_url: str) -> bool:
    """Return True if the URL was already successfully ingested."""
    conn = _connect()
    row = conn.execute(
        "SELECT id FROM ingestions WHERE source_url = ? AND status = 'success'",
        (source_url,),
    ).fetchone()
    conn.close()
    return row is not None


def get_ingestion_by_url(source_url: str) -> dict | None:
    """Return the full ingestion record for a URL, or None."""
    conn = _connect()
    row = conn.execute(
        "SELECT * FROM ingestions WHERE source_url = ?", (source_url,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def list_recent_ingestions(limit: int = 50) -> list[dict]:
    """Return the most recent ingestions, newest first."""
    conn = _connect()
    rows = conn.execute(
        "SELECT * FROM ingestions ORDER BY processed_at DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_ingestion_stats() -> dict:
    """Aggregate statistics for the analytics dashboard.

    Returns a dict with keys:
        total, success, failed,
        by_type   – list of (source_type, count),
        by_date   – list of (date_str, count),
        recent    – list of dicts (last 10)
    """
    conn = _connect()

    total = conn.execute("SELECT COUNT(*) FROM ingestions").fetchone()[0]
    success = conn.execute(
        "SELECT COUNT(*) FROM ingestions WHERE status = 'success'"
    ).fetchone()[0]
    failed = conn.execute(
        "SELECT COUNT(*) FROM ingestions WHERE status = 'failed'"
    ).fetchone()[0]

    by_type = conn.execute(
        "SELECT source_type, COUNT(*) as cnt FROM ingestions GROUP BY source_type ORDER BY cnt DESC"
    ).fetchall()

    by_date = conn.execute(
        """SELECT DATE(processed_at) as day, COUNT(*) as cnt
           FROM ingestions
           GROUP BY day ORDER BY day DESC LIMIT 30"""
    ).fetchall()

    recent = conn.execute(
        "SELECT * FROM ingestions ORDER BY processed_at DESC LIMIT 10"
    ).fetchall()

    conn.close()

    return {
        "total": total,
        "success": success,
        "failed": failed,
        "by_type": [(r[0], r[1]) for r in by_type],
        "by_date": [(r[0], r[1]) for r in by_date],
        "recent": [dict(r) for r in recent],
    }


# Auto-initialize on import (idempotent)
init_db()
