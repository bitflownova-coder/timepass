"""
Copilot Engine — Full Feature Test on bitflow_nova_app
Tests ALL engine features against a real Android/Kotlin project (243 .kt files).
"""
import sys, json, time, urllib.request, urllib.error, os
from typing import Any

BASE = "http://127.0.0.1:7779"
# Auto-detect: bitflow_nova_app should be a sibling of copilot-engine
_REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
WS = os.path.join(_REPO_ROOT, 'bitflow_nova_app')
WS_ENC = urllib.request.pathname2url(WS).lstrip('/')
SAMPLE_KT = os.path.join(WS, 'app', 'src', 'main', 'java', 'com', 'bitflow', 'finance', 'FinanceApp.kt')
SAMPLE_GRADLE = os.path.join(WS, 'app', 'build.gradle.kts')

passed = 0
failed = 0
errors = []

def req(method, path, body=None, timeout=60):
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

def test(name, result, checks):
    global passed, failed
    ok = True
    for desc, c in checks:
        if c:
            passed += 1
        else:
            failed += 1
            ok = False
            errors.append(f"  FAIL [{name}] {desc}")
    s = "PASS" if ok else "FAIL"
    icon = "\u2705" if ok else "\u274c"
    print(f"  {icon} {name}")
    if not ok:
        print(f"     {json.dumps(result, indent=2)[:300]}")

def section(t):
    print(f"\n{'='*60}\n  {t}\n{'='*60}")


# ═══════════════════════════════════════════════════════════
section("1. WORKSPACE REGISTRATION")
# ═══════════════════════════════════════════════════════════
r = req("POST", "/workspace/register", {"path": WS, "name": "bitflow-nova"})
test("Register workspace", r, [
    ("got id", "id" in r),
])

r = req("GET", "/workspaces")
test("List workspaces", r, [
    ("is list", isinstance(r, list)),
    ("bitflow in list", any("bitflow_nova_app" in w.get("path", "").lower() for w in r) if isinstance(r, list) else False),
])


# ═══════════════════════════════════════════════════════════
section("2. STACK DETECTION")
# ═══════════════════════════════════════════════════════════
r = req("POST", "/stack/detect", {"workspace_path": WS})
test("Detect stack", r, [
    ("response ok", "__error__" not in r),
])
rj = json.dumps(r).lower()
# Should detect Kotlin/Android/Gradle
has_kotlin = "kotlin" in rj
has_gradle = "gradle" in rj
has_android = "android" in rj
print(f"     Stack detected: kotlin={has_kotlin}, gradle={has_gradle}, android={has_android}")


# ═══════════════════════════════════════════════════════════
section("3. FILE INDEXING")
# ═══════════════════════════════════════════════════════════
r = req("GET", f"/files/{WS_ENC}")
test("Index files", r, [
    ("has files", "files" in r or isinstance(r, list)),
])
if "files" in r:
    files = r["files"]
    kt_count = sum(1 for f in files if f.get("path", "").endswith(".kt"))
    xml_count = sum(1 for f in files if f.get("path", "").endswith(".xml"))
    gradle_count = sum(1 for f in files if "gradle" in f.get("path", "").lower())
    print(f"     Total files: {len(files)} | .kt: {kt_count} | .xml: {xml_count} | gradle: {gradle_count}")


# ═══════════════════════════════════════════════════════════
section("4. GIT ANALYSIS")
# ═══════════════════════════════════════════════════════════
r = req("GET", f"/git/branch/{WS_ENC}")
test("Git branch", r, [
    ("has branch", "branch" in r),
])
if "branch" in r:
    print(f"     Branch: {r['branch']}")

r = req("GET", f"/git/recent-commits/{WS_ENC}")
test("Git recent commits", r, [
    ("response ok", "__error__" not in r),
])
commits = r.get("commits", r if isinstance(r, list) else [])
if isinstance(commits, list):
    print(f"     Recent commits: {len(commits)}")
    for c in commits[:3]:
        msg = c.get("message", c.get("msg", str(c)))[:60]
        print(f"       - {msg}")

