"""
Live Backend Integration Test
Tests every API endpoint against the running server at :7779
Run: python tests/test_live_endpoints.py
"""
import requests
import json
import sys
import time
import os

BASE = "http://127.0.0.1:7779"
# Auto-detect workspace: parent of copilot-engine directory
WS = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

passed = 0
failed = 0
errors = []

def test(name, method, path, body=None, expect_status=200, check=None):
    global passed, failed
    url = f"{BASE}{path}"
    try:
        if method == "GET":
            r = requests.get(url, timeout=10)
        else:
            r = requests.post(url, json=body, timeout=10)
        
        status_ok = r.status_code == expect_status
        data = None
        try:
            data = r.json()
        except:
            pass

        check_ok = True
        check_msg = ""
        if check and data:
            check_ok, check_msg = check(data)

        if status_ok and check_ok:
            passed += 1
            print(f"  ✅ {name}")
        else:
            failed += 1
            reason = f"status={r.status_code}" if not status_ok else check_msg
            errors.append(f"{name}: {reason}")
            print(f"  ❌ {name} — {reason}")
        
        return data
    except Exception as e:
        failed += 1
        errors.append(f"{name}: {e}")
        print(f"  ❌ {name} — {e}")
        return None

# ════════════════════════════════════════════════
print("\n" + "="*60)
print("   COPILOT ENGINE — LIVE ENDPOINT TEST")
print("="*60)

# ── 1. Core Routes ────────────────────────────
print("\n🔹 CORE ROUTES")

test("GET /", "GET", "/",
     check=lambda d: (d.get("name") == "Copilot Engine", f"name={d.get('name')}"))

test("GET /health", "GET", "/health",
     check=lambda d: (d.get("status") == "healthy", f"status={d.get('status')}"))

test("GET /cache/stats", "GET", "/cache/stats",
     check=lambda d: ("response" in d and "hit_rate" in d["response"], "missing response.hit_rate"))

test("POST /cache/clear", "POST", "/cache/clear",
     check=lambda d: ("status" in d, "missing status"))

# ── 2. Workspace Routes ──────────────────────
print("\n🔹 WORKSPACE")

test("POST /workspace/register", "POST", "/workspace/register",
     body={"path": WS, "name": "timepass"},
     check=lambda d: (d.get("path") == WS, f"path={d.get('path')}"))

test("GET /workspaces", "GET", "/workspaces",
     check=lambda d: (isinstance(d, list) and len(d) > 0, "empty workspaces"))

test("POST /workspace/register (invalid)", "POST", "/workspace/register",
     body={"path": "/nonexistent/path123"},
     expect_status=400)

# ── 3. Error Handling ────────────────────────
print("\n🔹 ERROR PARSING")

test("POST /error/parse (Python)", "POST", "/error/parse",
     body={"error_text": "Traceback (most recent call last):\n  File 'app.py', line 42\nTypeError: 'NoneType' has no attribute 'items'"},
     check=lambda d: (d.get("error_type") == "TypeError", f"type={d.get('error_type')}"))

test("POST /error/parse (JS)", "POST", "/error/parse",
     body={"error_text": "ReferenceError: foo is not defined\n    at Object.<anonymous> (test.js:3:1)"},
     check=lambda d: ("ReferenceError" in d.get("error_type", ""), f"type={d.get('error_type')}"))

test("POST /error/find-similar", "POST", "/error/find-similar",
     body={"error_text": "TypeError: Cannot read property 'map' of undefined"},
     check=lambda d: ("similar_fixes" in d or "similar_errors" in d, "missing similar data"))

# ── 4. Context Building ─────────────────────
print("\n🔹 CONTEXT BUILDING")

test("POST /context/build", "POST", "/context/build",
     body={"workspace_path": WS, "task": "Fix authentication bug"},
     check=lambda d: (d.get("token_estimate", 0) > 0, f"tokens={d.get('token_estimate')}"))

test("POST /context/debug", "POST", "/context/debug",
     body={"workspace_path": WS, "error_text": "ImportError: No module named 'flask'"},
     check=lambda d: ("prompt" in d, "missing prompt"))

test("POST /context/debug (no workspace)", "POST", "/context/debug",
     body={"error_text": "ImportError: No module named 'flask'"},
     expect_status=400)

