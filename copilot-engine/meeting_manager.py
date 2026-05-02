"""
Meeting Manager — SQLite-backed meetings, action items, and follow-up tracking.
Stores meeting records, associated action items, and follow-ups.
Thread-safe with module-level lock (same pattern as system_monitor.py).
"""
import json
import time
import logging
import uuid
import sqlite3
from typing import Any, Dict, List, Optional
from pathlib import Path
from datetime import datetime, timezone
from threading import Lock

logger = logging.getLogger(__name__)

_DB_PATH: Optional[Path] = None
_conn: Optional[sqlite3.Connection] = None
_lock = Lock()


def _get_conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(str(_DB_PATH), check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA journal_mode=WAL")
        _conn.execute("PRAGMA foreign_keys=ON")
        _init_tables(_conn)
    return _conn


def init(db_dir: str = "."):
    global _DB_PATH
    _DB_PATH = Path(db_dir) / "meetings.db"
    _get_conn()
    logger.info(f"Meeting manager initialized: {_DB_PATH}")


def _init_tables(conn: sqlite3.Connection):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS meetings (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            date TEXT NOT NULL,
            attendees TEXT DEFAULT '[]',
            category TEXT DEFAULT 'general',
            notes TEXT DEFAULT '',
            status TEXT DEFAULT 'upcoming',
            summary TEXT DEFAULT '',
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS action_items (
            id TEXT PRIMARY KEY,
            meeting_id TEXT NOT NULL,
            text TEXT NOT NULL,
            assignee TEXT DEFAULT '',
            due_date TEXT DEFAULT '',
            completed INTEGER DEFAULT 0,
            completed_at TEXT DEFAULT '',
            priority TEXT DEFAULT 'medium',
            created_at TEXT NOT NULL,
            FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS follow_ups (
            id TEXT PRIMARY KEY,
            meeting_id TEXT NOT NULL,
            text TEXT NOT NULL,
            due_date TEXT DEFAULT '',
            completed INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_actions_meeting ON action_items(meeting_id);
        CREATE INDEX IF NOT EXISTS idx_actions_completed ON action_items(completed);
        CREATE INDEX IF NOT EXISTS idx_followups_meeting ON follow_ups(meeting_id);
        CREATE INDEX IF NOT EXISTS idx_followups_completed ON follow_ups(completed);
        CREATE INDEX IF NOT EXISTS idx_meetings_date ON meetings(date DESC);
        CREATE INDEX IF NOT EXISTS idx_meetings_status ON meetings(status);
    """)
    conn.commit()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row_to_dict(row) -> Dict[str, Any]:
    if row is None:
        return {}
    d = dict(row)
    # Parse attendees JSON
    if "attendees" in d and isinstance(d["attendees"], str):
        try:
            d["attendees"] = json.loads(d["attendees"])
        except (json.JSONDecodeError, TypeError):
            d["attendees"] = []
    return d


# ═══════════════ Meeting CRUD ═══════════════

def create_meeting(
    title: str,
    date: str,
    attendees: Optional[List[str]] = None,
    category: str = "general",
    notes: str = "",
    status: str = "upcoming",
) -> Dict[str, Any]:
    meeting_id = str(uuid.uuid4())[:8]
    now = _now()
    attendees_json = json.dumps(attendees or [])
    with _lock:
        conn = _get_conn()
        conn.execute(
            """INSERT INTO meetings (id, title, date, attendees, category, notes, status, summary, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, '', ?)""",
            (meeting_id, title, date, attendees_json, category, notes, status, now),
        )
        conn.commit()
    return get_meeting(meeting_id)


def list_meetings(
    filter_type: Optional[str] = None,
    category: Optional[str] = None,
) -> List[Dict[str, Any]]:
    with _lock:
        conn = _get_conn()
        query = "SELECT * FROM meetings"
        conditions: List[str] = []
        params: List[Any] = []

        if filter_type == "upcoming":
            conditions.append("status = 'upcoming'")
        elif filter_type == "completed":
            conditions.append("status = 'completed'")

        if category:
            conditions.append("category = ?")
            params.append(category)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY date DESC"

        rows = conn.execute(query, params).fetchall()
        meetings = []
        for row in rows:
            m = _row_to_dict(row)
            # Count action items
            ai_count = conn.execute(
                "SELECT COUNT(*) as total, SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END) as done FROM action_items WHERE meeting_id = ?",
                (m["id"],),
            ).fetchone()
            m["action_item_count"] = ai_count["total"] if ai_count else 0
            m["action_items_done"] = ai_count["done"] or 0 if ai_count else 0
            # Count follow-ups
            fu_count = conn.execute(
                "SELECT COUNT(*) as c FROM follow_ups WHERE meeting_id = ? AND completed = 0",
                (m["id"],),
            ).fetchone()
            m["pending_follow_ups"] = fu_count["c"] if fu_count else 0
            meetings.append(m)
    return meetings


def get_meeting(meeting_id: str) -> Dict[str, Any]:
    with _lock:
        conn = _get_conn()
        row = conn.execute("SELECT * FROM meetings WHERE id = ?", (meeting_id,)).fetchone()
        if not row:
            return {}
        m = _row_to_dict(row)
        # Load action items
        ai_rows = conn.execute(
            "SELECT * FROM action_items WHERE meeting_id = ? ORDER BY created_at",
            (meeting_id,),
        ).fetchall()
        m["action_items"] = [dict(r) for r in ai_rows]
        # Load follow-ups
        fu_rows = conn.execute(
            "SELECT * FROM follow_ups WHERE meeting_id = ? ORDER BY created_at",
            (meeting_id,),
        ).fetchall()
        m["follow_ups"] = [dict(r) for r in fu_rows]
    return m


def update_meeting(meeting_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    allowed = {"title", "date", "attendees", "category", "notes", "status", "summary"}
    fields: Dict[str, Any] = {}
    for k, v in updates.items():
        if k in allowed:
            if k == "attendees" and isinstance(v, list):
                fields[k] = json.dumps(v)
            else:
                fields[k] = v

    if not fields:
        return get_meeting(meeting_id)

    set_clause = ", ".join(f"{k} = ?" for k in fields)
    params = list(fields.values()) + [meeting_id]
    with _lock:
        conn = _get_conn()
        conn.execute(f"UPDATE meetings SET {set_clause} WHERE id = ?", params)
        conn.commit()
    return get_meeting(meeting_id)


def delete_meeting(meeting_id: str) -> bool:
    with _lock:
        conn = _get_conn()
        cursor = conn.execute("DELETE FROM meetings WHERE id = ?", (meeting_id,))
        conn.commit()
        return cursor.rowcount > 0


# ═══════════════ Action Items ═══════════════

def add_action_item(
    meeting_id: str,
    text: str,
    assignee: str = "",
    due_date: str = "",
    priority: str = "medium",
) -> Dict[str, Any]:
    item_id = str(uuid.uuid4())[:8]
    now = _now()
    with _lock:
        conn = _get_conn()
        conn.execute(
            """INSERT INTO action_items (id, meeting_id, text, assignee, due_date, completed, completed_at, priority, created_at)
               VALUES (?, ?, ?, ?, ?, 0, '', ?, ?)""",
            (item_id, meeting_id, text, assignee, due_date, priority, now),
        )
        conn.commit()
        return dict(conn.execute("SELECT * FROM action_items WHERE id = ?", (item_id,)).fetchone())


def update_action_item(item_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    allowed = {"text", "assignee", "due_date", "completed", "priority"}
    fields: Dict[str, Any] = {}
    for k, v in updates.items():
        if k in allowed:
            fields[k] = v
    # Auto-set completed_at
    if fields.get("completed") == 1:
        fields["completed_at"] = _now()
    elif fields.get("completed") == 0:
        fields["completed_at"] = ""

    if not fields:
        with _lock:
            conn = _get_conn()
            row = conn.execute("SELECT * FROM action_items WHERE id = ?", (item_id,)).fetchone()
            return dict(row) if row else {}

    set_clause = ", ".join(f"{k} = ?" for k in fields)
    params = list(fields.values()) + [item_id]
    with _lock:
        conn = _get_conn()
        conn.execute(f"UPDATE action_items SET {set_clause} WHERE id = ?", params)
        conn.commit()
        row = conn.execute("SELECT * FROM action_items WHERE id = ?", (item_id,)).fetchone()
        return dict(row) if row else {}


def get_pending_actions() -> List[Dict[str, Any]]:
    with _lock:
        conn = _get_conn()
        rows = conn.execute(
            """SELECT ai.*, m.title as meeting_title, m.date as meeting_date
               FROM action_items ai
               JOIN meetings m ON ai.meeting_id = m.id
               WHERE ai.completed = 0
               ORDER BY
                 CASE ai.priority WHEN 'high' THEN 0 WHEN 'medium' THEN 1 ELSE 2 END,
                 ai.due_date ASC""",
        ).fetchall()
    return [dict(r) for r in rows]


# ═══════════════ Follow-ups ═══════════════

def add_follow_up(
    meeting_id: str,
    text: str,
    due_date: str = "",
) -> Dict[str, Any]:
    fu_id = str(uuid.uuid4())[:8]
    now = _now()
    with _lock:
        conn = _get_conn()
        conn.execute(
            """INSERT INTO follow_ups (id, meeting_id, text, due_date, completed, created_at)
               VALUES (?, ?, ?, ?, 0, ?)""",
            (fu_id, meeting_id, text, due_date, now),
        )
        conn.commit()
        return dict(conn.execute("SELECT * FROM follow_ups WHERE id = ?", (fu_id,)).fetchone())


def update_follow_up(follow_up_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    allowed = {"text", "due_date", "completed"}
    fields = {k: v for k, v in updates.items() if k in allowed}
    if not fields:
        with _lock:
            conn = _get_conn()
            row = conn.execute("SELECT * FROM follow_ups WHERE id = ?", (follow_up_id,)).fetchone()
            return dict(row) if row else {}

    set_clause = ", ".join(f"{k} = ?" for k in fields)
    params = list(fields.values()) + [follow_up_id]
    with _lock:
        conn = _get_conn()
        conn.execute(f"UPDATE follow_ups SET {set_clause} WHERE id = ?", params)
        conn.commit()
        row = conn.execute("SELECT * FROM follow_ups WHERE id = ?", (follow_up_id,)).fetchone()
        return dict(row) if row else {}


def get_pending_follow_ups() -> List[Dict[str, Any]]:
    with _lock:
        conn = _get_conn()
        rows = conn.execute(
            """SELECT f.*, m.title as meeting_title, m.date as meeting_date
               FROM follow_ups f
               JOIN meetings m ON f.meeting_id = m.id
               WHERE f.completed = 0
               ORDER BY f.due_date ASC""",
        ).fetchall()
    return [dict(r) for r in rows]


# ═══════════════ Statistics ═══════════════

def get_stats() -> Dict[str, Any]:
    with _lock:
        conn = _get_conn()
        total = conn.execute("SELECT COUNT(*) as c FROM meetings").fetchone()["c"]
        this_week = conn.execute(
            "SELECT COUNT(*) as c FROM meetings WHERE date >= date('now', '-7 days')"
        ).fetchone()["c"]
        pending_actions = conn.execute(
            "SELECT COUNT(*) as c FROM action_items WHERE completed = 0"
        ).fetchone()["c"]
        total_actions = conn.execute(
            "SELECT COUNT(*) as c FROM action_items"
        ).fetchone()["c"]
        completed_actions = conn.execute(
            "SELECT COUNT(*) as c FROM action_items WHERE completed = 1"
        ).fetchone()["c"]
        pending_follow_ups = conn.execute(
            "SELECT COUNT(*) as c FROM follow_ups WHERE completed = 0"
        ).fetchone()["c"]

    return {
        "total_meetings": total,
        "this_week": this_week,
        "pending_actions": pending_actions,
        "pending_follow_ups": pending_follow_ups,
        "completion_rate": round(completed_actions / total_actions * 100, 1) if total_actions > 0 else 0.0,
    }
