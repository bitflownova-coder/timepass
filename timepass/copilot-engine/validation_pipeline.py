"""
Copilot Engine - Structural Validation Pipeline
Unified pipeline that runs all enforcement checks on file changes.

Flow:
  File Change → AST/Regex Parse → Entity Extract → Contract Match
  → Prisma Validate → API Discipline Check → Security Scan
  → Change Impact Analyze → Risk Score → Report

This is the single entry point that orchestrates all three enforcement pillars:
  1. Prisma / ORM Intelligence
  2. API Contract Enforcement
  3. Change Impact Analysis
"""
import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone

from prisma_analyzer import PrismaAnalyzer
from contract_analyzer import ContractAnalyzer
from impact_analyzer import ImpactAnalyzer
from security_scanner import SecurityScanner


# ──────────────────────────────────────────────────────────────
# Data Structures
# ──────────────────────────────────────────────────────────────

@dataclass
class RiskReport:
    """Unified risk report from all enforcement pillars."""
    workspace_path: str
    timestamp: str
    overall_risk_score: float = 0.0
    overall_risk_level: str = "LOW"

    # Per-pillar summaries
    prisma_issues: int = 0
    contract_violations: int = 0
    security_findings: int = 0
    impact_radius: int = 0

    # Detailed results
    prisma: Dict[str, Any] = field(default_factory=dict)
    contracts: Dict[str, Any] = field(default_factory=dict)
    security: Dict[str, Any] = field(default_factory=dict)
    impact: Dict[str, Any] = field(default_factory=dict)

    # Aggregated issues list (for UI)
    issues: List[Dict[str, Any]] = field(default_factory=list)


# ──────────────────────────────────────────────────────────────
# Validation Pipeline
# ──────────────────────────────────────────────────────────────