# ── 5. Git Routes ────────────────────────────
print("\n🔹 GIT")

test("POST /git/diff", "POST", "/git/diff",
     body={"workspace_path": WS},
     check=lambda d: ("risk_score" in d, "missing risk_score"))

test("GET /git/branch", "GET", f"/git/branch/{WS}",
     check=lambda d: ("branch" in d, "missing branch"))

test("GET /git/changed-files", "GET", f"/git/changed-files/{WS}",
     check=lambda d: ("files" in d or isinstance(d, list), "missing files"))

# ── 6. Security ──────────────────────────────
print("\n🔹 SECURITY")

test("POST /security/scan-workspace", "POST", "/security/scan-workspace",
     body={"workspace_path": WS},
     check=lambda d: ("findings" in d or "vulnerabilities" in d or isinstance(d, list) or "total_findings" in d, "unexpected shape"))

test("POST /security/scan (file)", "POST", "/security/scan",
     body={"file_path": WS + r"\copilot-engine\server.py"},
     check=lambda d: ("findings" in d or "vulnerabilities" in d or isinstance(d, list), "unexpected shape"))

# ── 7. SQL ───────────────────────────────────
print("\n🔹 SQL ANALYSIS")

test("POST /sql/analyze", "POST", "/sql/analyze",
     body={"query": "SELECT * FROM users WHERE id = 1"},
     check=lambda d: ("query_type" in d or "type" in d, "missing query_type"))

test("POST /sql/validate", "POST", "/sql/validate",
     body={"query": "SELECT id, name FROM users WHERE active = true"},
     check=lambda d: ("valid" in d or "is_valid" in d, "missing valid"))

# ── 8. API Detection ────────────────────────
print("\n🔹 API DETECTION")

test("POST /api/detect", "POST", "/api/detect",
     body={"workspace_path": WS},
     check=lambda d: ("endpoints" in d or isinstance(d, list), "missing endpoints"))

# ── 9. Behavior ──────────────────────────────
print("\n🔹 BEHAVIOR TRACKING")

test("POST /behavior/track", "POST", "/behavior/track",
     body={"workspace_path": WS, "event": "error", "data": {"error": "test"}},
     check=lambda d: (d.get("status") == "tracked" or "message" in d, "not tracked"))

test("GET /behavior/status", "GET", f"/behavior/status/{WS}",
     check=lambda d: ("error_count" in d or "message" in d, "unexpected shape"))

test("GET /behavior/report", "GET", f"/behavior/report/{WS}",
     check=lambda d: (isinstance(d, dict), "not a dict"))

# ── 10. Prompt Optimizer ─────────────────────
print("\n🔹 PROMPT OPTIMIZER")

test("POST /prompt/optimize", "POST", "/prompt/optimize",
     body={"task": "Fix the login page CSS", "workspace_path": WS},
     check=lambda d: ("prompt" in d or "optimized" in d, "missing prompt"))

# ── 11. Session ──────────────────────────────
print("\n🔹 SESSION")

test("POST /session/update", "POST", "/session/update",
     body={"workspace_path": WS, "active_file": "server.py", "cursor_line": 42},
     check=lambda d: (d.get("status") == "updated" or "message" in d, "not updated"))

test("GET /session", "GET", f"/session/{WS}",
     check=lambda d: (isinstance(d, dict), "not a dict"))

# ── 12. Files ────────────────────────────────
print("\n🔹 FILES")

test("GET /files/{path}", "GET", f"/files/{WS}",
     check=lambda d: ("files" in d or isinstance(d, list), "missing files"))

test("GET /file/content", "GET", f"/file/content?file_path={WS}\\copilot-engine\\server.py",
     check=lambda d: ("content" in d and len(d["content"]) > 0, "empty content"))

test("GET /file/content (not found)", "GET", f"/file/content?file_path={WS}\\nonexistent_file_xyz.py",
     expect_status=404)

# ════════════════════════════════════════════════
# ENFORCEMENT ROUTES
# ════════════════════════════════════════════════
print("\n" + "="*60)
print("   ENFORCEMENT ENDPOINTS")
print("="*60)

# ── 13. Prisma/Schema ────────────────────────
print("\n🔹 PRISMA / SCHEMA")

test("POST /prisma/analyze", "POST", "/prisma/analyze",
     body={"workspace_path": WS},
     check=lambda d: ("has_prisma" in d or "models" in d, "unexpected shape"))

