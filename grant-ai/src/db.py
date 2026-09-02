"""
Database layer for the grant tracker.
Uses SQLite for zero-setup local storage. Swap for Postgres later by
changing get_conn() if you want multi-user / cloud hosting.
"""
import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "grants.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS opportunities (
    id TEXT PRIMARY KEY,           -- source-specific unique id (e.g. grants.gov opp number)
    source TEXT NOT NULL,          -- 'grants.gov', 'manual', 'web'
    title TEXT NOT NULL,
    funder TEXT,
    description TEXT,
    eligibility TEXT,
    amount_floor REAL,
    amount_ceiling REAL,
    deadline TEXT,                 -- ISO date string, nullable
    url TEXT,
    funder_category TEXT,          -- 'federal', 'CDFI', 'foundation', 'council_district', 'corporate', etc.
    raw_json TEXT,                 -- full original record, for reference
    match_score INTEGER,           -- 0-100, set by scoring step
    match_notes TEXT,
    status TEXT DEFAULT 'new',     -- new | reviewing | drafting | submitted | rejected | awarded | skipped
    org_project TEXT,              -- which of your projects this applies to
    date_added TEXT DEFAULT (datetime('now')),
    date_updated TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS application_drafts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    opportunity_id TEXT NOT NULL,
    question TEXT NOT NULL,
    draft_answer TEXT,
    word_limit INTEGER,
    gaps_flagged TEXT,             -- info the profile was missing, if any
    date_created TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (opportunity_id) REFERENCES opportunities(id)
);
"""


def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()


def upsert_opportunity(opp: dict):
    """opp must contain at least: id, source, title. Everything else optional."""
    conn = get_conn()
    cols = [
        "id", "source", "title", "funder", "description", "eligibility",
        "amount_floor", "amount_ceiling", "deadline", "url", "funder_category",
        "raw_json", "match_score", "match_notes", "org_project",
    ]
    values = [opp.get(c) for c in cols]
    if isinstance(opp.get("raw_json"), (dict, list)):
        values[cols.index("raw_json")] = json.dumps(opp["raw_json"])

    placeholders = ",".join("?" * len(cols))
    update_clause = ",".join(f"{c}=excluded.{c}" for c in cols if c != "id")
    conn.execute(
        f"""INSERT INTO opportunities ({','.join(cols)}) VALUES ({placeholders})
            ON CONFLICT(id) DO UPDATE SET {update_clause}, date_updated=datetime('now')""",
        values,
    )
    conn.commit()
    conn.close()


def list_opportunities(status: str = None, order_by: str = "deadline"):
    conn = get_conn()
    if status:
        rows = conn.execute(
            f"SELECT * FROM opportunities WHERE status = ? ORDER BY {order_by} IS NULL, {order_by}",
            (status,),
        ).fetchall()
    else:
        rows = conn.execute(
            f"SELECT * FROM opportunities ORDER BY {order_by} IS NULL, {order_by}"
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_opportunity(opp_id: str):
    conn = get_conn()
    row = conn.execute("SELECT * FROM opportunities WHERE id = ?", (opp_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_status(opp_id: str, status: str):
    conn = get_conn()
    conn.execute(
        "UPDATE opportunities SET status = ?, date_updated = datetime('now') WHERE id = ?",
        (status, opp_id),
    )
    conn.commit()
    conn.close()


def save_draft(opportunity_id: str, question: str, draft_answer: str,
                word_limit: int = None, gaps_flagged: str = None):
    conn = get_conn()
    conn.execute(
        """INSERT INTO application_drafts
           (opportunity_id, question, draft_answer, word_limit, gaps_flagged)
           VALUES (?, ?, ?, ?, ?)""",
        (opportunity_id, question, draft_answer, word_limit, gaps_flagged),
    )
    conn.commit()
    conn.close()


def list_drafts(opportunity_id: str):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM application_drafts WHERE opportunity_id = ? ORDER BY date_created",
        (opportunity_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


if __name__ == "__main__":
    init_db()
    print(f"Initialized database at {DB_PATH}")
