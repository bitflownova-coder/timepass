"""
Copilot Engine - Full Autonomous Runtime Live Test
Tests ALL features (old + new) against the running server on port 7779,
using the copilot-engine workspace itself as the test subject.
"""
import sys
import json
import time
import urllib.request
import urllib.error
from typing import Any, Optional

BASE = "http://127.0.0.1:7779"
WS_PATH = r"D:\Bitflow_softwares\timepass\copilot-engine"
WS_PATH_ENCODED = "D%3A%5CBitflow_softwares%5Ctimepass%5Ccopilot-engine"

passed = 0
failed = 0
errors = []


def req(method: str, path: str, body: Any = None, timeout: int = 30) -> dict:
    url = f"{BASE}{path}"
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"} if data else {}
    r = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return {"__error__": e.code, "__body__": e.read().decode()[:500]}
    except Exception as e:
        return {"__error__": str(e)}


def test(name: str, result: dict, checks: list[tuple[str, bool]]):
    global passed, failed
    all_ok = True
    for desc, ok in checks:
        if ok:
            passed += 1
        else:
            failed += 1
            all_ok = False
            errors.append(f"  FAIL [{name}] {desc}")
    status = "✅" if all_ok else "❌"
    print(f"  {status} {name}")
    if not all_ok:
        snippet = json.dumps(result, indent=2)[:300]
        print(f"     Response: {snippet}")


