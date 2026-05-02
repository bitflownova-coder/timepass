"""
Integration tests for Copilot Engine - Server API
Run with: pytest tests/test_api.py -v
"""
import os
import sys
import tempfile
import shutil
import pytest
from pathlib import Path

# Ensure engine modules are importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient
from server import app


@pytest.fixture(scope="module")
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture(scope="module")
def workspace_dir():
    """Create a temporary workspace with sample files."""
    tmpdir = tempfile.mkdtemp(prefix="copilot_test_")
    # Create some sample files
    Path(tmpdir, "main.py").write_text(
        'def greet(name):\n    return f"Hello {name}"\n\nif __name__ == "__main__":\n    greet("world")\n'
    )
    Path(tmpdir, "utils.py").write_text(
        'import os\n\ndef get_path():\n    return os.getcwd()\n'
    )
    Path(tmpdir, "requirements.txt").write_text("fastapi\nuvicorn\n")
    yield tmpdir
    shutil.rmtree(tmpdir, ignore_errors=True)


# ──────────────────────────────────────────────────────────────
# Health & Status
# ──────────────────────────────────────────────────────────────

class TestHealth:
    def test_root(self, client):
        r = client.get("/")
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "Copilot Engine"
        assert "version" in data

    def test_health(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "healthy"
        assert "uptime" in data

    def test_cache_stats(self, client):
        r = client.get("/cache/stats")
        assert r.status_code == 200
        data = r.json()
        assert "response" in data
        assert "hits" in data["response"]

    def test_cache_clear(self, client):
        r = client.post("/cache/clear")
        assert r.status_code == 200
        assert r.json()["status"] == "cleared"


# ──────────────────────────────────────────────────────────────
# Workspace Management
# ──────────────────────────────────────────────────────────────

class TestWorkspaces:
    def test_register_workspace(self, client, workspace_dir):
        r = client.post("/workspace/register", json={"path": workspace_dir})
        assert r.status_code == 200
        data = r.json()
        assert data["path"] == workspace_dir
        assert data["id"] is not None

    def test_register_invalid_path(self, client):
        r = client.post("/workspace/register", json={"path": "/nonexistent/path/12345"})
        assert r.status_code == 400

    def test_list_workspaces(self, client, workspace_dir):
        # Register first
        client.post("/workspace/register", json={"path": workspace_dir})
        r = client.get("/workspaces")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        paths = [ws["path"] for ws in data]
        assert workspace_dir in paths

    def test_re_register_updates(self, client, workspace_dir):
        """Re-registering same workspace should update, not duplicate."""
        r1 = client.post("/workspace/register", json={"path": workspace_dir})
        r2 = client.post("/workspace/register", json={"path": workspace_dir})
        assert r1.json()["id"] == r2.json()["id"]


# ──────────────────────────────────────────────────────────────
# Error Analysis
# ──────────────────────────────────────────────────────────────

class TestErrors:
    def test_parse_python_error(self, client):
        r = client.post("/error/parse", json={
            "error_text": """Traceback (most recent call last):
  File "app.py", line 10, in main
    x = data["missing"]
KeyError: 'missing'"""
        })
        assert r.status_code == 200
        data = r.json()
        assert data["error_type"] == "KeyError"
        assert data["language"] == "python"
        assert len(data["suggestions"]) > 0

    def test_parse_js_error(self, client):
        r = client.post("/error/parse", json={
            "error_text": "TypeError: Cannot read properties of null (reading 'length')"
        })
        assert r.status_code == 200
        assert r.json()["error_type"] in ("TypeError", "Error")

    def test_find_similar(self, client):
        r = client.post("/error/find-similar", json={
            "error_text": "KeyError: 'name'"
        })
        assert r.status_code == 200
        data = r.json()
        assert "current_error" in data
        assert "similar_fixes" in data


# ──────────────────────────────────────────────────────────────
# Context Building
# ──────────────────────────────────────────────────────────────

class TestContext:
    def test_build_context(self, client, workspace_dir):
        r = client.post("/context/build", json={
            "workspace_path": workspace_dir,
            "task": "Fix the bug",
        })
        assert r.status_code == 200
        data = r.json()
        assert "prompt" in data
        assert data["token_estimate"] > 0

    def test_build_debug_context(self, client, workspace_dir):
        r = client.post("/context/debug", json={
            "error_text": "KeyError: 'name'",
            "workspace_path": workspace_dir,
        })
        assert r.status_code == 200
        data = r.json()
        assert "prompt" in data

    def test_debug_context_requires_workspace(self, client):
        r = client.post("/context/debug", json={
            "error_text": "SomeError"
        })
        assert r.status_code == 400


# ──────────────────────────────────────────────────────────────
# Git Analysis
# ──────────────────────────────────────────────────────────────

class TestGit:
    def test_diff_non_repo(self, client, workspace_dir):
        r = client.post("/git/diff", json={"workspace_path": workspace_dir})
        assert r.status_code == 200
        # Non-git dir returns empty or error in data, but 200

    def test_branch(self, client, workspace_dir):
        r = client.get(f"/git/branch/{workspace_dir}")
        assert r.status_code == 200
        data = r.json()
        assert "branch" in data

    def test_changed_files(self, client, workspace_dir):
        r = client.get(f"/git/changed-files/{workspace_dir}")
        assert r.status_code == 200


# ──────────────────────────────────────────────────────────────
# Security
# ──────────────────────────────────────────────────────────────

class TestSecurity:
    def test_scan_file(self, client, workspace_dir):
        # Create a file with a vuln
        vuln_file = os.path.join(workspace_dir, "vuln.py")
        Path(vuln_file).write_text('result = eval(user_input)\n')
        r = client.post("/security/scan", json={"file_path": vuln_file})
        assert r.status_code == 200

    def test_scan_workspace(self, client, workspace_dir):
        r = client.post("/security/scan-workspace", json={"workspace_path": workspace_dir})
        assert r.status_code == 200
        data = r.json()
        assert "total_findings" in data or "files_scanned" in data


# ──────────────────────────────────────────────────────────────
# SQL
# ──────────────────────────────────────────────────────────────

class TestSQL:
    def test_analyze_select(self, client):
        r = client.post("/sql/analyze", json={
            "query": "SELECT id, name FROM users WHERE active = 1"
        })
        assert r.status_code == 200
        data = r.json()
        assert data["query_type"] == "SELECT"

    def test_validate_good(self, client):
        r = client.post("/sql/validate", json={
            "query": "SELECT a FROM t WHERE b = 1"
        })
        assert r.status_code == 200
        assert r.json()["valid"] is True

    def test_validate_bad(self, client):
        r = client.post("/sql/validate", json={
            "query": "SELECT (a FROM t"
        })
        assert r.status_code == 200
        assert r.json()["valid"] is False


# ──────────────────────────────────────────────────────────────
# API Detection
# ──────────────────────────────────────────────────────────────

class TestAPIDetection:
    def test_detect_endpoints(self, client, workspace_dir):
        # Write a Flask file
        Path(workspace_dir, "api.py").write_text(
            "from flask import Flask\napp = Flask(__name__)\n"
            "@app.route('/test', methods=['GET'])\ndef test(): pass\n"
        )
        r = client.post("/api/detect", json={"workspace_path": workspace_dir})
        assert r.status_code == 200
        data = r.json()
        assert "total_endpoints" in data

    def test_validate_api_call(self, client, workspace_dir):
        r = client.post("/api/validate", json={
            "workspace_path": workspace_dir,
            "method": "GET",
            "route": "/test"
        })
        assert r.status_code == 200


# ──────────────────────────────────────────────────────────────
# Behavior
# ──────────────────────────────────────────────────────────────

class TestBehavior:
    def test_track_event(self, client):
        r = client.post("/behavior/track", json={
            "workspace_path": "/test/ws",
            "event": "error",
            "data": {"error_type": "TypeError"}
        })
        assert r.status_code == 200

    def test_get_status(self, client):
        client.post("/behavior/track", json={
            "workspace_path": "/test/ws_status",
            "event": "error",
            "data": {}
        })
        r = client.get("/behavior/status//test/ws_status")
        assert r.status_code == 200

    def test_get_report(self, client):
        client.post("/behavior/track", json={
            "workspace_path": "/test/ws_report",
            "event": "file_switch",
            "data": {"file": "main.py"}
        })
        r = client.get("/behavior/report//test/ws_report")
        assert r.status_code == 200


# ──────────────────────────────────────────────────────────────
# Prompt Optimization
# ──────────────────────────────────────────────────────────────

class TestPrompt:
    def test_optimize(self, client, workspace_dir):
        r = client.post("/prompt/optimize", json={
            "workspace_path": workspace_dir,
            "task": "Fix the authentication bug"
        })
        assert r.status_code == 200
        data = r.json()
        assert "prompt" in data
        assert data["token_estimate"] > 0

    def test_optimize_with_error(self, client, workspace_dir):
        r = client.post("/prompt/optimize", json={
            "workspace_path": workspace_dir,
            "task": "Debug this error",
            "error_text": "KeyError: 'user'"
        })
        assert r.status_code == 200
        assert r.json()["token_estimate"] > 0


# ──────────────────────────────────────────────────────────────
# Session
# ──────────────────────────────────────────────────────────────

class TestSession:
    def test_update_session(self, client, workspace_dir):
        # Register first
        client.post("/workspace/register", json={"path": workspace_dir})
        r = client.post("/session/update", json={
            "workspace_path": workspace_dir,
            "current_file": "main.py",
            "git_branch": "main"
        })
        assert r.status_code == 200
        assert r.json()["status"] == "updated"

    def test_get_session(self, client, workspace_dir):
        r = client.get(f"/session/{workspace_dir}")
        assert r.status_code == 200
        data = r.json()
        assert "workspace" in data


# ──────────────────────────────────────────────────────────────
# Files
# ──────────────────────────────────────────────────────────────

class TestFiles:
    def test_list_files(self, client, workspace_dir):
        r = client.get(f"/files/{workspace_dir}")
        assert r.status_code == 200
        data = r.json()
        assert "files" in data
        assert len(data["files"]) > 0

    def test_get_file_content(self, client, workspace_dir):
        f = os.path.join(workspace_dir, "main.py")
        r = client.get("/file/content", params={"file_path": f})
        assert r.status_code == 200
        data = r.json()
        assert "content" in data
        assert "greet" in data["content"]

    def test_file_not_found(self, client):
        r = client.get("/file/content", params={"file_path": "/nonexistent/file.py"})
        assert r.status_code == 404