r = req("POST", "/git/diff", {"workspace_path": WS})
test("Git diff", r, [
    ("response ok", "__error__" not in r),
])


# ═══════════════════════════════════════════════════════════
section("5. ERROR PARSING (Kotlin errors)")
# ═══════════════════════════════════════════════════════════
r = req("POST", "/error/parse", {
    "error_text": "e: FinanceApp.kt:42:5: Unresolved reference: hiltModules\njava.lang.NullPointerException: Cannot invoke method on null reference\n    at com.bitflow.finance.FinanceApp.onCreate(FinanceApp.kt:28)",
    "workspace_path": WS
})
test("Parse Kotlin error", r, [
    ("got error_type", "error_type" in r),
    ("got suggestions", "suggestions" in r),
])
if "error_type" in r:
    print(f"     Type: {r['error_type']} | Suggestions: {len(r.get('suggestions', []))}")

r = req("POST", "/error/parse", {
    "error_text": "FAILURE: Build failed with an exception.\n* What went wrong:\nExecution failed for task ':app:kaptDebugKotlin'.\n> A failure occurred while executing org.jetbrains.kotlin.gradle.internal.KaptExecution",
    "workspace_path": WS
})
test("Parse Gradle build error", r, [
    ("got error_type", "error_type" in r),
])
if "error_type" in r:
    print(f"     Type: {r['error_type']}")

r = req("POST", "/error/find-similar", {
    "error_text": "NullPointerException at FinanceApp.kt:28",
    "workspace_path": WS
})
test("Find similar errors", r, [
    ("response ok", "__error__" not in r),
])


# ═══════════════════════════════════════════════════════════
section("6. CONTEXT BUILDING")
# ═══════════════════════════════════════════════════════════
r = req("POST", "/context/build", {
    "workspace_path": WS,
    "current_file": SAMPLE_KT,
    "task": "Fix dependency injection setup in FinanceApp"
})
test("Build context (FinanceApp.kt)", r, [
    ("got prompt", "prompt" in r),
    ("got token_estimate", "token_estimate" in r),
    ("substantial prompt", len(r.get("prompt", "")) > 50),
])
if "token_estimate" in r:
    print(f"     Prompt tokens: ~{r['token_estimate']} | Length: {len(r.get('prompt', ''))} chars")

r = req("POST", "/context/build", {
    "workspace_path": WS,
    "current_file": SAMPLE_GRADLE,
    "task": "Add a new dependency for Retrofit"
})
test("Build context (build.gradle.kts)", r, [
    ("got prompt", "prompt" in r),
])


# ═══════════════════════════════════════════════════════════
section("7. SECURITY SCANNING")
# ═══════════════════════════════════════════════════════════
r = req("POST", "/security/scan", {"file_path": SAMPLE_KT})
test("Scan single file (FinanceApp.kt)", r, [
    ("response ok", "__error__" not in r),
])
if isinstance(r, list):
    print(f"     Findings in FinanceApp.kt: {len(r)}")

r = req("POST", "/security/scan-workspace", {"workspace_path": WS})
test("Scan full workspace", r, [
    ("has scanned data", "scanned_files" in r or "findings" in r or "total_findings" in r or "summary" in r),
])
rj = json.dumps(r)
if "scanned_files" in r:
    print(f"     Scanned: {r['scanned_files']} files")
if "total_findings" in r:
    print(f"     Total findings: {r['total_findings']}")
if "summary" in r:
    s = r["summary"]
    print(f"     Critical: {s.get('critical', 0)} | High: {s.get('high', 0)} | Medium: {s.get('medium', 0)} | Low: {s.get('low', 0)}")


# ═══════════════════════════════════════════════════════════
section("8. BEHAVIOR TRACKING")
# ═══════════════════════════════════════════════════════════
r = req("POST", "/behavior/track", {
    "workspace_path": WS,
    "event": "file_switch",
    "data": {"file": SAMPLE_KT}
})
test("Track file switch", r, [("response ok", "__error__" not in r)])

