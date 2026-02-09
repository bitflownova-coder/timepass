"""
File Watcher - Monitors workspace for changes
"""
import asyncio
import hashlib
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Set, Callable, Optional, List
from dataclasses import dataclass, field
from watchdog.observers import Observer
from watchdog.events import (
    FileSystemEventHandler, 
    FileCreatedEvent,
    FileModifiedEvent,
    FileDeletedEvent,
    FileMovedEvent
)

from config import settings

logger = logging.getLogger(__name__)


@dataclass
class FileChange:
    """Represents a file change event"""
    path: Path
    event_type: str  # created, modified, deleted, moved
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    old_path: Optional[Path] = None  # For moved files
    content_hash: Optional[str] = None


class WorkspaceWatcher(FileSystemEventHandler):
    """Watches a workspace directory for file changes"""
    
    def __init__(self, workspace_path: str, callback: Callable[[FileChange], None] = None):
        self.workspace_path = Path(workspace_path)
        self.callback = callback
        self.observer = Observer()
        self._running = False
        self._change_buffer: List[FileChange] = []
        self._buffer_lock = asyncio.Lock() if asyncio.get_event_loop().is_running() else None
        self._debounce_task: Optional[asyncio.Task] = None
        self._debounce_delay = 0.5  # seconds
        
    def _should_ignore(self, path: Path) -> bool:
        """Check if path should be ignored"""
        path_str = str(path)
        
        # Check ignored directories
        for ignored in settings.ignored_dirs:
            if f"/{ignored}/" in path_str or f"\\{ignored}\\" in path_str:
                return True
            if path_str.endswith(f"/{ignored}") or path_str.endswith(f"\\{ignored}"):
                return True
        
        # Check file extension
        if path.is_file():
            if path.suffix not in settings.watched_extensions:
                return True
        
        return False
    
    def _get_file_hash(self, path: Path) -> Optional[str]:
        """Get MD5 hash of file content"""
        try:
            if path.exists() and path.is_file():
                return hashlib.md5(path.read_bytes()).hexdigest()
        except Exception:
            pass
        return None
    
    def _create_change(self, path: str, event_type: str, old_path: str = None) -> Optional[FileChange]:
        """Create a FileChange object"""
        file_path = Path(path)
        
        if self._should_ignore(file_path):
            return None
        
        return FileChange(
            path=file_path,
            event_type=event_type,
            old_path=Path(old_path) if old_path else None,
            content_hash=self._get_file_hash(file_path)
        )
    
    def on_created(self, event: FileCreatedEvent):
        if event.is_directory:
            return
        change = self._create_change(event.src_path, "created")
        if change:
            self._handle_change(change)
    
    def on_modified(self, event: FileModifiedEvent):
        if event.is_directory:
            return
        change = self._create_change(event.src_path, "modified")
        if change:
            self._handle_change(change)
    
    def on_deleted(self, event: FileDeletedEvent):
        if event.is_directory:
            return
        change = self._create_change(event.src_path, "deleted")
        if change:
            self._handle_change(change)
    
    def on_moved(self, event: FileMovedEvent):
        if event.is_directory:
            return
        change = self._create_change(event.dest_path, "moved", event.src_path)
        if change:
            self._handle_change(change)
    
    def _handle_change(self, change: FileChange):
        """Handle a file change with debouncing"""
        logger.debug(f"File {change.event_type}: {change.path}")
        
        if self.callback:
            self.callback(change)
    
    def start(self):
        """Start watching"""
        if self._running:
            return
        
        self.observer.schedule(self, str(self.workspace_path), recursive=True)
        self.observer.start()
        self._running = True
        logger.info(f"Started watching: {self.workspace_path}")
    
    def stop(self):
        """Stop watching"""
        if not self._running:
            return
        
        self.observer.stop()
        self.observer.join()
        self._running = False
        logger.info(f"Stopped watching: {self.workspace_path}")
    
    @property
    def is_running(self) -> bool:
        return self._running


class WatcherManager:
    """Manages multiple workspace watchers"""
    
    def __init__(self):
        self._watchers: Dict[str, WorkspaceWatcher] = {}
        self._callbacks: List[Callable[[str, FileChange], None]] = []
    
    def add_callback(self, callback: Callable[[str, FileChange], None]):
        """Add a callback for all file changes"""
        self._callbacks.append(callback)
    
    def _on_change(self, workspace_path: str, change: FileChange):
        """Internal change handler"""
        for callback in self._callbacks:
            try:
                callback(workspace_path, change)
            except Exception as e:
                logger.error(f"Callback error: {e}")
    
    def watch(self, workspace_path: str) -> bool:
        """Start watching a workspace"""
        if workspace_path in self._watchers:
            return True
        
        path = Path(workspace_path)
        if not path.exists() or not path.is_dir():
            logger.error(f"Invalid workspace path: {workspace_path}")
            return False
        
        watcher = WorkspaceWatcher(
            workspace_path,
            callback=lambda change: self._on_change(workspace_path, change)
        )
        watcher.start()
        self._watchers[workspace_path] = watcher
        return True
    
    def unwatch(self, workspace_path: str):
        """Stop watching a workspace"""
        if workspace_path in self._watchers:
            self._watchers[workspace_path].stop()
            del self._watchers[workspace_path]
    
    def get_watched(self) -> List[str]:
        """Get list of watched workspaces"""
        return list(self._watchers.keys())
    
    def stop_all(self):
        """Stop all watchers"""
        for watcher in self._watchers.values():
            watcher.stop()
        self._watchers.clear()


# Global watcher manager
watcher_manager = WatcherManager()
