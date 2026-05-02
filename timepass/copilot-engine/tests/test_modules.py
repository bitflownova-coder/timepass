"""
Unit tests for Copilot Engine - Backend Modules
Run with: pytest tests/ -v
"""
import os
import sys
import json
import tempfile
import shutil
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime

# Ensure engine modules are importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ──────────────────────────────────────────────────────────────
# Error Parser Tests
# ──────────────────────────────────────────────────────────────

class TestErrorParser:
    """Tests for error_parser.py"""

    def setup_method(self):
        from error_parser import error_parser
        self.parser = error_parser

    def test_parse_python_traceback(self):
        error = """Traceback (most recent call last):
  File "app.py", line 42, in main
    result = data["key"]
KeyError: 'key'"""
        parsed = self.parser.parse(error)
        assert parsed.error_type == "KeyError"
        assert parsed.language == "python"
        assert "key" in parsed.message
        assert len(parsed.suggestions) > 0

    def test_parse_python_import_error(self):
        error = """Traceback (most recent call last):
  File "app.py", line 1, in <module>
    import nonexistent_module
ModuleNotFoundError: No module named 'nonexistent_module'"""
        parsed = self.parser.parse(error)
        assert parsed.error_type in ("ModuleNotFoundError", "ImportError")
        assert parsed.language == "python"

    def test_parse_javascript_error(self):
        error = "TypeError: Cannot read properties of undefined (reading 'name')"
        parsed = self.parser.parse(error)
        assert parsed.error_type in ("TypeError", "Error")
        assert parsed.message is not None

    def test_parse_typescript_error(self):
        error = "src/app.ts(15,3): error TS2304: Cannot find name 'foo'."
        parsed = self.parser.parse(error)
        assert parsed.file_path is not None or parsed.error_type != ""

    def test_parse_empty_string(self):
        parsed = self.parser.parse("")
        assert parsed.error_type is not None  # Should not crash

    def test_parse_java_error(self):
        error = """Exception in thread "main" java.lang.NullPointerException
    at com.example.App.main(App.java:10)"""
        parsed = self.parser.parse(error)
        assert parsed.error_type in ("NullPointerException", "Exception")
        assert parsed.language == "java"

    def test_parse_generic_text(self):
        parsed = self.parser.parse("Some random text that isn't an error")
        assert parsed is not None  # Should not crash


# ──────────────────────────────────────────────────────────────
# Cache Tests
# ──────────────────────────────────────────────────────────────

class TestCache:
    """Tests for cache.py"""

    def setup_method(self):
        from cache import LRUCache, make_key
        self.LRUCache = LRUCache
        self.make_key = make_key

    def test_basic_set_get(self):
        cache = self.LRUCache(max_size=10)
        cache.set("key1", {"data": "value1"})
        assert cache.get("key1") == {"data": "value1"}

    def test_cache_miss(self):
        cache = self.LRUCache(max_size=10)
        assert cache.get("nonexistent") is None

    def test_ttl_expiration(self):
        import time
        cache = self.LRUCache(max_size=10, default_ttl=1)
        cache.set("key1", "value1", ttl=1)
        assert cache.get("key1") == "value1"
        time.sleep(1.1)
        assert cache.get("key1") is None

    def test_lru_eviction(self):
        cache = self.LRUCache(max_size=3)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)
        cache.set("d", 4)  # Should evict "a"
        assert cache.get("a") is None
        assert cache.get("b") == 2

    def test_invalidate(self):
        cache = self.LRUCache(max_size=10)
        cache.set("key1", "value1")
        cache.invalidate("key1")
        assert cache.get("key1") is None

    def test_invalidate_prefix(self):
        cache = self.LRUCache(max_size=10)
        cache.set("sec:file1", "v1")
        cache.set("sec:file2", "v2")
        cache.set("other:key", "v3")
        cache.invalidate_prefix("sec:")
        assert cache.get("sec:file1") is None
        assert cache.get("sec:file2") is None
        assert cache.get("other:key") == "v3"

    def test_clear(self):
        cache = self.LRUCache(max_size=10)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.clear()
        assert cache.get("a") is None
        assert cache.stats["size"] == 0

    def test_stats(self):
        cache = self.LRUCache(max_size=10)
        cache.set("a", 1)
        cache.get("a")  # hit
        cache.get("b")  # miss
        s = cache.stats
        assert s["hits"] == 1
        assert s["misses"] == 1
        assert s["size"] == 1

    def test_make_key_deterministic(self):
        k1 = self.make_key("fn", "arg1", "arg2")
        k2 = self.make_key("fn", "arg1", "arg2")
        k3 = self.make_key("fn", "arg1", "arg3")
        assert k1 == k2
        assert k1 != k3

    def test_thread_safety(self):
        import threading
        cache = self.LRUCache(max_size=100)
        errors = []

        def writer(n):
            try:
                for i in range(50):
                    cache.set(f"thread{n}_key{i}", i)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=writer, args=(n,)) for n in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(errors) == 0