r = req("POST", "/behavior/track", {
    "workspace_path": WS,
    "event": "error",
    "data": {"error_text": "Unresolved reference: hiltModules"}
})
test("Track error event", r, [("response ok", "__error__" not in r)])

r = req("GET", f"/behavior/status/{WS_ENC}")
test("Behavior status", r, [("response ok", "__error__" not in r)])


# ═══════════════════════════════════════════════════════════
section("9. API DETECTION")
# ═══════════════════════════════════════════════════════════
r = req("POST", "/api/detect", {"workspace_path": WS})
test("Detect APIs", r, [
    ("response ok", "__error__" not in r),
])
endpoints = r.get("endpoints", r if isinstance(r, list) else [])
if isinstance(endpoints, list):
    print(f"     API endpoints detected: {len(endpoints)}")
    for ep in endpoints[:5]:
        print(f"       - {ep.get('method', '?')} {ep.get('path', ep.get('route', str(ep)[:60]))}")


# ═══════════════════════════════════════════════════════════
section("10. SQL ANALYSIS (Room queries)")
# ═══════════════════════════════════════════════════════════
r = req("POST", "/sql/analyze", {
    "query": "SELECT t.*, c.name as categoryName FROM transactions t LEFT JOIN categories c ON t.categoryId = c.id WHERE t.date BETWEEN :startDate AND :endDate ORDER BY t.date DESC",
    "workspace_path": WS
})
test("Analyze Room-style query", r, [("response ok", "__error__" not in r)])

r = req("POST", "/sql/analyze", {
    "query": "DELETE FROM transactions WHERE accountId = :accountId AND date < :cutoff",
    "workspace_path": WS
})
test("Analyze DELETE query", r, [("response ok", "__error__" not in r)])


# ═══════════════════════════════════════════════════════════
section("11. PROMPT OPTIMIZATION")
# ═══════════════════════════════════════════════════════════
r = req("POST", "/prompt/optimize", {
    "task": "Add dark mode support to the finance dashboard screen",
    "workspace_path": WS,
    "current_file": SAMPLE_KT
})
test("Optimize prompt (dark mode)", r, [
    ("has prompt", "prompt" in r or "optimized_prompt" in r),
])

r = req("POST", "/prompt/optimize", {
    "task": "Fix the statement parser for SBI bank format",
    "workspace_path": WS,
    "error_text": "ParseException: Unexpected format in column 3"
})
test("Optimize prompt (parser fix)", r, [
    ("has prompt", "prompt" in r or "optimized_prompt" in r),
])


# ═══════════════════════════════════════════════════════════
section("12. PRISMA ANALYSIS (no Prisma expected)")
# ═══════════════════════════════════════════════════════════
r = req("POST", "/prisma/analyze", {"workspace_path": WS})
test("Prisma analyze (Android proj)", r, [
    ("response ok", "__error__" not in r),
])
print(f"     Result: {json.dumps(r)[:120]}")


# ═══════════════════════════════════════════════════════════
section("13. CONTRACT VALIDATION")
# ═══════════════════════════════════════════════════════════
r = req("POST", "/contracts/validate", {"workspace_path": WS})
test("Validate contracts", r, [("response ok", "__error__" not in r)])
if "issues" in r:
    print(f"     Contract issues: {len(r['issues'])}")

r = req("POST", "/contracts/map", {"workspace_path": WS})
test("Map contracts", r, [("response ok", "__error__" not in r)])


# ═══════════════════════════════════════════════════════════
section("14. IMPACT ANALYSIS")
# ═══════════════════════════════════════════════════════════
r = req("POST", "/impact/build-graph", {"workspace_path": WS})
test("Build impact graph", r, [("response ok", "__error__" not in r)])

r = req("POST", "/impact/analyze", {
    "workspace_path": WS,
    "changed_file": SAMPLE_KT,
    "old_content": "",
    "new_content": ""
})
test("Analyze impact (FinanceApp.kt)", r, [("response ok", "__error__" not in r)])

