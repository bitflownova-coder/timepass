"""
Infrastructure Monitor — HTTP health checks, uptime tracking, and alert rules.
Monitors deployed services, APIs, and websites with configurable check intervals.
Uses SQLite for persistence of check results and alert history.
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
import urllib.request
import urllib.error
import ssl

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
    _DB_PATH = Path(db_dir) / "infra_monitor.db"
    _get_conn()
    logger.info(f"Infra monitor initialized: {_DB_PATH}")


def _init_tables(conn: sqlite3.Connection):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS endpoints (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            url TEXT NOT NULL,
            method TEXT DEFAULT 'GET',
            expected_status INTEGER DEFAULT 200,
            timeout_seconds INTEGER DEFAULT 10,
            check_interval_seconds INTEGER DEFAULT 60,
            category TEXT DEFAULT 'api',
            enabled INTEGER DEFAULT 1,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS check_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            endpoint_id TEXT NOT NULL,
            status_code INTEGER,
            response_time_ms REAL,
            is_up INTEGER NOT NULL,
            error_message TEXT DEFAULT '',
            checked_at TEXT NOT NULL,
            FOREIGN KEY (endpoint_id) REFERENCES endpoints(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS alerts (
            id TEXT PRIMARY KEY,
            endpoint_id TEXT NOT NULL,
            alert_type TEXT NOT NULL,
            message TEXT NOT NULL,
            severity TEXT DEFAULT 'warning',
            acknowledged INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            FOREIGN KEY (endpoint_id) REFERENCES endpoints(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_results_endpoint ON check_results(endpoint_id, checked_at DESC);
        CREATE INDEX IF NOT EXISTS idx_alerts_endpoint ON alerts(endpoint_id);
        CREATE INDEX IF NOT EXISTS idx_alerts_ack ON alerts(acknowledged);
    """)
    conn.commit()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row_to_dict(row) -> Dict[str, Any]:
    return dict(row) if row else {}


# ═══════════════ Endpoint CRUD ═══════════════

def add_endpoint(
    name: str,
    url: str,
    method: str = "GET",
    expected_status: int = 200,
    timeout_seconds: int = 10,
    check_interval_seconds: int = 60,
    category: str = "api",
) -> Dict[str, Any]:
    endpoint_id = str(uuid.uuid4())[:8]
    now = _now()
    with _lock:
        conn = _get_conn()
        conn.execute(
            """INSERT INTO endpoints (id, name, url, method, expected_status,
               timeout_seconds, check_interval_seconds, category, enabled, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)""",
            (endpoint_id, name, url, method, expected_status,
             timeout_seconds, check_interval_seconds, category, now),
        )
        conn.commit()
    return get_endpoint(endpoint_id)


def get_endpoint(endpoint_id: str) -> Dict[str, Any]:
    with _lock:
        conn = _get_conn()
        row = conn.execute("SELECT * FROM endpoints WHERE id = ?", (endpoint_id,)).fetchone()
    return _row_to_dict(row)


def list_endpoints() -> List[Dict[str, Any]]:
    with _lock:
        conn = _get_conn()
        rows = conn.execute("SELECT * FROM endpoints ORDER BY category, name").fetchall()
        endpoints = []
        for row in rows:
            ep = _row_to_dict(row)
            # Get latest check result
            latest = conn.execute(
                """SELECT status_code, response_time_ms, is_up, error_message, checked_at
                   FROM check_results WHERE endpoint_id = ?
                   ORDER BY checked_at DESC LIMIT 1""",
                (ep["id"],),
            ).fetchone()
            ep["latest_check"] = _row_to_dict(latest) if latest else None

            # Count recent downtime (last 24h)
            down_count = conn.execute(
                """SELECT COUNT(*) as c FROM check_results
                   WHERE endpoint_id = ? AND is_up = 0
                   AND checked_at >= datetime('now', '-1 day')""",
                (ep["id"],),
            ).fetchone()
            total_count = conn.execute(
                """SELECT COUNT(*) as c FROM check_results
                   WHERE endpoint_id = ?
                   AND checked_at >= datetime('now', '-1 day')""",
                (ep["id"],),
            ).fetchone()
            total = total_count["c"] if total_count else 0
            down = down_count["c"] if down_count else 0
            ep["uptime_24h"] = round((1 - down / total) * 100, 1) if total > 0 else 100.0
            endpoints.append(ep)
    return endpoints


