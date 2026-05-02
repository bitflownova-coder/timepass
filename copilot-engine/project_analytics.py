"""
Project Analytics — workspace-level statistics, LOC counts,
language breakdowns, and cross-project health scoring.
"""
import os
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from collections import Counter, defaultdict

logger = logging.getLogger(__name__)

# Extensions → language mapping
_EXT_MAP: Dict[str, str] = {
    ".py": "Python", ".pyi": "Python",
    ".js": "JavaScript", ".mjs": "JavaScript", ".cjs": "JavaScript",
    ".ts": "TypeScript", ".tsx": "TypeScript", ".jsx": "JavaScript",
    ".kt": "Kotlin", ".kts": "Kotlin",
    ".java": "Java",
    ".go": "Go",
    ".rs": "Rust",
    ".c": "C", ".h": "C",
    ".cpp": "C++", ".cxx": "C++", ".hpp": "C++",
    ".cs": "C#",
    ".rb": "Ruby",
    ".php": "PHP",
    ".swift": "Swift",
    ".dart": "Dart",
    ".sql": "SQL",
    ".html": "HTML", ".htm": "HTML",
    ".css": "CSS", ".scss": "SCSS", ".less": "LESS",
    ".json": "JSON",
    ".yaml": "YAML", ".yml": "YAML",
    ".md": "Markdown",
    ".xml": "XML",
    ".sh": "Shell", ".bash": "Shell", ".zsh": "Shell",
    ".ps1": "PowerShell",
    ".bat": "Batch", ".cmd": "Batch",
    ".toml": "TOML",
    ".ini": "INI",
    ".cfg": "Config",
    ".env": "DotEnv",
    ".gradle": "Gradle",
    ".tf": "Terraform",
    ".dockerfile": "Docker",
    ".proto": "Protobuf",
    ".graphql": "GraphQL", ".gql": "GraphQL",
    ".vue": "Vue",
    ".svelte": "Svelte",
    ".r": "R",
    ".lua": "Lua",
    ".ex": "Elixir", ".exs": "Elixir",
}

# Directories to always skip
_SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv", "env",
    ".idea", ".vscode", ".gradle", "build", "dist", "target",
    ".next", ".nuxt", "coverage", ".mypy_cache", ".pytest_cache",
    "dist-electron", ".svelte-kit", "out",
}

# Binary/generated extensions to skip
_SKIP_EXTS = {
    ".pyc", ".pyo", ".class", ".o", ".obj", ".exe", ".dll", ".so",
    ".dylib", ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico",
    ".svg", ".woff", ".woff2", ".ttf", ".eot", ".mp3", ".mp4",
    ".zip", ".tar", ".gz", ".rar", ".7z", ".jar", ".war",
    ".lock", ".map", ".min.js", ".min.css",
    ".db", ".sqlite", ".sqlite3",
}


def analyze_workspace(workspace_path: str) -> Dict[str, Any]:
    """
    Analyze a workspace directory and return comprehensive statistics:
    file counts, LOC, language breakdown, largest files, directory structure.
    """
    root = Path(workspace_path)
    if not root.is_dir():
        return {"error": f"Not a directory: {workspace_path}"}

    start = time.time()

    lang_stats: Dict[str, Dict[str, int]] = defaultdict(lambda: {"files": 0, "lines": 0, "bytes": 0})
    total_files = 0
    total_lines = 0
    total_bytes = 0
    largest_files: List[Dict[str, Any]] = []
    dir_count = 0

    for dirpath, dirnames, filenames in os.walk(root):
        # Skip excluded directories
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS and not d.startswith(".")]
        dir_count += 1

        for fname in filenames:
            fpath = Path(dirpath) / fname
            ext = fpath.suffix.lower()

            if ext in _SKIP_EXTS:
                continue
            if fname.lower() == "dockerfile":
                ext = ".dockerfile"

            try:
                size = fpath.stat().st_size
            except OSError:
                continue

            # Skip huge files (>2MB — likely generated)
            if size > 2_000_000:
                continue

            total_files += 1
            total_bytes += size
            lang = _EXT_MAP.get(ext, "Other")

            # Count lines for text files
            lines = 0
            if ext not in {".json", ".xml"} and lang != "Other":
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        lines = sum(1 for _ in f)
                except Exception:
                    pass

            total_lines += lines

            lang_stats[lang]["files"] += 1
            lang_stats[lang]["lines"] += lines
            lang_stats[lang]["bytes"] += size

            rel = str(fpath.relative_to(root))
            largest_files.append({"path": rel, "size": size, "lines": lines, "language": lang})

    # Sort largest files
    largest_files.sort(key=lambda f: f["lines"], reverse=True)

    # Build language breakdown sorted by LOC
    lang_breakdown = [
        {"language": lang, **stats}
        for lang, stats in sorted(lang_stats.items(), key=lambda x: x[1]["lines"], reverse=True)
    ]

    elapsed = round(time.time() - start, 3)

    return {
        "workspace": workspace_path,
        "total_files": total_files,
        "total_lines": total_lines,
        "total_bytes": total_bytes,
        "directories": dir_count,
        "languages": lang_breakdown,
        "largest_files": largest_files[:25],
        "analysis_time_seconds": elapsed,
    }