r = req("POST", "/impact/dependency-map", {"workspace_path": WS})
test("Dependency map", r, [("response ok", "__error__" not in r)])
dep_map = r
if isinstance(dep_map, dict):
    total_deps = sum(len(v) if isinstance(v, list) else 0 for v in dep_map.values())
    print(f"     Files in dep map: {len(dep_map)} | Total edges: {total_deps}")


# ═══════════════════════════════════════════════════════════
section("15. VALIDATION PIPELINE")
# ═══════════════════════════════════════════════════════════
r = req("POST", "/pipeline/full-scan", {"workspace_path": WS}, timeout=120)
test("Full scan pipeline", r, [
    ("has issues or risk", "issues" in r or "risk_score" in r),
])
if "risk_score" in r:
    print(f"     Risk score: {r['risk_score']}")
if "issues" in r:
    by_sev = {}
    for i in r["issues"]:
        s = i.get("severity", "unknown")
        by_sev[s] = by_sev.get(s, 0) + 1
    print(f"     Total issues: {len(r['issues'])} | {by_sev}")

r = req("POST", "/pipeline/file-change", {
    "workspace_path": WS,
    "file_path": SAMPLE_KT,
    "old_content": "",
    "new_content": ""
})
test("File change pipeline", r, [("response ok", "__error__" not in r)])

r = req("POST", "/pipeline/pre-commit", {
    "workspace_path": WS,
    "changed_files": [SAMPLE_KT, SAMPLE_GRADLE]
})
test("Pre-commit check", r, [
    ("has commit_safe", "commit_safe" in r),
])
if "commit_safe" in r:
    print(f"     Commit safe: {r['commit_safe']} | Issues: {len(r.get('issues', []))}")


# ═══════════════════════════════════════════════════════════
section("16. AUTONOMOUS — INITIALIZE WORKSPACE")
# ═══════════════════════════════════════════════════════════
print("  \u23f3 Full index + graph build on 243 Kotlin files... (may take 30-60s)")
r = req("POST", "/autonomous/initialize", {"workspace_path": WS}, timeout=180)
test("Initialize workspace", r, [
    ("initialized", r.get("initialized") == True or r.get("already_initialized") == True),
])
if "steps" in r:
    s = r["steps"]
    idx = s.get("index", {})
    graph = s.get("graph", {})
    snaps = s.get("snapshots", 0)
    risk = s.get("risk", {})
    print(f"     \ud83d\udcca Indexed: {idx.get('indexed', '?')} files, {idx.get('entities_found', '?')} entities")
    print(f"     \ud83d\udd78\ufe0f  Graph: {graph.get('file_edges', '?')} file edges, {graph.get('entity_edges', '?')} entity edges")
    print(f"     \ud83d\udcf8 Snapshots: {snaps}")
    print(f"     \ud83c\udfaf Risk: {risk.get('overall_score', '?')}/10 ({risk.get('health_level', '?')})")


# ═══════════════════════════════════════════════════════════
section("17. AUTONOMOUS — STATUS & CONFIG")
# ═══════════════════════════════════════════════════════════
r = req("GET", "/autonomous/status")
test("Worker status", r, [
    ("running", r.get("running") == True),
])
if "stats" in r:
    s = r["stats"]
    print(f"     Events: {s.get('events_processed', 0)} | Fast: {s.get('fast_path_runs', 0)} | Idle: {s.get('idle_runs', 0)} | Errors: {s.get('errors', 0)}")

r = req("POST", "/autonomous/configure", {
    "workspace_path": WS,
    "idle_interval": 120,
    "debounce_ms": 500
})
test("Configure worker", r, [("idle_interval set", r.get("idle_interval") == 120)])


# ═══════════════════════════════════════════════════════════
section("18. AUTONOMOUS — EVENTS")
# ═══════════════════════════════════════════════════════════
r = req("POST", "/autonomous/event", {
    "file_path": SAMPLE_KT,
    "workspace_path": WS,
    "change_type": "saved",
    "git_branch": "main"
})
test("Event: FinanceApp.kt saved", r, [("queued", r.get("queued") == True)])

