"""
Async Task Queue — Phase J (VFS Architecture Refinement)

Lightweight in-process task queue using stdlib threading + queue.Queue.
Two worker threads process submitted callables asynchronously.

Usage:
    from app.utils.task_queue import task_queue

    task_id = task_queue.submit(my_fn, arg1, arg2, kwarg=value)
    status  = task_queue.status(task_id)
    # status: {id, state: 'pending'|'running'|'done'|'error', result, error}
"""
from __future__ import annotations

import logging
import queue
import threading
import uuid
from typing import Any, Callable

logger = logging.getLogger(__name__)

_NUM_WORKERS = 2


class TaskQueue:
    """Thread-safe in-process task queue with N worker threads."""

    def __init__(self, num_workers: int = _NUM_WORKERS):
        self._q: queue.Queue = queue.Queue()
        self._tasks: dict[str, dict] = {}
        self._lock = threading.Lock()
        self._workers: list[threading.Thread] = []

        for _ in range(num_workers):
            t = threading.Thread(target=self._worker, daemon=True)
            t.start()
            self._workers.append(t)

    # ── Public API ────────────────────────────────────────────────────────────

    def submit(self, fn: Callable, *args: Any, **kwargs: Any) -> str:
        """
        Schedule fn(*args, **kwargs) for async execution.

        Returns:
            str: Unique task_id that can be polled via status().
        """
        task_id = str(uuid.uuid4())
        with self._lock:
            self._tasks[task_id] = {'id': task_id, 'state': 'pending',
                                    'result': None, 'error': None}
        self._q.put((task_id, fn, args, kwargs))
        return task_id

    def status(self, task_id: str) -> dict | None:
        """Return a copy of the task status dict, or None if task_id unknown."""
        with self._lock:
            entry = self._tasks.get(task_id)
            return dict(entry) if entry else None

    # ── Internal ──────────────────────────────────────────────────────────────

    def _worker(self):
        while True:
            task_id, fn, args, kwargs = self._q.get()
            with self._lock:
                if task_id in self._tasks:
                    self._tasks[task_id]['state'] = 'running'
            try:
                result = fn(*args, **kwargs)
                with self._lock:
                    self._tasks[task_id].update({'state': 'done', 'result': result})
            except Exception as exc:
                logger.error(f"TaskQueue worker error (task={task_id}): {exc}")
                with self._lock:
                    self._tasks[task_id].update({'state': 'error', 'error': str(exc)})
            finally:
                self._q.task_done()


# Module-level singleton used throughout the application
task_queue = TaskQueue()