class ValidationPipeline:
    """Unified enforcement pipeline orchestrator."""

    def __init__(self):
        self.prisma = PrismaAnalyzer()
        self.contracts = ContractAnalyzer()
        self.impact = ImpactAnalyzer()
        self.security = SecurityScanner()

    def full_scan(self, workspace_path: str) -> Dict[str, Any]:
        """Run all enforcement checks on a workspace.
        
        This is the comprehensive scan — runs everything.
        Use for initial workspace registration or periodic full audits.
        """
        report = RiskReport(
            workspace_path=workspace_path,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        # 1. Prisma / ORM Intelligence
        try:
            prisma_result = self.prisma.analyze_workspace(workspace_path)
            report.prisma = prisma_result
            report.prisma_issues = prisma_result.get('total_issues', 0)
            # Add prisma issues to unified list
            for issue in prisma_result.get('issues', []):
                report.issues.append({
                    'pillar': 'prisma',
                    **issue,
                })
        except Exception as e:
            report.prisma = {'error': str(e)}

        # 2. API Contract Enforcement
        try:
            contract_result = self.contracts.analyze_workspace(workspace_path)
            report.contracts = contract_result
            report.contract_violations = contract_result.get('total_violations', 0)
            for violation in contract_result.get('violations', []):
                report.issues.append({
                    'pillar': 'contracts',
                    **violation,
                })
        except Exception as e:
            report.contracts = {'error': str(e)}

        # 3. Security Scan
        try:
            security_result = self.security.scan_workspace(workspace_path)
            report.security = security_result
            report.security_findings = security_result.get('total_findings', 0)
            for finding in security_result.get('findings', []):
                report.issues.append({
                    'pillar': 'security',
                    'severity': finding.get('severity', 'MEDIUM'),
                    'category': finding.get('category', 'security'),
                    'message': finding.get('issue', ''),
                    'file_path': finding.get('file', ''),
                    'line_number': finding.get('line', 0),
                })
        except Exception as e:
            report.security = {'error': str(e)}

        # 4. Dependency & Impact Graph
        try:
            graph_result = self.impact.build_graph(workspace_path)
            dep_map = self.impact.get_dependency_map(workspace_path)
            report.impact = {
                'graph': graph_result,
                'dependency_map': dep_map,
            }
        except Exception as e:
            report.impact = {'error': str(e)}

        # Calculate overall risk
        report.overall_risk_score = self._calculate_overall_risk(report)
        report.overall_risk_level = self._risk_level(report.overall_risk_score)

        # Sort issues by severity
        severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3, 'INFO': 4}
        report.issues.sort(key=lambda x: severity_order.get(x.get('severity', 'INFO'), 5))

        return asdict(report)

    def on_file_change(self, workspace_path: str, file_path: str,
                       old_content: str = "", new_content: str = "") -> Dict[str, Any]:
        """Run targeted enforcement checks when a file changes.
        
        This is the incremental check — only runs relevant validations
        based on what kind of file changed. Used for real-time feedback.
        """
        report = RiskReport(
            workspace_path=workspace_path,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        file_ext = Path(file_path).suffix.lower()
        file_name = Path(file_path).name.lower()

        # Always run security scan on changed file
        try:
            security_result = self.security.scan_file(file_path)
            # scan_file() returns a list of finding dicts
            report.security = {'findings': security_result, 'total_issues': len(security_result)}
            report.security_findings = len(security_result)
            for finding in security_result:
                report.issues.append({
                    'pillar': 'security',
                    'severity': finding.get('severity', 'MEDIUM'),
                    'category': finding.get('category', 'security'),
                    'message': finding.get('issue', ''),
                    'file_path': finding.get('file', file_path),
                    'line_number': finding.get('line', 0),
                })
        except Exception as e:
            report.security = {'error': str(e)}

        # Always run impact analysis
        try:
            impact_result = self.impact.analyze_change(
                workspace_path, file_path, old_content, new_content
            )
            report.impact = impact_result
            report.impact_radius = len(impact_result.get('affected_files', []))
            for bc in impact_result.get('breaking_changes', []):
                report.issues.append({
                    'pillar': 'impact',
                    'severity': 'CRITICAL',
                    'category': 'breaking_change',
                    'message': bc,
                    'file_path': file_path,
                })
            for w in impact_result.get('warnings', []):
                report.issues.append({
                    'pillar': 'impact',
                    'severity': 'MEDIUM',
                    'category': 'warning',
                    'message': w,
                    'file_path': file_path,
                })
        except Exception as e:
            report.impact = {'error': str(e)}

        # Prisma-related file changed?
        if file_name == 'schema.prisma' or 'prisma' in file_path.lower():
            try:
                prisma_result = self.prisma.analyze_workspace(workspace_path)
                report.prisma = prisma_result
                report.prisma_issues = prisma_result.get('total_issues', 0)
                for issue in prisma_result.get('issues', []):
                    report.issues.append({'pillar': 'prisma', **issue})
            except Exception as e:
                report.prisma = {'error': str(e)}

        # DTO file changed?
        if any(kw in file_name for kw in ['dto', 'schema', 'input', 'output', 'request', 'response', 'validator']):
            try:
                dto_result = self.prisma.validate_dto(workspace_path, file_path)
                report.prisma = dto_result
                report.prisma_issues = len(dto_result.get('issues', []))
                for issue in dto_result.get('issues', []):
                    report.issues.append({'pillar': 'prisma', **issue})
            except Exception as e:
                pass

        # Route/controller file changed?
        if any(kw in file_name for kw in ['route', 'controller', 'handler', 'endpoint', 'view', 'api']):
            try:
                contract_result = self.contracts.analyze_workspace(workspace_path)
                report.contracts = contract_result
                report.contract_violations = contract_result.get('total_violations', 0)
                for violation in contract_result.get('violations', []):
                    report.issues.append({'pillar': 'contracts', **violation})
            except Exception as e:
                report.contracts = {'error': str(e)}

        # Service/model files — check Prisma include/select usage
        if file_ext in ('.ts', '.tsx', '.js', '.jsx'):
            try:
                include_result = self.prisma.check_include_select(workspace_path, file_path)
                if include_result.get('issues'):
                    for issue in include_result['issues']:
                        report.issues.append({'pillar': 'prisma', **issue})
            except Exception as e:
                pass

        # Calculate risk
        report.overall_risk_score = self._calculate_overall_risk(report)
        report.overall_risk_level = self._risk_level(report.overall_risk_score)

        # Sort
        severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3, 'INFO': 4}
        report.issues.sort(key=lambda x: severity_order.get(x.get('severity', 'INFO'), 5))

        return asdict(report)

    def validate_before_commit(self, workspace_path: str, changed_files: List[str]) -> Dict[str, Any]:
        """Pre-commit validation — checks all changed files for issues.
        
        Intended to be run before git commit to catch problems.
        """
        report = RiskReport(
            workspace_path=workspace_path,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        # Multi-file impact analysis
        try:
            impact_result = self.impact.analyze_multiple_changes(workspace_path, changed_files)
            report.impact = impact_result
            report.impact_radius = impact_result.get('total_affected', 0)
            for bc in impact_result.get('breaking_changes', []):
                report.issues.append({
                    'pillar': 'impact',
                    'severity': 'CRITICAL',
                    'category': 'breaking_change',
                    'message': bc,
                })
        except Exception as e:
            report.impact = {'error': str(e)}

        # Security scan all changed files
        for f in changed_files:
            try:
                sec = self.security.scan_file(f)
                for finding in sec.get('findings', []):
                    report.issues.append({
                        'pillar': 'security',
                        'severity': finding.get('severity', 'MEDIUM'),
                        'category': finding.get('category', 'security'),
                        'message': finding.get('description', ''),
                        'file_path': finding.get('file', f),
                        'line_number': finding.get('line', 0),
                    })
                    report.security_findings += 1
            except Exception:
                pass

        # Prisma check if any schema/dto changed
        prisma_files = [f for f in changed_files if 'prisma' in f.lower() or 'schema' in f.lower() or 'dto' in f.lower()]
        if prisma_files:
            try:
                prisma_result = self.prisma.analyze_workspace(workspace_path)
                report.prisma = prisma_result
                report.prisma_issues = prisma_result.get('total_issues', 0)
                for issue in prisma_result.get('issues', []):
                    report.issues.append({'pillar': 'prisma', **issue})
            except Exception:
                pass

        # Contract check if any route/controller changed
        route_files = [f for f in changed_files if any(kw in f.lower() for kw in ['route', 'controller', 'handler', 'endpoint'])]
        if route_files:
            try:
                contract_result = self.contracts.analyze_workspace(workspace_path)
                report.contracts = contract_result
                report.contract_violations = contract_result.get('total_violations', 0)
                for violation in contract_result.get('violations', []):
                    report.issues.append({'pillar': 'contracts', **violation})
            except Exception:
                pass

        # Calculate risk
        report.overall_risk_score = self._calculate_overall_risk(report)
        report.overall_risk_level = self._risk_level(report.overall_risk_score)

        # Decision
        critical_count = sum(1 for i in report.issues if i.get('severity') == 'CRITICAL')
        high_count = sum(1 for i in report.issues if i.get('severity') == 'HIGH')

        severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3, 'INFO': 4}
        report.issues.sort(key=lambda x: severity_order.get(x.get('severity', 'INFO'), 5))

        result = asdict(report)
        result['commit_safe'] = critical_count == 0
        result['commit_warning'] = high_count > 0
        result['summary'] = (
            f'{critical_count} critical, {high_count} high severity issues. '
            f'{"BLOCK COMMIT" if critical_count > 0 else "PROCEED WITH CAUTION" if high_count > 0 else "SAFE TO COMMIT"}'
        )

        return result

    def _calculate_overall_risk(self, report: RiskReport) -> float:
        """Calculate combined risk score."""
        scores = []

        # Severity weights
        severity_score = {'CRITICAL': 1.0, 'HIGH': 0.7, 'MEDIUM': 0.4, 'LOW': 0.1, 'INFO': 0.0}

        for issue in report.issues:
            scores.append(severity_score.get(issue.get('severity', 'INFO'), 0.0))

        if not scores:
            return 0.0

        # Weighted: max severity + average of all
        max_score = max(scores)
        avg_score = sum(scores) / len(scores)

        return round(max_score * 0.7 + avg_score * 0.3, 2)

    def _risk_level(self, score: float) -> str:
        if score >= 0.8:
            return 'CRITICAL'
        elif score >= 0.6:
            return 'HIGH'
        elif score >= 0.4:
            return 'MEDIUM'
        return 'LOW'