r = req("POST", "/autonomous/event", {
    "file_path": SAMPLE_GRADLE,
    "workspace_path": WS,
    "change_type": "saved"
})
test("Event: build.gradle.kts saved", r, [("queued", r.get("queued") == True)])

r = req("POST", "/autonomous/event", {
    "file_path": WS + r"\app\src\main\java\com\bitflow\finance\di\RepositoryModule.kt",
    "workspace_path": WS,
    "change_type": "saved"
})
test("Event: RepositoryModule.kt saved", r, [("queued", r.get("queued") == True)])

print("  \u23f3 Waiting 4s for fast worker to process...")
time.sleep(4)


# ═══════════════════════════════════════════════════════════
section("19. AUTONOMOUS — HEALTH & DASHBOARD")
# ═══════════════════════════════════════════════════════════
r = req("GET", f"/autonomous/health/{WS_ENC}")
test("Health check", r, [
    ("has workspace", "workspace" in r),
    ("has risk_scores", "risk_scores" in r),
    ("has graph", "graph" in r),
    ("has worker", "worker" in r),
])
if "risk_scores" in r:
    rs = r["risk_scores"]
    print(f"     \ud83c\udfaf Overall: {rs.get('overall_score', '?')}/10 ({rs.get('health_level', '?')})")
    print(f"     Schema: {rs.get('schema_risk', '?')} | Contract: {rs.get('contract_risk', '?')} | Drift: {rs.get('drift_risk', '?')}")
    print(f"     Security: {rs.get('security_risk', '?')} | Deps: {rs.get('dependency_risk', '?')} | Migration: {rs.get('migration_risk', '?')}")
    print(f"     Naming: {rs.get('naming_risk', '?')}")
if "worker" in r:
    w = r["worker"]
    print(f"     \u2699\ufe0f Events: {w.get('events_processed', 0)} | Fast: {w.get('fast_path_runs', 0)} | Errors: {w.get('errors', 0)}")


r = req("GET", f"/autonomous/dashboard/{WS_ENC}")
test("Full dashboard", r, [
    ("has health", "health" in r),
    ("has risk_trend", "risk_trend" in r),
    ("has drifts", "unresolved_drifts" in r),
    ("has circular", "circular_dependencies" in r),
    ("has dead_code", "dead_code_files" in r),
    ("has timestamp", "timestamp" in r),
])


# ═══════════════════════════════════════════════════════════
section("20. AUTONOMOUS — RISK TREND")
# ═══════════════════════════════════════════════════════════
r = req("GET", f"/autonomous/risk-trend/{WS_ENC}?limit=20")
test("Risk trend", r, [("is list", isinstance(r, list))])
if isinstance(r, list) and r:
    print(f"     \ud83d\udcc8 {len(r)} points | Latest: {r[-1].get('overall_score', '?')}/10")


# ═══════════════════════════════════════════════════════════
section("21. AUTONOMOUS — DRIFT EVENTS")
# ═══════════════════════════════════════════════════════════
r = req("GET", f"/autonomous/drifts/{WS_ENC}")
test("Unresolved drifts", r, [("is list", isinstance(r, list))])
if isinstance(r, list):
    print(f"     \ud83d\udd04 {len(r)} unresolved drift(s)")
    for d in r[:5]:
        print(f"       - [{d.get('severity', '?')}] {d.get('entity_name', '?')} in {str(d.get('file_path', '?')).split(chr(92))[-1]}: {d.get('drift_type', '?')}")


# ═══════════════════════════════════════════════════════════
section("22. AUTONOMOUS — CIRCULAR DEPENDENCIES")
# ═══════════════════════════════════════════════════════════
r = req("GET", "/autonomous/circular-deps")
test("Circular deps", r, [("is list", isinstance(r, list))])
if isinstance(r, list):
    print(f"     \ud83d\udd04 {len(r)} cycle(s)")
    for c in r[:5]:
        if isinstance(c, list):
            short = [f.split("\\")[-1].split("/")[-1] for f in c]
            print(f"       \u2192 {' \u2192 '.join(short)}")