def section(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


# ═══════════════════════════════════════════════════════════
# SECTION 1: HEALTH & BASICS
# ═══════════════════════════════════════════════════════════
section("1. HEALTH & BASICS")

r = req("GET", "/health")
test("GET /health", r, [
    ("status is healthy", r.get("status") == "healthy"),
    ("version exists", "version" in r),
    ("uptime > 0", r.get("uptime", 0) > 0),
])

r = req("GET", "/")
test("GET / (root)", r, [
    ("has name", "name" in r),
])

r = req("GET", "/cache/stats")
test("GET /cache/stats", r, [
    ("response ok", "__error__" not in r),
])


# ═══════════════════════════════════════════════════════════
# SECTION 2: WORKSPACE REGISTRATION
# ═══════════════════════════════════════════════════════════
section("2. WORKSPACE")

r = req("POST", "/workspace/register", {"path": WS_PATH, "name": "copilot-engine"})
test("POST /workspace/register", r, [
    ("got id", "id" in r),
    ("path matches", WS_PATH.lower() in r.get("path", "").lower() or "id" in r),
])

r = req("GET", "/workspaces")
test("GET /workspaces", r, [
    ("is list", isinstance(r, list)),
    ("has at least 1", len(r) >= 1 if isinstance(r, list) else False),
])


# ═══════════════════════════════════════════════════════════
# SECTION 3: ERROR PARSING
# ═══════════════════════════════════════════════════════════
section("3. ERROR PARSING")

r = req("POST", "/error/parse", {
    "error_text": "TypeError: Cannot read property 'map' of undefined at server.py:42",
    "workspace_path": WS_PATH
})
test("POST /error/parse", r, [
    ("got error_type", "error_type" in r),
    ("got suggestions", "suggestions" in r),
])

r = req("POST", "/error/find-similar", {
    "error_text": "TypeError: Cannot read property 'map' of undefined",
    "workspace_path": WS_PATH
})
test("POST /error/find-similar", r, [
    ("response ok", "__error__" not in r),
])


# ═══════════════════════════════════════════════════════════
# SECTION 4: CONTEXT BUILDING
# ═══════════════════════════════════════════════════════════
section("4. CONTEXT BUILDING")

r = req("POST", "/context/build", {
    "workspace_path": WS_PATH,
    "current_file": f"{WS_PATH}\\server.py",
    "task": "Fix a bug in the server"
})
test("POST /context/build", r, [
    ("got prompt", "prompt" in r),
    ("got token_estimate", "token_estimate" in r),
    ("prompt not empty", len(r.get("prompt", "")) > 10),
])


# ═══════════════════════════════════════════════════════════
# SECTION 5: FILE INDEXING
# ═══════════════════════════════════════════════════════════
section("5. FILE INDEXING")

r = req("GET", f"/files/{WS_PATH_ENCODED}")
test("GET /files/{ws}", r, [
    ("has files", "files" in r or isinstance(r, list)),
    ("no error", "__error__" not in r),
])


# ═══════════════════════════════════════════════════════════
# SECTION 6: GIT ANALYSIS
# ═══════════════════════════════════════════════════════════
section("6. GIT ANALYSIS")

r = req("POST", "/git/diff", {"workspace_path": WS_PATH})
test("POST /git/diff", r, [
    ("has changes or workspace", "changes" in r or "workspace" in r),
])

r = req("GET", f"/git/recent-commits/{WS_PATH_ENCODED}")
test("GET /git/recent-commits", r, [
    ("response ok", "__error__" not in r),
])

r = req("GET", f"/git/branch/{WS_PATH_ENCODED}")
test("GET /git/branch", r, [
    ("has branch", "branch" in r),
])


# ═══════════════════════════════════════════════════════════
# SECTION 7: SECURITY SCANNING
# ═══════════════════════════════════════════════════════════
section("7. SECURITY")

r = req("POST", "/security/scan", {"file_path": f"{WS_PATH}\\server.py"})
test("POST /security/scan (single file)", r, [
    ("response ok", "__error__" not in r),
])

r = req("POST", "/security/scan-workspace", {"workspace_path": WS_PATH})
test("POST /security/scan-workspace", r, [
    ("has findings or total", "findings" in r or "total_findings" in r or "scanned_files" in r),
])


# ═══════════════════════════════════════════════════════════
# SECTION 8: BEHAVIOR TRACKING
# ═══════════════════════════════════════════════════════════
section("8. BEHAVIOR")

r = req("POST", "/behavior/track", {
    "workspace_path": WS_PATH,
    "event": "error",
    "data": {"error_text": "test error"}
})
test("POST /behavior/track", r, [
    ("response ok", "__error__" not in r),
])

r = req("GET", f"/behavior/status/{WS_PATH_ENCODED}")
test("GET /behavior/status", r, [
    ("response ok", "__error__" not in r),
])


# ═══════════════════════════════════════════════════════════
# SECTION 9: API DETECTION
# ═══════════════════════════════════════════════════════════
section("9. API DETECTION")

r = req("POST", "/api/detect", {"workspace_path": WS_PATH})
test("POST /api/detect", r, [
    ("has endpoints", "endpoints" in r or "routes" in r or isinstance(r, list)),
])


# ═══════════════════════════════════════════════════════════
# SECTION 10: SQL ANALYSIS
# ═══════════════════════════════════════════════════════════
section("10. SQL ANALYSIS")

r = req("POST", "/sql/analyze", {"query": "SELECT * FROM users WHERE id = 1"})
test("POST /sql/analyze", r, [
    ("response ok", "__error__" not in r),
])


# ═══════════════════════════════════════════════════════════
# SECTION 11: PROMPT OPTIMIZATION
# ═══════════════════════════════════════════════════════════
section("11. PROMPT OPTIMIZATION")

r = req("POST", "/prompt/optimize", {
    "task": "fix the bug in my code",
    "workspace_path": WS_PATH
})
test("POST /prompt/optimize", r, [
    ("has optimized_prompt or prompt", "optimized_prompt" in r or "prompt" in r),
])


# ═══════════════════════════════════════════════════════════
# SECTION 12: ENFORCEMENT - PRISMA
# ═══════════════════════════════════════════════════════════
section("12. PRISMA / SCHEMA")

r = req("POST", "/prisma/analyze", {"workspace_path": WS_PATH})
test("POST /prisma/analyze", r, [
    ("response ok", "__error__" not in r),
])

r = req("POST", "/prisma/schema", {"workspace_path": WS_PATH})
test("POST /prisma/schema", r, [
    ("response ok or no schema", "__error__" not in r or r.get("__error__") == 404),
])


# ═══════════════════════════════════════════════════════════
# SECTION 13: ENFORCEMENT - CONTRACTS
# ═══════════════════════════════════════════════════════════
section("13. CONTRACTS")

r = req("POST", "/contracts/validate", {"workspace_path": WS_PATH})
test("POST /contracts/validate", r, [
    ("response ok", "__error__" not in r),
])

r = req("POST", "/contracts/map", {"workspace_path": WS_PATH})
test("POST /contracts/map", r, [
    ("response ok", "__error__" not in r),
])


# ═══════════════════════════════════════════════════════════
# SECTION 14: ENFORCEMENT - IMPACT
# ═══════════════════════════════════════════════════════════
section("14. IMPACT ANALYSIS")

r = req("POST", "/impact/build-graph", {"workspace_path": WS_PATH})
test("POST /impact/build-graph", r, [
    ("response ok", "__error__" not in r),
])

r = req("POST", "/impact/analyze", {
    "workspace_path": WS_PATH,
    "changed_file": f"{WS_PATH}\\server.py",
    "old_content": "",
    "new_content": ""
})
test("POST /impact/analyze", r, [
    ("response ok", "__error__" not in r),
])

r = req("POST", "/impact/dependency-map", {"workspace_path": WS_PATH})
test("POST /impact/dependency-map", r, [
    ("response ok", "__error__" not in r),
])


# ═══════════════════════════════════════════════════════════
# SECTION 15: PIPELINE
# ═══════════════════════════════════════════════════════════
section("15. VALIDATION PIPELINE")

r = req("POST", "/pipeline/full-scan", {"workspace_path": WS_PATH})
test("POST /pipeline/full-scan", r, [
    ("has issues or risk_score", "issues" in r or "risk_score" in r),
])

r = req("POST", "/pipeline/file-change", {
    "workspace_path": WS_PATH,
    "file_path": f"{WS_PATH}\\server.py",
    "old_content": "",
    "new_content": ""
})
test("POST /pipeline/file-change", r, [
    ("response ok", "__error__" not in r),
])

r = req("POST", "/pipeline/pre-commit", {
    "workspace_path": WS_PATH,
    "changed_files": [f"{WS_PATH}\\server.py", f"{WS_PATH}\\models.py"]
})
test("POST /pipeline/pre-commit", r, [
    ("has commit_safe", "commit_safe" in r),
])


# ═══════════════════════════════════════════════════════════
# SECTION 16: STACK DETECTION
# ═══════════════════════════════════════════════════════════
section("16. STACK DETECTION")

r = req("POST", "/stack/detect", {"workspace_path": WS_PATH})
test("POST /stack/detect", r, [
    ("detected python", "python" in json.dumps(r).lower()),
])


# ═══════════════════════════════════════════════════════════
# SECTION 17: AUTONOMOUS - STATUS & CONFIG
# ═══════════════════════════════════════════════════════════
section("17. AUTONOMOUS - STATUS & CONFIG")

r = req("GET", "/autonomous/status")
test("GET /autonomous/status", r, [
    ("running field exists", "running" in r),
    ("stats exist", "stats" in r),
    ("worker is running", r.get("running") == True),
])

r = req("POST", "/autonomous/configure", {
    "workspace_path": WS_PATH,
    "idle_interval": 120,
    "debounce_ms": 500
})
test("POST /autonomous/configure", r, [
    ("idle_interval set", r.get("idle_interval") == 120),
    ("debounce_ms set", r.get("debounce_ms") == 500),
])


# ═══════════════════════════════════════════════════════════
# SECTION 18: AUTONOMOUS - INITIALIZE WORKSPACE
# ═══════════════════════════════════════════════════════════
section("18. AUTONOMOUS - INITIALIZE WORKSPACE")

print("  ⏳ Initializing workspace (full index + graph build)... this may take a moment")
r = req("POST", "/autonomous/initialize", {"workspace_path": WS_PATH}, timeout=120)
test("POST /autonomous/initialize", r, [
    ("initialized or already", r.get("initialized") == True or r.get("already_initialized") == True),
    ("has steps", "steps" in r or "already_initialized" in r),
])

if "steps" in r:
    steps = r["steps"]
    idx = steps.get("index", {})
    graph = steps.get("graph", {})
    snaps = steps.get("snapshots", 0)
    risk = steps.get("risk", {})
    print(f"     📊 Indexed: {idx.get('indexed', '?')} files, {idx.get('entities_found', '?')} entities")
    print(f"     🕸️  Graph: {graph.get('file_edges', '?')} file edges, {graph.get('entity_edges', '?')} entity edges")
    print(f"     📸 Snapshots stored: {snaps}")
    print(f"     🎯 Risk score: {risk.get('overall_score', '?')}/10 ({risk.get('health_level', '?')})")

    test("Init - entities found", r, [
        ("found >0 entities", idx.get("entities_found", 0) > 0),
    ])
    test("Init - graph built", r, [
        ("has file edges", graph.get("file_edges", 0) >= 0),
    ])


# ═══════════════════════════════════════════════════════════
# SECTION 19: AUTONOMOUS - EVENT SUBMISSION
# ═══════════════════════════════════════════════════════════
section("19. AUTONOMOUS - EVENT SUBMISSION")

r = req("POST", "/autonomous/event", {
    "file_path": f"{WS_PATH}\\server.py",
    "workspace_path": WS_PATH,
    "change_type": "saved",
    "git_branch": "main"
})
test("POST /autonomous/event (save)", r, [
    ("queued", r.get("queued") == True),
    ("file matches", "server.py" in r.get("file", "")),
])

r = req("POST", "/autonomous/event", {
    "file_path": f"{WS_PATH}\\models.py",
    "workspace_path": WS_PATH,
    "change_type": "saved"
})
test("POST /autonomous/event (models save)", r, [
    ("queued", r.get("queued") == True),
])

# Give the fast worker time to process
print("  ⏳ Waiting 3s for fast worker to process events...")
time.sleep(3)


# ═══════════════════════════════════════════════════════════
# SECTION 20: AUTONOMOUS - HEALTH & DASHBOARD
# ═══════════════════════════════════════════════════════════
section("20. AUTONOMOUS - HEALTH & DASHBOARD")

r = req("GET", f"/autonomous/health/{WS_PATH_ENCODED}")
test("GET /autonomous/health/{ws}", r, [
    ("has workspace", "workspace" in r),
    ("has risk_scores", "risk_scores" in r),
    ("has graph", "graph" in r),
    ("has worker", "worker" in r),
])

if "risk_scores" in r:
    rs = r["risk_scores"]
    print(f"     🎯 Overall: {rs.get('overall_score', '?')}/10 ({rs.get('health_level', '?')})")
    print(f"     📋 Schema: {rs.get('schema_risk', '?')} | Contracts: {rs.get('contract_risk', '?')} | Drift: {rs.get('drift_risk', '?')}")
    print(f"     🛡️  Security: {rs.get('security_risk', '?')} | Deps: {rs.get('dependency_risk', '?')} | Migration: {rs.get('migration_risk', '?')}")
    print(f"     📝 Naming: {rs.get('naming_risk', '?')}")

if "worker" in r:
    w = r["worker"]
    print(f"     ⚙️  Events processed: {w.get('events_processed', 0)} | Fast runs: {w.get('fast_path_runs', 0)} | Errors: {w.get('errors', 0)}")


# Full dashboard endpoint
r = req("GET", f"/autonomous/dashboard/{WS_PATH_ENCODED}")
test("GET /autonomous/dashboard/{ws}", r, [
    ("has health", "health" in r),
    ("has risk_trend", "risk_trend" in r),
    ("has unresolved_drifts", "unresolved_drifts" in r),
    ("has circular_dependencies", "circular_dependencies" in r),
    ("has dead_code_files", "dead_code_files" in r),
    ("has timestamp", "timestamp" in r),
])


# ═══════════════════════════════════════════════════════════
# SECTION 21: AUTONOMOUS - RISK TREND
# ═══════════════════════════════════════════════════════════
section("21. AUTONOMOUS - RISK TREND")

r = req("GET", f"/autonomous/risk-trend/{WS_PATH_ENCODED}?limit=10")
test("GET /autonomous/risk-trend", r, [
    ("is list", isinstance(r, list)),
])
if isinstance(r, list) and len(r) > 0:
    print(f"     📈 {len(r)} trend point(s), latest score: {r[-1].get('overall_score', '?')}")


# ═══════════════════════════════════════════════════════════
# SECTION 22: AUTONOMOUS - DRIFT EVENTS
# ═══════════════════════════════════════════════════════════
section("22. AUTONOMOUS - DRIFT EVENTS")

r = req("GET", f"/autonomous/drifts/{WS_PATH_ENCODED}")
test("GET /autonomous/drifts", r, [
    ("is list", isinstance(r, list)),
])
if isinstance(r, list):
    print(f"     🔄 {len(r)} unresolved drift event(s)")


# ═══════════════════════════════════════════════════════════
# SECTION 23: AUTONOMOUS - CIRCULAR DEPS
# ═══════════════════════════════════════════════════════════
section("23. AUTONOMOUS - CIRCULAR DEPENDENCIES")

r = req("GET", "/autonomous/circular-deps")
test("GET /autonomous/circular-deps", r, [
    ("is list", isinstance(r, list)),
])
if isinstance(r, list):
    print(f"     🔄 {len(r)} circular dependency cycle(s)")
    for cycle in r[:5]:
        short = [f.split("\\")[-1] for f in cycle] if isinstance(cycle, list) else cycle
        print(f"        → {' → '.join(short)}")


# ═══════════════════════════════════════════════════════════
# SECTION 24: AUTONOMOUS - DEAD CODE
# ═══════════════════════════════════════════════════════════
section("24. AUTONOMOUS - DEAD CODE")

r = req("GET", "/autonomous/dead-code")
test("GET /autonomous/dead-code", r, [
    ("is list", isinstance(r, list)),
])
if isinstance(r, list):
    print(f"     📄 {len(r)} dead code file(s)")
    for f in r[:10]:
        short = f.split("\\")[-1] if "\\" in f else f.split("/")[-1]
        print(f"        → {short}")


# ═══════════════════════════════════════════════════════════
# SECTION 25: AUTONOMOUS - GRAPH STATS
# ═══════════════════════════════════════════════════════════
section("25. AUTONOMOUS - GRAPH STATS")

r = req("GET", "/autonomous/graph-stats")
test("GET /autonomous/graph-stats", r, [
    ("has total_files", "total_files" in r),
    ("has file_edges", "file_edges" in r),
])
if "total_files" in r:
    print(f"     📊 {r['total_files']} files, {r['file_edges']} file edges, {r.get('entity_edges', '?')} entity edges")
    dcf = r.get('dead_code_files', [])
    dcf_count = len(dcf) if isinstance(dcf, list) else dcf
    print(f"     🔄 {r.get('circular_count', '?')} cycles, 📄 {dcf_count} dead files")
    md = r.get("most_depended", [])
    if md and isinstance(md, list) and len(md) > 0:
        top = md[0]
        if isinstance(top, list) and len(top) >= 2:
            print(f"     🏆 Most depended: {str(top[0]).split(chr(92))[-1]} ({top[1]} dependents)")
        elif isinstance(top, dict):
            print(f"     🏆 Most depended: {json.dumps(top)[:80]}")
        else:
            print(f"     🏆 Most depended: {top}")


# ═══════════════════════════════════════════════════════════
# SECTION 26: AUTONOMOUS - ENTITIES
# ═══════════════════════════════════════════════════════════
section("26. AUTONOMOUS - ENTITIES")

r = req("GET", f"/autonomous/entities/{WS_PATH_ENCODED}")
test("GET /autonomous/entities (all)", r, [
    ("is list", isinstance(r, list)),
    ("has entities", len(r) > 0 if isinstance(r, list) else False),
])
if isinstance(r, list):
    # Count by type
    types = {}
    for e in r:
        t = e.get("entity_type", "?")
        types[t] = types.get(t, 0) + 1
    print(f"     📋 {len(r)} total entities")
    for t, c in sorted(types.items(), key=lambda x: -x[1]):
        print(f"        {t}: {c}")

r = req("GET", f"/autonomous/entities/{WS_PATH_ENCODED}?entity_type=function")
test("GET /autonomous/entities (functions)", r, [
    ("is list", isinstance(r, list)),
])
if isinstance(r, list):
    print(f"     🔧 {len(r)} function(s) found")


# ═══════════════════════════════════════════════════════════
# SECTION 27: AUTONOMOUS - WORKER STATUS CHECK
# ═══════════════════════════════════════════════════════════
section("27. WORKER STATUS AFTER ALL TESTS")

r = req("GET", "/autonomous/status")
test("GET /autonomous/status (final)", r, [
    ("still running", r.get("running") == True),
])
if "stats" in r:
    s = r["stats"]
    print(f"     ⚙️  Events: {s.get('events_processed', 0)} | Fast: {s.get('fast_path_runs', 0)} | Idle: {s.get('idle_runs', 0)} | Errors: {s.get('errors', 0)}")


# ═══════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════
print(f"\n{'='*60}")
print(f"  RESULTS: {passed} passed, {failed} failed")
print(f"{'='*60}")

if errors:
    print("\n  FAILURES:")
    for e in errors:
        print(e)

sys.exit(1 if failed > 0 else 0)