# ──────────────────────────────────────────────────────────────
# Stack Detection (bonus)
# ──────────────────────────────────────────────────────────────

class StackDetector:
    """Detects project tech stack from config files."""

    def detect(self, workspace_path: str) -> Dict[str, Any]:
        """Detect project stack from config files."""
        root = Path(workspace_path)
        stack = {
            'language': None,
            'framework': None,
            'orm': None,
            'auth': None,
            'test': None,
            'database': None,
            'package_manager': None,
            'detected_tools': [],
        }

        # ── Node.js / TypeScript ──
        pkg_json = root / 'package.json'
        if pkg_json.exists():
            try:
                pkg = json.loads(pkg_json.read_text(encoding='utf-8'))
                all_deps = {}
                all_deps.update(pkg.get('dependencies', {}))
                all_deps.update(pkg.get('devDependencies', {}))

                stack['language'] = 'typescript' if 'typescript' in all_deps else 'javascript'

                # Framework
                for fw, name in [
                    ('next', 'Next.js'), ('@nestjs/core', 'NestJS'),
                    ('express', 'Express'), ('fastify', 'Fastify'),
                    ('koa', 'Koa'), ('hapi', 'Hapi'), ('nuxt', 'Nuxt'),
                    ('svelte', 'Svelte'), ('react', 'React'), ('vue', 'Vue'),
                    ('angular', 'Angular'),
                ]:
                    if fw in all_deps or f'@{fw}' in all_deps:
                        stack['framework'] = name
                        break

                # ORM
                for orm, name in [
                    ('prisma', 'Prisma'), ('@prisma/client', 'Prisma'),
                    ('typeorm', 'TypeORM'), ('sequelize', 'Sequelize'),
                    ('drizzle-orm', 'Drizzle'), ('mongoose', 'Mongoose'),
                    ('knex', 'Knex'),
                ]:
                    if orm in all_deps:
                        stack['orm'] = name
                        stack['detected_tools'].append(name)
                        break

                # Auth
                for auth, name in [
                    ('next-auth', 'NextAuth'), ('@auth/core', 'Auth.js'),
                    ('passport', 'Passport'), ('jsonwebtoken', 'JWT'),
                    ('@clerk/nextjs', 'Clerk'), ('lucia', 'Lucia'),
                    ('supertokens-node', 'SuperTokens'),
                ]:
                    if auth in all_deps:
                        stack['auth'] = name
                        stack['detected_tools'].append(name)
                        break

                # Test
                for test, name in [
                    ('jest', 'Jest'), ('vitest', 'Vitest'),
                    ('mocha', 'Mocha'), ('@playwright/test', 'Playwright'),
                    ('cypress', 'Cypress'),
                ]:
                    if test in all_deps:
                        stack['test'] = name
                        stack['detected_tools'].append(name)
                        break

                # Package manager
                if (root / 'pnpm-lock.yaml').exists():
                    stack['package_manager'] = 'pnpm'
                elif (root / 'yarn.lock').exists():
                    stack['package_manager'] = 'yarn'
                elif (root / 'bun.lockb').exists():
                    stack['package_manager'] = 'bun'
                else:
                    stack['package_manager'] = 'npm'

            except Exception:
                pass

        # ── Python ──
        req_txt = root / 'requirements.txt'
        pyproject = root / 'pyproject.toml'

        if req_txt.exists() or pyproject.exists():
            stack['language'] = stack['language'] or 'python'

            deps_text = ""
            if req_txt.exists():
                deps_text = req_txt.read_text(encoding='utf-8', errors='ignore').lower()
            if pyproject.exists():
                deps_text += pyproject.read_text(encoding='utf-8', errors='ignore').lower()

            for fw, name in [
                ('fastapi', 'FastAPI'), ('django', 'Django'),
                ('flask', 'Flask'), ('starlette', 'Starlette'),
            ]:
                if fw in deps_text:
                    stack['framework'] = stack['framework'] or name
                    break

            for orm, name in [
                ('sqlalchemy', 'SQLAlchemy'), ('tortoise', 'Tortoise'),
                ('django', 'Django ORM'), ('peewee', 'Peewee'),
                ('prisma', 'Prisma'),
            ]:
                if orm in deps_text:
                    stack['orm'] = stack['orm'] or name
                    stack['detected_tools'].append(name)
                    break

        # ── Go ──
        go_mod = root / 'go.mod'
        if go_mod.exists():
            stack['language'] = stack['language'] or 'go'
            mod_content = go_mod.read_text(encoding='utf-8', errors='ignore')
            if 'gin-gonic' in mod_content:
                stack['framework'] = 'Gin'
            elif 'labstack/echo' in mod_content:
                stack['framework'] = 'Echo'
            elif 'gorilla/mux' in mod_content:
                stack['framework'] = 'Gorilla Mux'

        # ── Database from config ──
        env_file = root / '.env'
        if env_file.exists():
            try:
                env_content = env_file.read_text(encoding='utf-8', errors='ignore')
                if 'postgres' in env_content.lower():
                    stack['database'] = 'PostgreSQL'
                elif 'mysql' in env_content.lower():
                    stack['database'] = 'MySQL'
                elif 'mongodb' in env_content.lower() or 'mongo' in env_content.lower():
                    stack['database'] = 'MongoDB'
                elif 'sqlite' in env_content.lower():
                    stack['database'] = 'SQLite'
            except Exception:
                pass

        return stack


# Global singleton
pipeline = ValidationPipeline()
stack_detector = StackDetector()