# ═══════════════════════════════════════════════════════════
section("23. AUTONOMOUS — DEAD CODE")
# ═══════════════════════════════════════════════════════════
r = req("GET", "/autonomous/dead-code")
test("Dead code files", r, [("is list", isinstance(r, list))])
if isinstance(r, list):
    print(f"     \ud83d\udcc4 {len(r)} dead code file(s)")
    for f in r[:15]:
        print(f"       \u2192 {str(f).split(chr(92))[-1].split('/')[-1]}")


# ═══════════════════════════════════════════════════════════
section("24. AUTONOMOUS — GRAPH STATS")
# ═══════════════════════════════════════════════════════════
r = req("GET", "/autonomous/graph-stats")
test("Graph stats", r, [
    ("has total_files", "total_files" in r),
    ("has file_edges", "file_edges" in r),
])
if "total_files" in r:
    print(f"     \ud83d\udcca {r['total_files']} files | {r['file_edges']} file edges | {r.get('entity_edges', '?')} entity edges")
    print(f"     Cycles: {r.get('circular_count', '?')} | Dead files: {r.get('dead_code_files', '?')}")
    md = r.get("most_depended", [])
    if md and isinstance(md, list):
        for item in md[:5]:
            if isinstance(item, list) and len(item) >= 2:
                print(f"     \ud83c\udfc6 {str(item[0]).split(chr(92))[-1]}: {item[1]} dependents")
            elif isinstance(item, dict):
                print(f"     \ud83c\udfc6 {json.dumps(item)[:80]}")


# ═══════════════════════════════════════════════════════════
section("25. AUTONOMOUS — ENTITIES")
# ═══════════════════════════════════════════════════════════
r = req("GET", f"/autonomous/entities/{WS_ENC}")
test("All entities", r, [
    ("is list", isinstance(r, list)),
    ("has entities", len(r) > 0 if isinstance(r, list) else False),
])
if isinstance(r, list):
    types = {}
    for e in r:
        t = e.get("entity_type", "?")
        types[t] = types.get(t, 0) + 1
    print(f"     \ud83d\udccb {len(r)} total entities")
    for t, c in sorted(types.items(), key=lambda x: -x[1]):
        print(f"       {t}: {c}")

r = req("GET", f"/autonomous/entities/{WS_ENC}?entity_type=class")
test("Class entities", r, [("is list", isinstance(r, list))])
if isinstance(r, list):
    print(f"     \ud83c\udfe0 {len(r)} classes found")
    for e in r[:10]:
        print(f"       - {e.get('entity_name', '?')} ({str(e.get('file_path', '?')).split(chr(92))[-1]})")

r = req("GET", f"/autonomous/entities/{WS_ENC}?entity_type=function")
test("Function entities", r, [("is list", isinstance(r, list))])
if isinstance(r, list):
    print(f"     \ud83d\udd27 {len(r)} functions found")


# ═══════════════════════════════════════════════════════════
section("26. CACHE")
# ═══════════════════════════════════════════════════════════
r = req("GET", "/cache/stats")
test("Cache stats", r, [("response ok", "__error__" not in r)])
print(f"     {json.dumps(r)[:200]}")


# ═══════════════════════════════════════════════════════════
section("27. FINAL STATUS")
# ═══════════════════════════════════════════════════════════
r = req("GET", "/autonomous/status")
test("Worker still running", r, [("running", r.get("running") == True)])
if "stats" in r:
    s = r["stats"]
    print(f"     Events: {s.get('events_processed', 0)} | Fast: {s.get('fast_path_runs', 0)} | Idle: {s.get('idle_runs', 0)} | Errors: {s.get('errors', 0)}")

r = req("GET", "/health")
test("Server health", r, [
    ("healthy", r.get("status") == "healthy"),
])
print(f"     Uptime: {r.get('uptime', 0):.0f}s")


# ═══════════════════════════════════════════════════════════
print(f"\n{'='*60}")
print(f"  RESULTS: {passed} passed, {failed} failed out of {passed+failed} checks")
print(f"{'='*60}")
if errors:
    print("\n  FAILURES:")
    for e in errors:
        print(e)

sys.exit(1 if failed > 0 else 0)
