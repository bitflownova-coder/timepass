"""
Copilot Engine - Continuous Risk Engine
Maintains a real-time, multi-category health model for each workspace.

Risk categories:
  - schema:     Prisma/ORM issues (relations, indexes, naming)
  - contract:   API contract violations (HTTP discipline, auth, naming)
  - migration:  Schema drift, unapplied migrations
  - dependency: Circular dependencies, dead code, impact radius
  - security:   Hardcoded secrets, injection risks, weak crypto
  - naming:     Naming convention violations across the codebase
  - drift:      Structural drift (removed/changed fields, types, signatures)

Each category scored 0-10.
Aggregate → overall ProjectHealthScore.
History stored for trend visualization.
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class RiskEngine:
    """
    Aggregates risk scores from all enforcement modules into a unified health model.
    Persists snapshots for trend tracking.
    """

    # Weights for aggregate score
    CATEGORY_WEIGHTS = {
        'schema':     1.2,
        'contract':   1.3,
        'migration':  1.0,
        'dependency': 0.8,
        'security':   1.5,
        'naming':     0.5,
        'drift':      1.4,
    }

    def __init__(self):
        # In-memory latest scores per workspace
        self._scores: Dict[str, Dict[str, float]] = {}

    def compute(self, workspace_path: str,
                prisma_result: Dict = None,
                contract_result: Dict = None,
                migration_result: Dict = None,
                graph_stats: Dict = None,
                security_result: Dict = None,
                drift_summary: Dict = None,
                naming_issues: int = 0) -> Dict[str, Any]:
        """
        Compute risk scores from all available analysis results.
        Any parameter can be None (skip that category).
        """
        scores = {
            'schema': 0.0,
            'contract': 0.0,
            'migration': 0.0,
            'dependency': 0.0,
            'security': 0.0,
            'naming': 0.0,
            'drift': 0.0,
        }

        # ── Schema Risk (from Prisma analysis) ──
        if prisma_result:
            total_issues = prisma_result.get('total_issues', 0)
            sev_map = prisma_result.get('issues_by_severity', {})
            scores['schema'] = self._issues_to_score(
                total_issues,
                sev_map.get('CRITICAL', 0),
                sev_map.get('HIGH', 0),
                sev_map.get('MEDIUM', 0),
            )

        # ── Contract Risk (from Contract analysis) ──
        if contract_result:
            total_v = contract_result.get('total_violations', 0)
            sev_map = contract_result.get('violations_by_severity', {})
            scores['contract'] = self._issues_to_score(
                total_v,
                sev_map.get('CRITICAL', 0),
                sev_map.get('HIGH', 0),
                sev_map.get('MEDIUM', 0),
            )

        # ── Migration Risk ──
        if migration_result:
            scores['migration'] = migration_result.get('risk_score', 0.0)

        # ── Dependency Risk (from graph engine) ──
        if graph_stats:
            circular = graph_stats.get('circular_count', 0)
            dead = graph_stats.get('dead_code_files', 0)
            scores['dependency'] = min(10.0,
                circular * 2.5 +
                min(dead * 0.3, 3.0)
            )

        # ── Security Risk ──
        if security_result:
            summary = security_result.get('summary', security_result)
            findings = security_result.get('total_findings', 0)
            critical = summary.get('critical', 0)
            high = summary.get('high', 0)
            scores['security'] = self._issues_to_score(findings, critical, high, 0)

        # ── Naming Risk ──
        scores['naming'] = min(10.0, naming_issues * 0.5)

        # ── Drift Risk ──
        if drift_summary:
            by_sev = drift_summary.get('by_severity', {})
            total_drift = drift_summary.get('total_unresolved', 0)
            scores['drift'] = self._issues_to_score(
                total_drift,
                by_sev.get('CRITICAL', 0),
                by_sev.get('HIGH', 0),
                by_sev.get('MEDIUM', 0),
            )

        # ── Aggregate ──
        weighted_sum = sum(scores[k] * self.CATEGORY_WEIGHTS[k] for k in scores)
        total_weight = sum(self.CATEGORY_WEIGHTS.values())
        overall = round(min(10.0, weighted_sum / total_weight), 2)

        # Health level
        if overall <= 2.0:
            health_level = 'HEALTHY'
        elif overall <= 4.0:
            health_level = 'CAUTION'
        elif overall <= 6.0:
            health_level = 'AT_RISK'
        elif overall <= 8.0:
            health_level = 'DEGRADED'
        else:
            health_level = 'CRITICAL'

        result = {
            'overall_score': overall,
            'health_level': health_level,
            'categories': scores,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }

        self._scores[workspace_path] = scores
        return result

    def persist_snapshot(self, workspace_path: str, risk_result: Dict[str, Any],
                         db_session) -> None:
        """Store a point-in-time risk snapshot for trend tracking."""
        from models import RiskHistory, Workspace

        ws = db_session.query(Workspace).filter(Workspace.path == workspace_path).first()
        if not ws:
            return

        cats = risk_result.get('categories', {})
        db_session.add(RiskHistory(
            workspace_id=ws.id,
            timestamp=datetime.now(timezone.utc),
            schema_risk=cats.get('schema', 0.0),
            contract_risk=cats.get('contract', 0.0),
            migration_risk=cats.get('migration', 0.0),
            dependency_risk=cats.get('dependency', 0.0),
            security_risk=cats.get('security', 0.0),
            naming_risk=cats.get('naming', 0.0),
            drift_risk=cats.get('drift', 0.0),
            overall_score=risk_result.get('overall_score', 0.0),
            issue_count=0,
            details=risk_result,
        ))
        db_session.commit()

    def get_trend(self, workspace_path: str, db_session,
                  limit: int = 50) -> List[Dict[str, Any]]:
        """Get risk score trend over time."""
        from models import RiskHistory, Workspace

        ws = db_session.query(Workspace).filter(Workspace.path == workspace_path).first()
        if not ws:
            return []

        records = db_session.query(RiskHistory).filter(
            RiskHistory.workspace_id == ws.id
        ).order_by(RiskHistory.timestamp.desc()).limit(limit).all()

        return [{
            'timestamp': r.timestamp.isoformat() if r.timestamp else '',
            'overall_score': r.overall_score,
            'schema': r.schema_risk,
            'contract': r.contract_risk,
            'migration': r.migration_risk,
            'dependency': r.dependency_risk,
            'security': r.security_risk,
            'naming': r.naming_risk,
            'drift': r.drift_risk,
        } for r in reversed(records)]

    def get_latest(self, workspace_path: str) -> Dict[str, float]:
        """Get latest in-memory scores."""
        return dict(self._scores.get(workspace_path, {}))

    def _issues_to_score(self, total: int, critical: int = 0,
                         high: int = 0, medium: int = 0) -> float:
        """Convert issue counts to a 0-10 risk score."""
        score = critical * 3.0 + high * 1.5 + medium * 0.5
        # Diminishing returns above a few issues
        if total > 10:
            score += (total - 10) * 0.1
        return round(min(10.0, score), 2)