def update_endpoint(endpoint_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    allowed = {"name", "url", "method", "expected_status", "timeout_seconds",
               "check_interval_seconds", "category", "enabled"}
    fields = {k: v for k, v in updates.items() if k in allowed}
    if not fields:
        return get_endpoint(endpoint_id)

    set_clause = ", ".join(f"{k} = ?" for k in fields)
    params = list(fields.values()) + [endpoint_id]
    with _lock:
        conn = _get_conn()
        conn.execute(f"UPDATE endpoints SET {set_clause} WHERE id = ?", params)
        conn.commit()
    return get_endpoint(endpoint_id)


def delete_endpoint(endpoint_id: str) -> bool:
    with _lock:
        conn = _get_conn()
        cursor = conn.execute("DELETE FROM endpoints WHERE id = ?", (endpoint_id,))
        conn.commit()
        return cursor.rowcount > 0


# ═══════════════ Health Checks ═══════════════

def check_endpoint(endpoint_id: str) -> Dict[str, Any]:
    """Perform an HTTP health check on a single endpoint."""
    ep = get_endpoint(endpoint_id)
    if not ep:
        return {"error": "Endpoint not found"}

    url = ep["url"]
    method = ep.get("method", "GET")
    expected = ep.get("expected_status", 200)
    timeout = ep.get("timeout_seconds", 10)

    start = time.time()
    status_code = 0
    is_up = False
    error_msg = ""

    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(url, method=method)
        req.add_header("User-Agent", "BitflowInfraMonitor/1.0")
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            status_code = resp.status
            is_up = status_code == expected
    except urllib.error.HTTPError as e:
        status_code = e.code
        is_up = status_code == expected
        if not is_up:
            error_msg = f"HTTP {e.code}: {e.reason}"
    except urllib.error.URLError as e:
        error_msg = str(e.reason)
    except Exception as e:
        error_msg = str(e)

    response_time = round((time.time() - start) * 1000, 1)
    now = _now()

    # Store result
    with _lock:
        conn = _get_conn()
        conn.execute(
            """INSERT INTO check_results (endpoint_id, status_code, response_time_ms,
               is_up, error_message, checked_at) VALUES (?, ?, ?, ?, ?, ?)""",
            (endpoint_id, status_code, response_time, int(is_up), error_msg, now),
        )
        conn.commit()

    result = {
        "endpoint_id": endpoint_id,
        "name": ep["name"],
        "url": url,
        "status_code": status_code,
        "response_time_ms": response_time,
        "is_up": is_up,
        "error_message": error_msg,
        "checked_at": now,
    }

    # Generate alert if down
    if not is_up:
        _create_alert(endpoint_id, "endpoint_down",
                       f"{ep['name']} is DOWN: {error_msg or f'HTTP {status_code}'}",
                       "error")

    return result


def check_all() -> List[Dict[str, Any]]:
    """Check all enabled endpoints."""
    endpoints = list_endpoints()
    results = []
    for ep in endpoints:
        if ep.get("enabled", 1):
            result = check_endpoint(ep["id"])
            results.append(result)
    return results


def get_check_history(endpoint_id: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Get recent check results for an endpoint."""
    with _lock:
        conn = _get_conn()
        rows = conn.execute(
            """SELECT * FROM check_results WHERE endpoint_id = ?
               ORDER BY checked_at DESC LIMIT ?""",
            (endpoint_id, limit),
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


# ═══════════════ Alerts ═══════════════

def _create_alert(endpoint_id: str, alert_type: str, message: str, severity: str = "warning"):
    alert_id = str(uuid.uuid4())[:8]
    now = _now()
    try:
        conn = _get_conn()
        conn.execute(
            """INSERT INTO alerts (id, endpoint_id, alert_type, message, severity, acknowledged, created_at)
               VALUES (?, ?, ?, ?, ?, 0, ?)""",
            (alert_id, endpoint_id, alert_type, message, severity, now),
        )
        conn.commit()
    except Exception as e:
        logger.error(f"Failed to create alert: {e}")


def get_alerts(acknowledged: Optional[bool] = None, limit: int = 50) -> List[Dict[str, Any]]:
    with _lock:
        conn = _get_conn()
        query = """SELECT a.*, e.name as endpoint_name, e.url as endpoint_url
                   FROM alerts a JOIN endpoints e ON a.endpoint_id = e.id"""
        params: List[Any] = []
        if acknowledged is not None:
            query += " WHERE a.acknowledged = ?"
            params.append(int(acknowledged))
        query += " ORDER BY a.created_at DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(query, params).fetchall()
    return [_row_to_dict(r) for r in rows]


def acknowledge_alert(alert_id: str) -> bool:
    with _lock:
        conn = _get_conn()
        cursor = conn.execute("UPDATE alerts SET acknowledged = 1 WHERE id = ?", (alert_id,))
        conn.commit()
        return cursor.rowcount > 0


# ═══════════════ Statistics ═══════════════

def get_stats() -> Dict[str, Any]:
    with _lock:
        conn = _get_conn()
        total_eps = conn.execute("SELECT COUNT(*) as c FROM endpoints").fetchone()["c"]
        enabled_eps = conn.execute("SELECT COUNT(*) as c FROM endpoints WHERE enabled = 1").fetchone()["c"]
        total_checks = conn.execute("SELECT COUNT(*) as c FROM check_results").fetchone()["c"]
        # Count endpoints where the latest check is UP
        recent_up = conn.execute(
            """SELECT COUNT(*) as c FROM endpoints e
               WHERE e.enabled = 1
               AND EXISTS (
                   SELECT 1 FROM check_results cr
                   WHERE cr.endpoint_id = e.id AND cr.is_up = 1
                   AND cr.checked_at = (SELECT MAX(cr2.checked_at) FROM check_results cr2 WHERE cr2.endpoint_id = e.id)
               )"""
        ).fetchone()["c"]
        unack_alerts = conn.execute(
            "SELECT COUNT(*) as c FROM alerts WHERE acknowledged = 0"
        ).fetchone()["c"]

        # Average response time (last 100 checks)
        avg_rt = conn.execute(
            "SELECT AVG(response_time_ms) as avg_rt FROM (SELECT response_time_ms FROM check_results WHERE is_up = 1 ORDER BY checked_at DESC LIMIT 100)"
        ).fetchone()

    return {
        "total_endpoints": total_eps,
        "enabled_endpoints": enabled_eps,
        "endpoints_up": recent_up,
        "endpoints_down": enabled_eps - recent_up,
        "total_checks": total_checks,
        "unacknowledged_alerts": unack_alerts,
        "avg_response_time_ms": round(avg_rt["avg_rt"], 1) if avg_rt and avg_rt["avg_rt"] else 0,
    }
