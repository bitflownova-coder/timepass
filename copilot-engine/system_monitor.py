"""
System Monitor — real-time CPU, RAM, disk, network, and process telemetry.
Uses psutil for cross-platform system metrics.
"""
import time
import logging
import platform
from typing import Any, Dict, List
from collections import deque
from threading import Lock

try:
    import psutil
except ImportError:
    psutil = None  # graceful degradation

logger = logging.getLogger(__name__)

# ── In-memory ring buffer for history ──────────────────────────
_MAX_HISTORY = 120  # ~2 minutes at 1s intervals
_history: deque = deque(maxlen=_MAX_HISTORY)
_history_lock = Lock()
_last_snapshot_time = 0.0


def _require_psutil():
    if psutil is None:
        raise RuntimeError("psutil is not installed. Run: pip install psutil")


def get_system_snapshot() -> Dict[str, Any]:
    """Return a point-in-time snapshot of CPU, RAM, disk, network, and battery."""
    _require_psutil()
    cpu_freq = psutil.cpu_freq()
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    disk = psutil.disk_usage("/")
    net = psutil.net_io_counters()
    boot = psutil.boot_time()

    snapshot: Dict[str, Any] = {
        "timestamp": time.time(),
        "cpu": {
            "percent": psutil.cpu_percent(interval=0),
            "per_core": psutil.cpu_percent(percpu=True),
            "cores_physical": psutil.cpu_count(logical=False) or 0,
            "cores_logical": psutil.cpu_count(logical=True) or 0,
            "freq_current": round(cpu_freq.current, 1) if cpu_freq else 0,
            "freq_max": round(cpu_freq.max, 1) if cpu_freq else 0,
        },
        "memory": {
            "total": mem.total,
            "used": mem.used,
            "available": mem.available,
            "percent": mem.percent,
            "swap_total": swap.total,
            "swap_used": swap.used,
            "swap_percent": swap.percent,
        },
        "disk": {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": disk.percent,
        },
        "network": {
            "bytes_sent": net.bytes_sent,
            "bytes_recv": net.bytes_recv,
            "packets_sent": net.packets_sent,
            "packets_recv": net.packets_recv,
        },
        "system": {
            "platform": platform.system(),
            "platform_release": platform.release(),
            "hostname": platform.node(),
            "architecture": platform.machine(),
            "python_version": platform.python_version(),
            "boot_time": boot,
            "uptime_seconds": round(time.time() - boot),
        },
    }

    # Battery (laptops)
    try:
        batt = psutil.sensors_battery()
        if batt:
            snapshot["battery"] = {
                "percent": batt.percent,
                "plugged": batt.power_plugged,
                "secs_left": batt.secsleft if batt.secsleft != psutil.POWER_TIME_UNLIMITED else -1,
            }
    except Exception:
        pass

    return snapshot


def get_top_processes(limit: int = 15, sort_by: str = "cpu") -> List[Dict[str, Any]]:
    """Return the top processes sorted by CPU or memory usage."""
    _require_psutil()
    procs: List[Dict[str, Any]] = []
    for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent", "status", "create_time"]):
        try:
            info = p.info
            procs.append({
                "pid": info["pid"],
                "name": info["name"] or "unknown",
                "cpu_percent": round(info.get("cpu_percent") or 0, 1),
                "memory_percent": round(info.get("memory_percent") or 0, 1),
                "status": info.get("status", "unknown"),
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    key = "cpu_percent" if sort_by == "cpu" else "memory_percent"
    procs.sort(key=lambda p: p[key], reverse=True)
    return procs[:limit]


def get_disk_partitions() -> List[Dict[str, Any]]:
    """Return mounted disk partitions with usage."""
    _require_psutil()
    parts = []
    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
            parts.append({
                "device": part.device,
                "mountpoint": part.mountpoint,
                "fstype": part.fstype,
                "total": usage.total,
                "used": usage.used,
                "free": usage.free,
                "percent": usage.percent,
            })
        except (PermissionError, OSError):
            continue
    return parts


def record_snapshot() -> Dict[str, Any]:
    """Take a snapshot and add it to the ring-buffer history."""
    global _last_snapshot_time
    snap = get_system_snapshot()
    with _history_lock:
        _history.append({
            "timestamp": snap["timestamp"],
            "cpu": snap["cpu"]["percent"],
            "memory": snap["memory"]["percent"],
            "disk": snap["disk"]["percent"],
            "net_sent": snap["network"]["bytes_sent"],
            "net_recv": snap["network"]["bytes_recv"],
        })
    _last_snapshot_time = snap["timestamp"]
    return snap


def get_history() -> List[Dict[str, Any]]:
    """Return the ring-buffer history for sparkline/charts."""
    with _history_lock:
        return list(_history)


def is_available() -> bool:
    """Check if psutil is installed."""
    return psutil is not None
