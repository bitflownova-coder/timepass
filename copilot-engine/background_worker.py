"""
Copilot Engine - Autonomous Background Worker
The brain of the autonomous runtime. Processes two paths:

  FAST PATH (on every file save, <200ms):
    1. Incremental re-index of changed file
    2. Graph edge update for changed file
    3. Drift detection (compare to stored snapshot)
    4. Security partial scan
    5. Risk score recalculation

  BACKGROUND PATH (idle worker, every 2-5 minutes):
    1. Dead code detection
    2. Circular dependency detection
    3. Full naming audit
    4. Migration consistency check
    5. Full graph rebuild consistency
    6. Risk trend snapshot

Event queue decouples event production from processing.
"""
import os
import time
import logging
import threading
import hashlib
from queue import Queue, Empty
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timezone
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────
# Change Event
# ──────────────────────────────────────────────────────────────

@dataclass
class ChangeEvent:
    file_path: str
    change_type: str        # saved, opened, created, deleted, renamed
    workspace_path: str
    timestamp: float = field(default_factory=time.time)
    git_branch: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


# ──────────────────────────────────────────────────────────────
# Background Worker
# ──────────────────────────────────────────────────────────────

class BackgroundWorker:
    """
    Autonomous analysis runtime.

    Two threads:
      1. Fast worker — drains the event queue, runs fast-path per event
      2. Idle worker — runs comprehensive checks on a timer

    All analysis modules are injected at construction time.
    DB session factory is injected for thread-safe session creation.
    """

    def __init__(self, db_factory, indexer, graph_engine, drift_detector,
                 migration_monitor, risk_engine, security_scanner,
                 prisma_analyzer, contract_analyzer,
                 ws_broadcast: Callable = None):
        """
        Args:
            db_factory: callable that returns a context-managed DB session
            indexer: SemanticIndexer instance
            graph_engine: GraphEngine instance
            drift_detector: DriftDetector instance
            migration_monitor: MigrationMonitor instance
            risk_engine: RiskEngine instance
            security_scanner: SecurityScanner instance
            prisma_analyzer: PrismaAnalyzer instance
            contract_analyzer: ContractAnalyzer instance
            ws_broadcast: optional callable(workspace_path, event_type, data) for push notifications
        """
        self._db_factory = db_factory
        self._indexer = indexer
        self._graph = graph_engine
        self._drift = drift_detector
        self._migration = migration_monitor
        self._risk = risk_engine
        self._security = security_scanner
        self._prisma = prisma_analyzer
        self._contracts = contract_analyzer
        self._broadcast = ws_broadcast

        # Event queue
        self._queue: Queue[ChangeEvent] = Queue(maxsize=500)

        # State
        self._running = False
        self._fast_thread: Optional[threading.Thread] = None
        self._idle_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._initialized_workspaces: set = set()
        self._last_idle_run: Dict[str, float] = {}
        self._idle_interval = 120  # seconds (2 minutes)

        # Debounce tracking — don't re-process same file within N ms
        self._last_processed: Dict[str, float] = {}
        self._debounce_ms = 500

        # Stats
        self._stats = {
            'events_processed': 0,
            'fast_path_runs': 0,
            'idle_runs': 0,
            'errors': 0,
            'started_at': None,
            'last_event': None,
        }

    # ══════════════════════════════════════════════
    # Lifecycle
    # ══════════════════════════════════════════════

    def start(self):
        """Start the background worker threads."""
        if self._running:
            return

        self._running = True
        self._stats['started_at'] = datetime.now(timezone.utc).isoformat()

        self._fast_thread = threading.Thread(
            target=self._fast_worker_loop,
            daemon=True,
            name='copilot-fast-worker'
        )
        self._idle_thread = threading.Thread(
            target=self._idle_worker_loop,
            daemon=True,
            name='copilot-idle-worker'
        )

        self._fast_thread.start()
        self._idle_thread.start()
        logger.info("Background worker started (fast + idle workers)")

    def stop(self):
        """Stop the background worker."""
        self._running = False
        # Put a poison pill to unblock the queue
        try:
            self._queue.put_nowait(None)
        except Exception:
            pass
        logger.info("Background worker stopped")

    def is_running(self) -> bool:
        return self._running

    def get_stats(self) -> Dict[str, Any]:
        return dict(self._stats)

    # ══════════════════════════════════════════════
    # Event Submission
    # ══════════════════════════════════════════════

    def submit_event(self, event: ChangeEvent):
        """Submit a change event to the processing queue."""
        if not self._running:
            return

        try:
            self._queue.put_nowait(event)
        except Exception:
            logger.warning("Event queue full, dropping event")

    def submit_file_change(self, file_path: str, workspace_path: str,
                           change_type: str = 'saved'):
        """Convenience method for file change events."""
        self.submit_event(ChangeEvent(
            file_path=file_path,
            change_type=change_type,
            workspace_path=workspace_path,
        ))

    # ══════════════════════════════════════════════
    # Initialize Workspace (first-time full index)
    # ══════════════════════════════════════════════

    def initialize_workspace(self, workspace_path: str) -> Dict[str, Any]:
        """
        Full initialization for a workspace (called once on register).
        Runs full index, builds graph, runs all analysis.
        """
        with self._lock:
            if workspace_path in self._initialized_workspaces:
                return {'already_initialized': True}

        result = {'workspace': workspace_path, 'steps': {}}

        try:
            logger.info(f"🚀 Starting workspace initialization: {workspace_path}")
            logger.info(f"📊 Step 1/4: Scanning files...")
            
            with self._db_factory() as session:
                # 1. Full semantic index
                idx_result = self._indexer.full_index(workspace_path, db_session=session)
                result['steps']['index'] = idx_result
                logger.info(f"✓ Indexed {idx_result.get('indexed', 0)} files, {idx_result.get('entities_found', 0)} entities")

                # Bail out early if indexing failed (e.g. workspace path doesn't exist)
                if idx_result.get('error'):
                    logger.warning(f"⚠️  Index returned error: {idx_result['error']} — skipping graph/snapshot steps")
                    result['steps']['graph'] = {'built': False, 'reason': idx_result['error']}
                    result['steps']['snapshots'] = 0
                    result['steps']['risk'] = self._compute_full_risk(workspace_path)
                    with self._lock:
                        self._initialized_workspaces.add(workspace_path)
                    result['initialized'] = True
                    return result

                # 2. Build dependency graph
                logger.info(f"📊 Step 2/4: Building dependency graph...")
                graph_result = self._graph.build_from_indexer(workspace_path, self._indexer, session)
                result['steps']['graph'] = graph_result
                logger.info(f"✓ Built graph: {graph_result.get('file_edges', 0)} file edges, {graph_result.get('entity_edges', 0)} entity edges")

                # 3. Store initial AST snapshots for drift baseline
                logger.info(f"📊 Step 3/4: Creating AST snapshots for drift detection...")
                from models import EntityIndex
                ws_model = session.query(self._get_ws_model()).filter_by(path=workspace_path).first()
                if ws_model:
                    files = session.query(EntityIndex.file_path).filter(
                        EntityIndex.workspace_id == ws_model.id
                    ).distinct().all()
                    snap_count = 0
                    for (fpath,) in files:
                        snap = self._indexer.build_ast_snapshot(fpath)
                        if snap:
                            self._drift.update_snapshot(fpath, snap, workspace_path, session)
                            snap_count += 1
                    result['steps']['snapshots'] = snap_count
                    logger.info(f"✓ Created {snap_count} AST snapshots")

            # 4. Run initial risk assessment (outside the session to avoid nesting)
            logger.info(f"📊 Step 4/4: Computing risk assessment...")
            risk_result = self._compute_full_risk(workspace_path)
            result['steps']['risk'] = risk_result
            logger.info(f"✓ Risk analysis complete (score: {risk_result.get('overall_score', 0):.1f}/10)")

            with self._lock:
                self._initialized_workspaces.add(workspace_path)
            result['initialized'] = True
            logger.info(f"✅ Workspace initialization complete!")
            
            # Broadcast completion if WS available
            if self._broadcast:
                try:
                    self._broadcast(workspace_path, 'init_complete', {
                        'files': idx_result.get('indexed', 0),
                        'entities': idx_result.get('entities_found', 0),
                        'risk_score': risk_result.get('overall_score', 0)
                    })
                except:
                    pass

        except Exception as e:
            logger.error(f"❌ Workspace initialization error: {e}")
            result['error'] = str(e)
            self._stats['errors'] += 1

        return result

    # ══════════════════════════════════════════════
    # Fast Worker (Event-Driven)
    # ══════════════════════════════════════════════

    def _fast_worker_loop(self):
        """Drain event queue and run fast-path for each event."""
        while self._running:
            try:
                event = self._queue.get(timeout=1.0)
                if event is None:
                    break  # Poison pill — stop the worker

                # Debounce
                now = time.time()
                last = self._last_processed.get(event.file_path, 0)
                if (now - last) * 1000 < self._debounce_ms:
                    continue
                self._last_processed[event.file_path] = now

                self._run_fast_path(event)
                self._stats['events_processed'] += 1
                self._stats['last_event'] = event.file_path

            except Empty:
                continue
            except Exception as e:
                logger.error(f"Fast worker error: {e}")
                self._stats['errors'] += 1

    def _run_fast_path(self, event: ChangeEvent):
        """
        Fast path — runs on every file save.
        Target: under 200ms total.
        """
        start = time.time()
        file_path = event.file_path
        workspace_path = event.workspace_path

        # Skip non-code files
        ext = Path(file_path).suffix.lower()
        if ext not in ('.py', '.ts', '.tsx', '.js', '.jsx', '.prisma'):
            return

        drifts_detected = []

        try:
            with self._db_factory() as session:
                # 1. Incremental re-index
                parse_result = self._indexer.incremental_update(
                    file_path, workspace_path, db_session=session
                )

                if parse_result:
                    # 2. Update graph edges for this file
                    self._graph.update_file(file_path, workspace_path, session)

                    # 3. Drift detection
                    new_snap = self._indexer.build_ast_snapshot(file_path)
                    if new_snap:
                        old_snap = self._drift.get_stored_snapshot(
                            file_path, workspace_path, session
                        )
                        if old_snap:
                            drifts_detected = self._drift.compare_snapshots(old_snap, new_snap)
                            if drifts_detected:
                                self._drift.persist_drifts(
                                    drifts_detected, workspace_path, session
                                )
                        # Update stored snapshot
                        self._drift.update_snapshot(
                            file_path, new_snap, workspace_path, session
                        )

        except Exception as e:
            logger.error(f"Fast path error (index/graph/drift): {e}")
            self._stats['errors'] += 1

        # 4. Security partial scan (file-level)
        security_findings = []
        try:
            scan_result = self._security.scan_file(file_path)
            if scan_result and isinstance(scan_result, list):
                security_findings = [f for f in scan_result if isinstance(f, dict)]
        except Exception as e:
            logger.error(f"Fast path security scan error: {e}")

        # 5. Quick risk recalculation
        try:
            self._quick_risk_update(workspace_path, drifts_detected, security_findings)
        except Exception as e:
            logger.error(f"Fast path risk update error: {e}")

        self._stats['fast_path_runs'] += 1
        elapsed = (time.time() - start) * 1000
        if elapsed > 200:
            logger.warning(f"Fast path took {elapsed:.0f}ms for {file_path}")

        # 6. Broadcast update to extension via WebSocket
        if self._broadcast and (drifts_detected or security_findings):
            try:
                self._broadcast(workspace_path, 'fast_path_complete', {
                    'file': file_path,
                    'drifts': len(drifts_detected),
                    'security_findings': len(security_findings),
                    'elapsed_ms': round(elapsed, 1),
                })
            except Exception:
                pass

    # ══════════════════════════════════════════════
    # Idle Worker (Background Timer)
    # ══════════════════════════════════════════════

    def _idle_worker_loop(self):
        """Runs comprehensive checks on a timer."""
        while self._running:
            try:
                time.sleep(10)  # Check every 10 seconds if it's time

                now = time.time()
                with self._lock:
                    workspaces = list(self._initialized_workspaces)
                for workspace_path in workspaces:
                    last_run = self._last_idle_run.get(workspace_path, 0)
                    if now - last_run >= self._idle_interval:
                        self._run_idle_path(workspace_path)
                        self._last_idle_run[workspace_path] = now

            except Exception as e:
                logger.error(f"Idle worker error: {e}")
                self._stats['errors'] += 1

    def _run_idle_path(self, workspace_path: str):
        """
        Background path — runs every 2-5 minutes.
        Comprehensive analysis that's too slow for fast-path.
        """
        start = time.time()
        logger.info(f"Running idle analysis for {workspace_path}")

        try:
            risk_result = self._compute_full_risk(workspace_path)

            # Persist risk snapshot for trend
            with self._db_factory() as session:
                self._risk.persist_snapshot(workspace_path, risk_result, session)

            self._stats['idle_runs'] += 1

            # Broadcast to extension
            if self._broadcast:
                try:
                    self._broadcast(workspace_path, 'idle_complete', {
                        'risk': risk_result,
                        'elapsed_ms': round((time.time() - start) * 1000, 1),
                    })
                except Exception:
                    pass

        except Exception as e:
            logger.error(f"Idle path error: {e}")
            self._stats['errors'] += 1

    # ══════════════════════════════════════════════
    # Risk Computation
    # ══════════════════════════════════════════════

    def _compute_full_risk(self, workspace_path: str) -> Dict[str, Any]:
        """Run all analysis modules and compute full risk score."""
        prisma_result = None
        contract_result = None
        migration_result = None
        graph_stats = None
        security_result = None
        drift_summary = None

        # Prisma
        try:
            prisma_result = self._prisma.analyze_workspace(workspace_path)
        except Exception:
            pass

        # Contracts
        try:
            contract_result = self._contracts.analyze_workspace(workspace_path)
        except Exception:
            pass

        # Migration
        try:
            migration_result = self._migration.check(workspace_path)
        except Exception:
            pass

        # Graph
        try:
            graph_stats = self._graph.get_graph_stats()
        except Exception:
            pass

        # Security (workspace-level)
        try:
            security_result = self._security.scan_workspace(workspace_path)
        except Exception:
            pass

        # Drift
        try:
            with self._db_factory() as session:
                drift_summary = self._drift.get_drift_summary(workspace_path, session)
        except Exception:
            pass

        # Compute
        return self._risk.compute(
            workspace_path=workspace_path,
            prisma_result=prisma_result,
            contract_result=contract_result,
            migration_result=migration_result,
            graph_stats=graph_stats,
            security_result=security_result,
            drift_summary=drift_summary,
        )

    def _quick_risk_update(self, workspace_path: str,
                           drifts: List[Dict], security_findings: List[Dict]):
        """
        Lightweight risk update after fast-path.
        Only updates drift + security categories, keeps rest unchanged.
        """
        try:
            with self._db_factory() as session:
                drift_summary = self._drift.get_drift_summary(workspace_path, session)

            # Just recompute with minimal data
            self._risk.compute(
                workspace_path=workspace_path,
                drift_summary=drift_summary,
                security_result={
                    'total_findings': len(security_findings),
                    'critical': sum(1 for f in security_findings if f.get('severity') == 'CRITICAL'),
                    'high': sum(1 for f in security_findings if f.get('severity') == 'HIGH'),
                } if security_findings else None,
            )
        except Exception:
            pass

    # ══════════════════════════════════════════════
    # Query API (for dashboard / routes)
    # ══════════════════════════════════════════════

    def get_health(self, workspace_path: str) -> Dict[str, Any]:
        """Get current workspace health status for dashboard."""
        risk = self._risk.get_latest(workspace_path)

        # Graph stats
        graph_stats = {}
        try:
            graph_stats = self._graph.get_graph_stats()
        except Exception:
            pass

        # Drift summary
        drift_summary = {}
        try:
            with self._db_factory() as session:
                drift_summary = self._drift.get_drift_summary(workspace_path, session)
        except Exception:
            pass

        return {
            'workspace': workspace_path,
            'risk_scores': risk,
            'graph': graph_stats,
            'drift': drift_summary,
            'worker': self._stats,
        }

    def get_risk_trend(self, workspace_path: str, limit: int = 50) -> List[Dict]:
        """Get risk score trend over time."""
        try:
            with self._db_factory() as session:
                return self._risk.get_trend(workspace_path, session, limit)
        except Exception:
            return []

    def get_unresolved_drifts(self, workspace_path: str) -> List[Dict]:
        try:
            with self._db_factory() as session:
                return self._drift.get_unresolved_drifts(workspace_path, session)
        except Exception:
            return []

    def get_circular_deps(self) -> List[List[str]]:
        try:
            return self._graph.detect_circular_dependencies()
        except Exception:
            return []

    def get_dead_code(self) -> List[str]:
        try:
            return self._graph.find_dead_code_files()
        except Exception:
            return []

    # ── Helper ──

    def _get_ws_model(self):
        from models import Workspace
        return Workspace
