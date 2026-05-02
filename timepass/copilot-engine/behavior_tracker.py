"""
Copilot Engine - Behavior Tracker
Tracks developer patterns: error frequency, file switches,
debugging loops, and suggests focus mode when needed.
"""
import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional


class BehaviorTracker:
    """Tracks developer behavior to detect debugging loops and suggest focus mode."""

    def __init__(self):
        # Per-workspace tracking
        self.workspaces: dict[str, WorkspaceSession] = {}

    def get_session(self, workspace_path: str) -> 'WorkspaceSession':
        """Get or create session for a workspace."""
        if workspace_path not in self.workspaces:
            self.workspaces[workspace_path] = WorkspaceSession(workspace_path)
        return self.workspaces[workspace_path]

    def track_event(self, workspace_path: str, event: str, data: dict) -> dict:
        """Track a developer behavior event."""
        session = self.get_session(workspace_path)

        if event == 'error':
            return session.track_error(data)
        elif event == 'file_switch':
            return session.track_file_switch(data)
        elif event == 'file_save':
            return session.track_file_save(data)
        elif event == 'terminal_run':
            return session.track_terminal_run(data)
        elif event == 'copy_paste':
            return session.track_copy_paste(data)
        else:
            session.events.append({
                'event': event,
                'data': data,
                'timestamp': time.time(),
            })
            return session.get_status()

    def get_status(self, workspace_path: str) -> dict:
        """Get current behavior status."""
        session = self.get_session(workspace_path)
        return session.get_status()

    def get_session_report(self, workspace_path: str) -> dict:
        """Get detailed session report."""
        session = self.get_session(workspace_path)
        return session.get_report()


class WorkspaceSession:
    """Tracks behavior for a single workspace session."""

    def __init__(self, workspace_path: str):
        self.workspace_path = workspace_path
        self.start_time = time.time()
        self.events: list[dict] = []

        # Error tracking
        self.error_count = 0
        self.error_types: dict[str, int] = defaultdict(int)
        self.error_history: list[dict] = []
        self.recent_errors: list[str] = []

        # File tracking
        self.file_switch_count = 0
        self.files_visited: set[str] = set()
        self.rapid_switch_timestamps: list[float] = []
        self.last_file_switch_time: float = 0

        # Activity tracking
        self.file_save_count = 0
        self.terminal_run_count = 0
        self.copy_paste_count = 0

        # Loop detection
        self.error_repeat_threshold = 3
        self.rapid_switch_threshold = 10
        self.focus_mode_suggested = False

    def track_error(self, data: dict) -> dict:
        """Track an error event."""
        error_type = data.get('error_type', 'unknown')
        error_msg = data.get('message', '')
        error_sig = f"{error_type}:{error_msg[:50]}"

        self.error_count += 1
        self.error_types[error_type] += 1
        self.recent_errors.append(error_sig)

        # Keep only last 50
        if len(self.recent_errors) > 50:
            self.recent_errors = self.recent_errors[-50:]

        self.error_history.append({
            'type': error_type,
            'message': error_msg[:200],
            'file': data.get('file'),
            'timestamp': time.time(),
        })

        # Keep history manageable
        if len(self.error_history) > 100:
            self.error_history = self.error_history[-100:]

        self.events.append({
            'event': 'error',
            'error_type': error_type,
            'timestamp': time.time(),
        })

        return self.get_status()

    def track_file_switch(self, data: dict) -> dict:
        """Track a file switch event."""
        self.file_switch_count += 1
        file_path = data.get('file', '')
        self.files_visited.add(file_path)

        now = time.time()
        if now - self.last_file_switch_time < 3.0:
            self.rapid_switch_timestamps.append(now)
        self.last_file_switch_time = now

        # Clean old rapid switch timestamps (older than 60 seconds)
        cutoff = now - 60
        self.rapid_switch_timestamps = [t for t in self.rapid_switch_timestamps if t > cutoff]

        return self.get_status()

    def track_file_save(self, data: dict) -> dict:
        """Track a file save event."""
        self.file_save_count += 1
        return self.get_status()

    def track_terminal_run(self, data: dict) -> dict:
        """Track a terminal command execution."""
        self.terminal_run_count += 1
        return self.get_status()

    def track_copy_paste(self, data: dict) -> dict:
        """Track a copy-paste event (often error messages)."""
        self.copy_paste_count += 1
        return self.get_status()

    def get_status(self) -> dict:
        """Get current status with loop detection."""
        # Count repeated errors in last 5 minutes
        now = time.time()
        recent_cutoff = now - 300

        recent_errors = [e for e in self.error_history if e['timestamp'] > recent_cutoff]
        recent_error_types = defaultdict(int)
        for e in recent_errors:
            recent_error_types[e['type']] += 1

        max_repeated = max(recent_error_types.values()) if recent_error_types else 0
        most_repeated_type = max(recent_error_types, key=recent_error_types.get) if recent_error_types else None

        # Detect rapid file switching
        rapid_switches = len(self.rapid_switch_timestamps)

        # Determine if focus mode should be suggested
        suggest_focus = False
        message = 'Normal development pace'

        if max_repeated >= self.error_repeat_threshold:
            suggest_focus = True
            message = f'Debugging loop detected: "{most_repeated_type}" repeated {max_repeated} times in 5 min'
        elif rapid_switches >= self.rapid_switch_threshold:
            suggest_focus = True
            message = f'Rapid file switching detected ({rapid_switches} in 60s) - may indicate confusion'
        elif self.error_count > 10 and self.file_save_count < 3:
            message = 'Many errors with few saves - consider stepping back to plan'

        return {
            'error_count': self.error_count,
            'repeated_errors': max_repeated,
            'most_repeated_error': most_repeated_type,
            'file_switches': self.file_switch_count,
            'rapid_switches': rapid_switches,
            'files_visited': len(self.files_visited),
            'saves': self.file_save_count,
            'terminal_runs': self.terminal_run_count,
            'focus_mode_suggested': suggest_focus,
            'message': message,
            'session_minutes': round((now - self.start_time) / 60, 1),
        }

    def get_report(self) -> dict:
        """Get detailed session report."""
        status = self.get_status()
        now = time.time()

        # Error summary
        error_summary = dict(self.error_types)

        # File visit frequency
        recent_events = [e for e in self.events if e['timestamp'] > now - 600]

        return {
            **status,
            'workspace': self.workspace_path,
            'session_start': datetime.fromtimestamp(self.start_time).isoformat(),
            'error_summary': error_summary,
            'total_events': len(self.events),
            'recent_event_count': len(recent_events),
            'unique_files': len(self.files_visited),
            'copy_pastes': self.copy_paste_count,
        }