test("POST /prisma/validate", "POST", "/prisma/validate",
     body={"workspace_path": WS},
     check=lambda d: ("has_prisma" in d or "issues" in d or "valid" in d, "unexpected shape"))

test("POST /prisma/schema", "POST", "/prisma/schema",
     body={"workspace_path": WS},
     # No prisma schema in workspace — 404 is expected
     expect_status=404)

test("POST /prisma/validate-dto", "POST", "/prisma/validate-dto",
     body={"workspace_path": WS, "dto_file": WS + r"\copilot-engine\server.py"},
     check=lambda d: (isinstance(d, dict), "not a dict"))

test("POST /prisma/check-include", "POST", "/prisma/check-include",
     body={"workspace_path": WS, "file_path": WS + r"\copilot-engine\server.py"},
     check=lambda d: (isinstance(d, dict), "not a dict"))

# ── 14. Contracts ────────────────────────────
print("\n🔹 CONTRACTS")

test("POST /contracts/analyze", "POST", "/contracts/analyze",
     body={"workspace_path": WS},
     check=lambda d: (isinstance(d, dict), "not a dict"))

test("POST /contracts/validate", "POST", "/contracts/validate",
     body={"workspace_path": WS},
     check=lambda d: ("violations" in d or isinstance(d, dict), "unexpected shape"))

test("POST /contracts/map", "POST", "/contracts/map",
     body={"workspace_path": WS},
     check=lambda d: ("endpoints" in d or "total_endpoints" in d, "missing endpoints"))

test("POST /contracts/check", "POST", "/contracts/check",
     body={"method": "GET", "path": "/api/users", "workspace_path": WS},
     check=lambda d: (isinstance(d, dict), "not a dict"))

# ── 15. Impact ───────────────────────────────
print("\n🔹 IMPACT ANALYSIS")

test("POST /impact/build-graph", "POST", "/impact/build-graph",
     body={"workspace_path": WS},
     check=lambda d: (isinstance(d, dict), "not a dict"))

test("POST /impact/analyze", "POST", "/impact/analyze",
     body={"workspace_path": WS, "changed_file": WS + r"\copilot-engine\server.py"},
     check=lambda d: ("risk_score" in d or "risk_level" in d or "impact_radius" in d, "missing risk data"))

test("POST /impact/dependency-map", "POST", "/impact/dependency-map",
     body={"workspace_path": WS},
     check=lambda d: (isinstance(d, dict), "not a dict"))

test("POST /impact/file-info", "POST", "/impact/file-info",
     body={"workspace_path": WS, "file_path": WS + r"\copilot-engine\server.py"},
     check=lambda d: (isinstance(d, dict), "not a dict"))

# ── 16. Pipeline ─────────────────────────────
print("\n🔹 VALIDATION PIPELINE")

test("POST /pipeline/full-scan", "POST", "/pipeline/full-scan",
     body={"workspace_path": WS},
     check=lambda d: ("issues" in d and "overall_risk_score" in d, "missing issues/overall_risk_score"))

test("POST /pipeline/file-change", "POST", "/pipeline/file-change",
     body={"workspace_path": WS, "file_path": WS + r"\copilot-engine\server.py", "change_type": "modified"},
     check=lambda d: ("issues" in d, "missing issues"))

test("POST /pipeline/pre-commit", "POST", "/pipeline/pre-commit",
     body={"workspace_path": WS, "changed_files": ["server.py", "config.py"]},
     check=lambda d: ("issues" in d and "overall_risk_score" in d, "missing issues/overall_risk_score"))

# ── 17. Stack Detection ─────────────────────
print("\n🔹 STACK DETECTION")

test("POST /stack/detect", "POST", "/stack/detect",
     body={"workspace_path": WS},
     check=lambda d: ("language" in d or "framework" in d, "missing stack info"))

# ════════════════════════════════════════════════
# SUMMARY
# ════════════════════════════════════════════════
print("\n" + "="*60)
total = passed + failed
print(f"   RESULTS: {passed}/{total} passed, {failed} failed")
print("="*60)

if errors:
    print("\n❌ FAILURES:")
    for e in errors:
        print(f"   → {e}")

print()
sys.exit(1 if failed > 0 else 0)