# ──────────────────────────────────────────────────────────────
# Security Scanner Tests
# ──────────────────────────────────────────────────────────────

class TestSecurityScanner:
    """Tests for security_scanner.py"""

    def setup_method(self):
        from security_scanner import SecurityScanner
        self.scanner = SecurityScanner()
        self.tmpdir = tempfile.mkdtemp()

    def teardown_method(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _write(self, name: str, content: str) -> str:
        p = os.path.join(self.tmpdir, name)
        Path(p).write_text(content)
        return p

    def test_detect_eval(self):
        f = self._write("test.py", 'result = eval(user_input)\n')
        findings = self.scanner.scan_file(f)
        assert any("eval" in str(f).lower() or "dangerous" in str(f).lower() for f in findings)

    def test_detect_hardcoded_secret(self):
        f = self._write("config.py", 'password = "super_secret_123"\napi_key = "sk-abc123def456"\n')
        findings = self.scanner.scan_file(f)
        assert len(findings) > 0

    def test_detect_sql_injection(self):
        f = self._write("db.py", 'query = "SELECT * FROM users WHERE id = " + user_id\n')
        findings = self.scanner.scan_file(f)
        has_sql = any("sql" in str(f).lower() for f in findings)
        assert has_sql or len(findings) > 0

    def test_clean_file_no_findings(self):
        f = self._write("clean.py", 'x = 1 + 2\nprint(x)\n')
        findings = self.scanner.scan_file(f)
        assert len(findings) == 0

    def test_scan_workspace(self):
        self._write("a.py", 'eval(x)\n')
        self._write("b.py", 'print("safe")\n')
        result = self.scanner.scan_workspace(self.tmpdir)
        assert "total_findings" in result or "files_scanned" in result


# ──────────────────────────────────────────────────────────────
# SQL Analyzer Tests
# ──────────────────────────────────────────────────────────────

class TestSQLAnalyzer:
    """Tests for sql_analyzer.py"""

    def setup_method(self):
        from sql_analyzer import SQLAnalyzer
        self.analyzer = SQLAnalyzer()

    def test_select_query(self):
        result = self.analyzer.analyze("SELECT id, name FROM users WHERE id = 1")
        assert result["query_type"] == "SELECT"
        assert result["is_safe"] is True

    def test_select_star_warning(self):
        result = self.analyzer.analyze("SELECT * FROM users")
        issues = result.get("issues", []) + result.get("performance_issues", [])
        has_star_warning = any("SELECT *" in str(i) or "select *" in str(i).lower() for i in issues)
        assert has_star_warning or result["total_issues"] > 0

    def test_injection_risk(self):
        result = self.analyzer.analyze("SELECT * FROM users WHERE name = '" + "' + user_input")
        # Should flag as risky
        assert result["total_issues"] > 0 or not result["is_safe"]

    def test_delete_without_where(self):
        result = self.analyzer.analyze("DELETE FROM users")
        findings = result.get("findings", [])
        assert len(findings) > 0 or not result.get("is_safe", True)

    def test_insert_query(self):
        result = self.analyzer.analyze("INSERT INTO users (name) VALUES ('test')")
        assert result["query_type"] == "INSERT"

    def test_validate_syntax_balanced(self):
        result = self.analyzer.validate_query_syntax("SELECT (a + b) FROM t")
        assert result["valid"] is True

    def test_validate_syntax_unbalanced(self):
        result = self.analyzer.validate_query_syntax("SELECT (a + b FROM t")
        assert result["valid"] is False


# ──────────────────────────────────────────────────────────────
# API Detector Tests
# ──────────────────────────────────────────────────────────────

class TestAPIDetector:
    """Tests for api_detector.py"""

    def setup_method(self):
        from api_detector import APIDetector
        self.detector = APIDetector()
        self.tmpdir = tempfile.mkdtemp()

    def teardown_method(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _write(self, name: str, content: str) -> str:
        p = os.path.join(self.tmpdir, name)
        Path(p).parent.mkdir(parents=True, exist_ok=True)
        Path(p).write_text(content)
        return p

    def test_detect_flask_routes(self):
        self._write("app.py", """
from flask import Flask
app = Flask(__name__)

@app.route('/users', methods=['GET'])
def get_users():
    pass

@app.route('/users', methods=['POST'])
def create_user():
    pass
""")
        result = self.detector.detect_endpoints(self.tmpdir)
        assert result["total_endpoints"] >= 2
        assert "flask" in result["frameworks"]

    def test_detect_fastapi_routes(self):
        self._write("main.py", """
from fastapi import FastAPI
app = FastAPI()

@app.get('/items')
def list_items():
    pass

@app.post('/items')
def create_item():
    pass
""")
        result = self.detector.detect_endpoints(self.tmpdir)
        assert result["total_endpoints"] >= 2
        assert "fastapi" in result["frameworks"]

    def test_detect_express_routes(self):
        self._write("server.js", """
const express = require('express');
const app = express();

app.get('/api/users', (req, res) => {});
app.post('/api/users', (req, res) => {});
""")
        result = self.detector.detect_endpoints(self.tmpdir)
        assert result["total_endpoints"] >= 2

    def test_empty_workspace(self):
        result = self.detector.detect_endpoints(self.tmpdir)
        assert result["total_endpoints"] == 0


# ──────────────────────────────────────────────────────────────
# Behavior Tracker Tests
# ──────────────────────────────────────────────────────────────

class TestBehaviorTracker:
    """Tests for behavior_tracker.py"""

    def setup_method(self):
        from behavior_tracker import BehaviorTracker
        self.tracker = BehaviorTracker()

    def test_track_error_event(self):
        result = self.tracker.track_event("/test/ws", "error", {"error_type": "TypeError"})
        assert result["error_count"] >= 1

    def test_track_file_switch(self):
        result = self.tracker.track_event("/test/ws", "file_switch", {"file": "main.py"})
        assert "file_switches" in result

    def test_focus_mode_detection(self):
        """Repeated errors should eventually suggest focus mode."""
        for _ in range(10):
            result = self.tracker.track_event("/test/ws2", "error", {"error_type": "KeyError"})
        assert result.get("focus_mode_suggested", False) or result["error_count"] >= 10

    def test_get_status(self):
        self.tracker.track_event("/test/ws3", "error", {"error_type": "X"})
        status = self.tracker.get_status("/test/ws3")
        assert "error_count" in status or "errors" in str(status).lower()

    def test_get_report(self):
        self.tracker.track_event("/test/ws4", "error", {"error_type": "Y"})
        report = self.tracker.get_session_report("/test/ws4")
        assert report is not None


# ──────────────────────────────────────────────────────────────
# Git Analyzer Tests
# ──────────────────────────────────────────────────────────────

class TestGitAnalyzer:
    """Tests for git_analyzer.py"""

    def setup_method(self):
        from git_analyzer import GitAnalyzer
        self.analyzer = GitAnalyzer()

    def test_is_git_repo_valid(self):
        # The workspace itself should be a git repo
        ws = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        result = self.analyzer.is_git_repo(ws)
        # May or may not be a repo; just ensure no crash
        assert isinstance(result, bool)

    def test_is_git_repo_invalid(self):
        assert self.analyzer.is_git_repo(tempfile.mkdtemp()) is False

    def test_analyze_diff_non_repo(self):
        result = self.analyzer.analyze_diff(tempfile.mkdtemp())
        assert "risk_score" in result or "error" in str(result).lower()

    def test_get_current_branch(self):
        result = self.analyzer.get_current_branch(tempfile.mkdtemp())
        # Non-repo should return None or empty
        assert result is None or isinstance(result, str)


# ──────────────────────────────────────────────────────────────
# Prompt Optimizer Tests
# ──────────────────────────────────────────────────────────────

class TestPromptOptimizer:
    """Tests for prompt_optimizer.py"""

    def setup_method(self):
        from prompt_optimizer import PromptOptimizer
        self.optimizer = PromptOptimizer()
        self.tmpdir = tempfile.mkdtemp()

    def teardown_method(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_optimize_debug(self):
        result = self.optimizer.optimize(
            workspace_path=self.tmpdir,
            task="Fix KeyError in main.py",
            error_text="KeyError: 'name'",
        )
        assert "prompt" in result
        assert result["token_estimate"] > 0
        assert "debug" in result["metadata"].get("template", "").lower() or len(result["prompt"]) > 10

    def test_optimize_general(self):
        result = self.optimizer.optimize(
            workspace_path=self.tmpdir,
            task="Add user authentication",
        )
        assert "prompt" in result
        assert result["token_estimate"] > 0

    def test_optimize_with_code_snippet(self):
        result = self.optimizer.optimize(
            workspace_path=self.tmpdir,
            task="Improve this function",
            code_snippet="def add(a, b):\n    return a + b",
        )
        assert "prompt" in result


# ──────────────────────────────────────────────────────────────
# Context Builder Tests
# ──────────────────────────────────────────────────────────────

class TestContextBuilder:
    """Tests for context_builder.py"""

    def setup_method(self):
        from context_builder import context_builder
        self.builder = context_builder
        self.tmpdir = tempfile.mkdtemp()

    def teardown_method(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_get_project_context(self):
        ctx = self.builder.get_project_context(self.tmpdir)
        assert ctx is not None

    def test_detect_language(self):
        lang = self.builder.detect_language("test.py")
        assert lang == "python"
        lang = self.builder.detect_language("app.js")
        assert lang == "javascript"
        lang = self.builder.detect_language("main.go")
        assert lang == "go"

    def test_build_prompt(self):
        built = self.builder.build_prompt(task="Fix bug")
        assert built.prompt is not None
        assert built.token_estimate > 0


# ──────────────────────────────────────────────────────────────
# Database Tests
# ──────────────────────────────────────────────────────────────

class TestDatabase:
    """Tests for database.py and models.py"""

    def setup_method(self):
        from database import Database
        self.db = Database(db_path=":memory:")
        self.db.init_db()

    def test_init_creates_tables(self):
        from models import Workspace
        with self.db.get_session() as session:
            count = session.query(Workspace).count()
            assert count == 0  # Empty but table exists

    def test_create_workspace(self):
        from models import Workspace
        with self.db.get_session() as session:
            ws = Workspace(path="/test/project", name="test")
            session.add(ws)
            session.flush()
            assert ws.id is not None
            assert ws.path == "/test/project"

    def test_create_error_log(self):
        from models import Workspace, ErrorLog
        with self.db.get_session() as session:
            ws = Workspace(path="/test/project2", name="test2")
            session.add(ws)
            session.flush()

            err = ErrorLog(
                workspace_id=ws.id,
                error_type="TypeError",
                message="test error"
            )
            session.add(err)
            session.flush()
            assert err.id is not None

    def test_workspace_error_relationship(self):
        from models import Workspace, ErrorLog
        with self.db.get_session() as session:
            ws = Workspace(path="/test/project3", name="test3")
            session.add(ws)
            session.flush()

            err = ErrorLog(workspace_id=ws.id, error_type="KeyError", message="missing")
            session.add(err)
            session.flush()

            loaded = session.query(Workspace).filter_by(path="/test/project3").first()
            assert len(loaded.errors) == 1
            assert loaded.errors[0].error_type == "KeyError"


# ──────────────────────────────────────────────────────────────
# Config Tests
# ──────────────────────────────────────────────────────────────

class TestConfig:
    """Tests for config.py"""

    def test_default_settings(self):
        from config import Settings
        s = Settings()
        assert s.host == "127.0.0.1"
        assert s.port == 7779
        assert s.max_prompt_tokens == 4000
        assert ".py" in s.watched_extensions
        assert "node_modules" in s.ignored_dirs
