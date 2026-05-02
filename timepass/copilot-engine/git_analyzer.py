"""
Copilot Engine - Git Analyzer
Provides git diff analysis, change risk scoring, commit correlation,
and root cause analysis for errors.
"""
import os
import re
import subprocess
from datetime import datetime, timedelta, timezone
from typing import Optional
from pathlib import Path


class GitAnalyzer:
    """Analyzes git history, diffs, and correlates errors with recent changes."""

    # Files that are inherently higher risk when changed
    HIGH_RISK_PATTERNS = [
        r'requirements\.txt$', r'package\.json$', r'Cargo\.toml$',
        r'go\.mod$', r'build\.gradle', r'pom\.xml$',
        r'Dockerfile$', r'docker-compose',
        r'\.env$', r'config\.(py|js|ts|yaml|yml|json)$',
        r'settings\.(py|js|ts)$', r'migrations?/',
        r'schema\.(py|ts|sql)$', r'auth', r'security',
    ]

    # Patterns indicating dangerous operations
    DANGEROUS_PATTERNS = [
        (r'eval\s*\(', 'eval() usage added'),
        (r'exec\s*\(', 'exec() usage added'),
        (r'DROP\s+TABLE', 'DROP TABLE statement added'),
        (r'DELETE\s+FROM.*WHERE\s*$', 'DELETE without WHERE clause'),
        (r'password\s*=\s*["\']', 'Hardcoded password added'),
        (r'api_key\s*=\s*["\']', 'Hardcoded API key added'),
        (r'\.env', 'Environment file modified'),
        (r'TODO|FIXME|HACK|XXX', 'Technical debt marker added'),
    ]

    def __init__(self):
        pass

    def is_git_repo(self, workspace_path: str) -> bool:
        """Check if path is inside a git repository."""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--git-dir'],
                cwd=workspace_path, capture_output=True, text=True, timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    def get_current_branch(self, workspace_path: str) -> Optional[str]:
        """Get current git branch name."""
        try:
            result = subprocess.run(
                ['git', 'branch', '--show-current'],
                cwd=workspace_path, capture_output=True, text=True, timeout=5
            )
            return result.stdout.strip() if result.returncode == 0 else None
        except Exception:
            return None

    def get_recent_commits(self, workspace_path: str, limit: int = 20) -> list[dict]:
        """Get recent commits with details."""
        try:
            result = subprocess.run(
                ['git', 'log', f'-{limit}', '--pretty=format:%H||%an||%ae||%at||%s'],
                cwd=workspace_path, capture_output=True, text=True, timeout=10
            )
            if result.returncode != 0:
                return []

            commits = []
            for line in result.stdout.strip().split('\n'):
                if not line.strip():
                    continue
                parts = line.split('||')
                if len(parts) >= 5:
                    commits.append({
                        'hash': parts[0],
                        'author_name': parts[1],
                        'author_email': parts[2],
                        'timestamp': int(parts[3]),
                        'message': parts[4],
                        'time_ago': self._time_ago(int(parts[3])),
                    })
            return commits
        except Exception:
            return []

    def get_diff(self, workspace_path: str, staged: bool = False) -> str:
        """Get current diff (staged or unstaged)."""
        try:
            cmd = ['git', 'diff']
            if staged:
                cmd.append('--staged')
            result = subprocess.run(
                cmd, cwd=workspace_path, capture_output=True, text=True, timeout=15
            )
            return result.stdout if result.returncode == 0 else ''
        except Exception:
            return ''

    def get_changed_files(self, workspace_path: str) -> list[dict]:
        """Get list of changed files with their status."""
        try:
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=workspace_path, capture_output=True, text=True, timeout=10
            )
            if result.returncode != 0:
                return []

            files = []
            for line in result.stdout.strip().split('\n'):
                if not line.strip():
                    continue
                status_code = line[:2].strip()
                file_path = line[3:].strip()

                status_map = {
                    'M': 'modified', 'A': 'added', 'D': 'deleted',
                    'R': 'renamed', 'C': 'copied', '??': 'untracked',
                    'UU': 'conflict',
                }
                status = status_map.get(status_code, 'unknown')
                files.append({
                    'file': file_path,
                    'status': status,
                    'status_code': status_code,
                })
            return files
        except Exception:
            return []

    def analyze_diff(self, workspace_path: str) -> dict:
        """Full diff analysis with risk scoring."""
        if not self.is_git_repo(workspace_path):
            return {'error': 'Not a git repository', 'changes': [], 'risk_score': 0, 'warnings': []}

        changed_files = self.get_changed_files(workspace_path)
        diff_text = self.get_diff(workspace_path) or ''
        staged_diff = self.get_diff(workspace_path, staged=True) or ''
        full_diff = diff_text + '\n' + staged_diff

        changes = []
        risk_score = 0
        warnings = []

        for cf in changed_files:
            file_risk = self._assess_file_risk(cf['file'], full_diff)
            changes.append({
                'file': cf['file'],
                'change_type': cf['status'],
                'risk_level': file_risk['level'],
                'details': file_risk['reason'],
            })
            risk_score = max(risk_score, file_risk['score'])
            warnings.extend(file_risk['warnings'])

        # Check for dangerous patterns in diff
        for pattern, desc in self.DANGEROUS_PATTERNS:
            added_lines = [l for l in full_diff.split('\n') if l.startswith('+') and not l.startswith('+++')]
            for line in added_lines:
                if re.search(pattern, line, re.IGNORECASE):
                    warnings.append(f'{desc}: {line[1:].strip()[:80]}')
                    risk_score = min(10, risk_score + 2)

        # Large change set = higher risk
        if len(changed_files) > 10:
            warnings.append(f'Large changeset: {len(changed_files)} files modified')
            risk_score = min(10, risk_score + 1)

        return {
            'workspace': workspace_path,
            'branch': self.get_current_branch(workspace_path),
            'changes': changes,
            'risk_score': min(10, risk_score),
            'warnings': list(set(warnings)),
            'total_files_changed': len(changed_files),
        }

    def analyze_change_risk(self, workspace_path: str, file_path: str) -> dict:
        """Analyze risk of a specific file change."""
        if not self.is_git_repo(workspace_path):
            return {'risk_level': 'unknown', 'warnings': []}

        try:
            # Get diff for this file
            rel_path = os.path.relpath(file_path, workspace_path)
            result = subprocess.run(
                ['git', 'diff', '--', rel_path],
                cwd=workspace_path, capture_output=True, text=True, timeout=10
            )
            diff_text = result.stdout

            risk = self._assess_file_risk(rel_path, diff_text)

            # Count lines changed
            added = len([l for l in diff_text.split('\n') if l.startswith('+') and not l.startswith('+++')])
            removed = len([l for l in diff_text.split('\n') if l.startswith('-') and not l.startswith('---')])

            return {
                'file': rel_path,
                'risk_level': risk['level'],
                'risk_score': risk['score'],
                'warnings': risk['warnings'],
                'lines_added': added,
                'lines_removed': removed,
            }
        except Exception as e:
            return {'risk_level': 'unknown', 'error': str(e), 'warnings': []}

    def correlate_error_with_changes(self, workspace_path: str, error_text: str) -> dict:
        """Try to correlate an error with recent git changes."""
        if not self.is_git_repo(workspace_path):
            return {'likely_cause': None, 'changed_file': None}

        # Extract file path from error
        file_matches = re.findall(r'(?:File\s+["\']|at\s+|in\s+)([^"\':\s]+\.\w+)', error_text)
        error_keywords = re.findall(r'\b([A-Z]\w+Error|Exception|Warning)\b', error_text)

        # Get recent changes
        changed_files = self.get_changed_files(workspace_path)
        recent_commits = self.get_recent_commits(workspace_path, limit=10)

        best_match = None
        best_score = 0

        for cf in changed_files:
            score = 0
            reasons = []

            # Direct file match
            for fm in file_matches:
                if fm in cf['file'] or cf['file'] in fm:
                    score += 5
                    reasons.append(f"Error references {fm}, which was recently {cf['status']}")

            # Same directory match
            for fm in file_matches:
                if os.path.dirname(fm) == os.path.dirname(cf['file']):
                    score += 2
                    reasons.append(f"Changed file is in same directory as error source")

            # Import/dependency match
            if cf['file'].endswith(('.txt', '.toml', '.json', '.lock')):
                score += 1
                reasons.append("Dependency file was modified")

            if score > best_score:
                best_score = score
                best_match = {
                    'likely_cause': '; '.join(reasons) if reasons else None,
                    'changed_file': cf['file'],
                    'change_type': cf['status'],
                    'confidence': min(1.0, score / 5),
                }

        # Also check recent commits
        commit_match = None
        for commit in recent_commits:
            for keyword in error_keywords:
                if keyword.lower() in commit['message'].lower():
                    commit_match = {
                        'hash': commit['hash'],
                        'message': commit['message'],
                        'time_ago': commit['time_ago'],
                    }
                    break

        result = best_match or {'likely_cause': None, 'changed_file': None}
        if commit_match:
            result['commit'] = commit_match
            result['time_ago'] = commit_match['time_ago']

        return result

    def _assess_file_risk(self, file_path: str, diff_text: str) -> dict:
        """Assess risk level of a file change."""
        score = 0
        warnings = []

        # Check if file matches high-risk patterns
        for pattern in self.HIGH_RISK_PATTERNS:
            if re.search(pattern, file_path, re.IGNORECASE):
                score += 3
                warnings.append(f'High-risk file pattern: {file_path}')
                break

        # Count change size in this file
        file_diff_lines = diff_text.split('\n')
        added = sum(1 for l in file_diff_lines if l.startswith('+') and not l.startswith('+++'))
        removed = sum(1 for l in file_diff_lines if l.startswith('-') and not l.startswith('---'))
        total_changes = added + removed

        if total_changes > 100:
            score += 3
            warnings.append(f'Large change: {total_changes} lines modified')
        elif total_changes > 50:
            score += 2
        elif total_changes > 20:
            score += 1

        level = 'low'
        if score >= 5:
            level = 'high'
        elif score >= 3:
            level = 'medium'

        return {
            'level': level,
            'score': score,
            'reason': f'{total_changes} lines changed',
            'warnings': warnings,
        }

    def _time_ago(self, timestamp: int) -> str:
        """Convert unix timestamp to human-readable time ago."""
        now = datetime.now(timezone.utc)
        then = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        diff = now - then

        if diff.days > 30:
            return f'{diff.days // 30} months ago'
        elif diff.days > 0:
            return f'{diff.days} days ago'
        elif diff.seconds > 3600:
            return f'{diff.seconds // 3600} hours ago'
        elif diff.seconds > 60:
            return f'{diff.seconds // 60} minutes ago'
        else:
            return 'just now'