def get_workspace_health_score(
    workspace_path: str,
    risk_score: Optional[float] = None,
    security_issues: int = 0,
    contract_violations: int = 0,
    drift_events: int = 0,
) -> Dict[str, Any]:
    """
    Compute a composite project health score 0-100 using available metrics.
    Higher is better.
    """
    score = 100.0
    breakdown: Dict[str, Dict[str, Any]] = {}

    # Risk penalty (0-10 scale → 0-30 penalty)
    if risk_score is not None:
        risk_penalty = min(risk_score * 3, 30)
        score -= risk_penalty
        breakdown["risk"] = {
            "raw_score": risk_score,
            "penalty": round(risk_penalty, 1),
            "status": "good" if risk_score < 3 else "warning" if risk_score < 6 else "critical",
        }

    # Security penalty (each issue = -2, max -20)
    sec_penalty = min(security_issues * 2, 20)
    score -= sec_penalty
    breakdown["security"] = {
        "issues": security_issues,
        "penalty": sec_penalty,
        "status": "good" if security_issues == 0 else "warning" if security_issues < 5 else "critical",
    }

    # Contract violations (-3 each, max -15)
    contract_penalty = min(contract_violations * 3, 15)
    score -= contract_penalty
    breakdown["contracts"] = {
        "violations": contract_violations,
        "penalty": contract_penalty,
        "status": "good" if contract_violations == 0 else "warning" if contract_violations < 3 else "critical",
    }

    # Drift (-4 each, max -20)
    drift_penalty = min(drift_events * 4, 20)
    score -= drift_penalty
    breakdown["drift"] = {
        "events": drift_events,
        "penalty": drift_penalty,
        "status": "good" if drift_events == 0 else "warning" if drift_events < 3 else "critical",
    }

    # Workspace exists and has files bonus
    ws_stats = analyze_workspace(workspace_path)
    has_files = ws_stats.get("total_files", 0) > 0
    if not has_files:
        score -= 15
        breakdown["structure"] = {"status": "critical", "penalty": 15, "note": "No source files found"}
    else:
        breakdown["structure"] = {"status": "good", "penalty": 0, "total_files": ws_stats["total_files"]}

    final_score = max(0, min(100, round(score)))
    health_level = (
        "EXCELLENT" if final_score >= 90 else
        "GOOD" if final_score >= 70 else
        "FAIR" if final_score >= 50 else
        "POOR" if final_score >= 30 else
        "CRITICAL"
    )

    return {
        "workspace": workspace_path,
        "score": final_score,
        "health_level": health_level,
        "breakdown": breakdown,
    }


def compare_workspaces(workspace_paths: List[str]) -> List[Dict[str, Any]]:
    """Analyze and compare multiple workspaces side by side."""
    results = []
    for ws in workspace_paths:
        try:
            stats = analyze_workspace(ws)
            results.append(stats)
        except Exception as e:
            results.append({"workspace": ws, "error": str(e)})
    return results
