"""Comprehensive API test suite for water_analysis project."""
import requests, json, time, sys, os

BASE = "http://localhost:8000"
RESULTS = []
PASS = 0
FAIL = 0
REQ_TIMEOUT = 30  # seconds

def test(name, cond, detail=""):
    global PASS, FAIL
    status = "PASS" if cond else "FAIL"
    if cond: PASS += 1
    else: FAIL += 1
    msg = f"[{status}] {name} {detail}"
    RESULTS.append(msg)
    print(msg, flush=True)
    return cond


print("=" * 60, flush=True)
print("WATER ANALYSIS — COMPREHENSIVE API TEST SUITE", flush=True)
print(f"Target: {BASE}", flush=True)
print("=" * 60, flush=True)

# ═══════════════════════════════════════════
# 1. Health
# ═══════════════════════════════════════════
print("\n--- 1. Health ---", flush=True)
r = requests.get(f"{BASE}/api/health", timeout=REQ_TIMEOUT)
test("Health check", r.json()["status"] == "ok", r.json()["app"])

# ═══════════════════════════════════════════
# 2. Auth
# ═══════════════════════════════════════════
print("\n--- 2. Auth ---", flush=True)
ts = str(int(time.time()))
username = f"tester_{ts}"
password = "test123"

# Register
r = requests.post(f"{BASE}/api/auth/register",
    json={"username": username, "password": password, "email": f"{ts}@test.com"},
    timeout=REQ_TIMEOUT)
reg_data = r.json()
test("Register", reg_data.get("status") == 1, f"user={username}")

# Login
r = requests.post(f"{BASE}/api/auth/login",
    json={"username": username, "password": password}, timeout=REQ_TIMEOUT)
login_data = r.json()
login_ok = test("Login", login_data.get("status") == 1 and "token" in login_data.get("datas", {}))
TOKEN = login_data.get("datas", {}).get("token", "") if login_ok else ""
H = {"Authorization": f"Bearer {TOKEN}"}

# Get me
if TOKEN:
    r = requests.get(f"{BASE}/api/auth/me", headers=H, timeout=REQ_TIMEOUT)
    test("Get current user", r.json().get("status") == 1,
         f"username={r.json().get('datas',dict()).get('username','')}")

# ═══════════════════════════════════════════
# 3. Dashboard
# ═══════════════════════════════════════════
print("\n--- 3. Dashboard ---", flush=True)
r = requests.get(f"{BASE}/api/dashboard/stats", headers=H, timeout=REQ_TIMEOUT)
d = r.json()
dash_ok = test("Dashboard stats", d.get("status") == 1)
if dash_ok:
    dd = d.get("datas", {})
    test("  total_tasks", "total_tasks" in dd, str(dd.get("total_tasks")))
    test("  status_counts", "status_counts" in dd, str(dd.get("status_counts")))
    test("  total_anomalies", "total_anomalies" in dd, str(dd.get("total_anomalies")))
    test("  recent_anomalies", "recent_anomalies" in dd, f"len={len(dd.get('recent_anomalies', []))}")
    test("  anomaly_by_indicator", "anomaly_by_indicator" in dd, str(dd.get("anomaly_by_indicator")))

# ═══════════════════════════════════════════
# 4. Task List
# ═══════════════════════════════════════════
print("\n--- 4. Task List ---", flush=True)
r = requests.get(f"{BASE}/api/tasks?page=1&page_size=5", headers=H, timeout=REQ_TIMEOUT)
d = r.json()
tl_ok = test("Task list basic", d.get("status") == 1)
if tl_ok:
    dd = d.get("datas", {})
    items = dd.get("items", [])
    test("  Has items", len(items) > 0, f"count={len(items)}")
    test("  Has total", dd.get("total", 0) > 0, f"total={dd.get('total')}")
    TASK_ID = items[0]["task_id"] if items else None
else:
    TASK_ID = None

# Filter by status
r = requests.get(f"{BASE}/api/tasks?status=success&page=1&page_size=3", headers=H, timeout=REQ_TIMEOUT)
test("Task filter by status", r.json().get("status") == 1,
     f"total={r.json().get('datas',dict()).get('total',0)}")

# Sort
r = requests.get(f"{BASE}/api/tasks?sort=anomaly_count&order=desc&page=1&page_size=3", headers=H, timeout=REQ_TIMEOUT)
r = requests.get(f"{BASE}/api/tasks?sort=anomaly_count&order=desc&page=1&page_size=3", headers=H, timeout=REQ_TIMEOUT)
sort_json = r.json()
_items = sort_json.get("datas", {}).get("items", [{}])
_first = _items[0].get("anomaly_count", "?") if _items else "?"
test("Task sort by anomaly_count desc", sort_json.get("status") == 1,
     f"first={_first}")
if not TASK_ID:
    print("[SKIP] No tasks in database, skipping task-specific tests", flush=True)
    sys.exit(1)

# ═══════════════════════════════════════════
# 5. Task Status
# ═══════════════════════════════════════════
print("\n--- 5. Task Status ---", flush=True)
r = requests.get(f"{BASE}/api/task/{TASK_ID}/status", headers=H, timeout=REQ_TIMEOUT)
d = r.json()
ts_ok = test("Task status", d.get("status") == 1)
if ts_ok:
    dd = d.get("datas", {})
    test("  task_id", dd.get("task_id") == TASK_ID)
    test("  status field", "status" in dd, dd.get("status"))
    test("  progress field", "progress" in dd, str(dd.get("progress")))

# ═══════════════════════════════════════════
# 6. Task Update
# ═══════════════════════════════════════════
print("\n--- 6. Task Update ---", flush=True)
r = requests.put(f"{BASE}/api/task/{TASK_ID}",
    json={"reservoir_name": "TEST_RESERVOIR"}, headers=H, timeout=REQ_TIMEOUT)
test("Update reservoir_name", r.json().get("status") == 1)

# Verify
r = requests.get(f"{BASE}/api/tasks?page=1&page_size=100&search={TASK_ID}", headers=H, timeout=REQ_TIMEOUT)
items = r.json().get("datas", {}).get("items", [])
updated = [t for t in items if t["task_id"] == TASK_ID]
test("Verify update persisted", len(updated) > 0 and updated[0].get("reservoir_name") == "TEST_RESERVOIR")

# ═══════════════════════════════════════════
# 7. Statistics (Issue A fix)
# ═══════════════════════════════════════════
print("\n--- 7. Statistics (ISSUE A) ---", flush=True)
r = requests.get(f"{BASE}/api/task/{TASK_ID}/statistics", headers=H, timeout=REQ_TIMEOUT)
d = r.json()
stat_ok = test("Get statistics", d.get("status") == 1)
if stat_ok:
    dd = d.get("datas", {})
    indicators = dd.get("indicators", {})
    total_from_indicators = sum(v.get("anomaly_count", 0) for v in indicators.values())
    total_reported = dd.get("total_anomalies", 0)
    match = total_from_indicators == total_reported
    test(f"  Per-indicator sum({total_from_indicators}) == total({total_reported})", match)
    if not match:
        for k, v in indicators.items():
            print(f"    {k}: {v.get('anomaly_count')} (label={v.get('label')})")

# ═══════════════════════════════════════════
# 8. Visualization (Issue B fix)
# ═══════════════════════════════════════════
print("\n--- 8. Visualization (ISSUE B) ---", flush=True)
r = requests.get(f"{BASE}/api/task/{TASK_ID}/visualization?indicator=chlorophyll&depth=1", headers=H, timeout=REQ_TIMEOUT)
d = r.json()
viz_ok = test("Visualization", d.get("status") == 1)
if viz_ok:
    dd = d.get("datas", {})
    html_len = len(dd.get("contour_html", ""))
    test(f"  contour_html NOT inlined (len={html_len})", html_len < 1000, "was ~500KB before fix")
    test("  contour_url present", bool(dd.get("contour_url")))
    test("  grid present", bool(dd.get("grid")))
    test("  depths present", len(dd.get("depths", [])) > 0, str(dd.get("depths")))

# ═══════════════════════════════════════════
# 9. Depth Profile
# ═══════════════════════════════════════════
print("\n--- 9. Depth Profile ---", flush=True)
r = requests.get(f"{BASE}/api/task/{TASK_ID}/depth_profile?indicator=chlorophyll", headers=H, timeout=REQ_TIMEOUT)
d = r.json()
dp_ok = test("Depth profile JSON", d.get("status") == 1)
if dp_ok:
    dd = d.get("datas", {})
    test("  profile layers", len(dd.get("profile", [])) > 0, f"layers={len(dd.get('profile',[]))}")

# ═══════════════════════════════════════════
# 10. Distribution
# ═══════════════════════════════════════════
print("\n--- 10. Distribution ---", flush=True)
for ind in ["chlorophyll", "ph", "temperature"]:
    r = requests.get(f"{BASE}/api/task/{TASK_ID}/distribution?indicator={ind}&bins=20", headers=H, timeout=REQ_TIMEOUT)
    d = r.json()
    ok = d.get("status") == 1
    if ok:
        dd = d.get("datas", {})
        ok = len(dd.get("bins", [])) == 20 and len(dd.get("counts", [])) == 20
    test(f"  Distribution ({ind})", ok)

# ═══════════════════════════════════════════
# 11. Raw Data
# ═══════════════════════════════════════════
print("\n--- 11. Raw Data ---", flush=True)
r = requests.get(f"{BASE}/api/task/{TASK_ID}/raw_data?page=1&page_size=5", headers=H, timeout=REQ_TIMEOUT)
d = r.json()
rd_ok = test("Raw data list", d.get("status") == 1)
if rd_ok:
    dd = d.get("datas", {})
    test("  items count", len(dd.get("items", [])) == 5)
    test("  fields present", len(dd.get("fields", [])) == 10, f"fields={dd.get('fields')}")
    test("  field_labels present", len(dd.get("field_labels", [])) == 10)
    test("  total present", dd.get("total", 0) > 0, f"total={dd.get('total')}")

# Page 2
r = requests.get(f"{BASE}/api/task/{TASK_ID}/raw_data?page=2&page_size=5", headers=H, timeout=REQ_TIMEOUT)
d = r.json()
test("Raw data pagination", d.get("status") == 1 and d.get("datas", {}).get("page") == 2)

# ═══════════════════════════════════════════
# 12. Anomalies
# ═══════════════════════════════════════════
print("\n--- 12. Anomalies ---", flush=True)
r = requests.get(f"{BASE}/api/anomalies?page=1&page_size=5", headers=H, timeout=REQ_TIMEOUT)
d = r.json()
an_ok = test("Anomaly list", d.get("status") == 1)
if an_ok:
    dd = d.get("datas", {})
    test("  items count", len(dd.get("items", [])) > 0, str(len(dd.get("items", []))))
    test("  total present", dd.get("total", 0) > 0, f"total={dd.get('total')}")

# Filter by task_id
r = requests.get(f"{BASE}/api/anomalies?task_id={TASK_ID}&page=1&page_size=3", headers=H, timeout=REQ_TIMEOUT)
d = r.json()
test(f"  Filter by task_id", d.get("status") == 1,
     f"total={d.get('datas',dict()).get('total',0)}")

# Combined filters
r = requests.get(f"{BASE}/api/anomalies?task_id={TASK_ID}&indicator=ph&method=threshold"
    f"&depth_min=0&depth_max=5&value_min=6&value_max=9&page=1&page_size=10", headers=H, timeout=REQ_TIMEOUT)
d = r.json()
test(f"  Multi-filter (indicator+method+depth+value)", d.get("status") == 1,
     f"total={d.get('datas',dict()).get('total',0)}")

# ═══════════════════════════════════════════
# 13. Reports
# ═══════════════════════════════════════════
print("\n--- 13. Reports ---", flush=True)
r = requests.get(f"{BASE}/api/reports", headers=H, timeout=REQ_TIMEOUT)
d = r.json()
test("Report list", d.get("status") == 1,
     f"total={d.get('datas',dict()).get('total',0)}")

r = requests.get(f"{BASE}/api/task/{TASK_ID}/report_status", headers=H, timeout=REQ_TIMEOUT)
d = r.json()
rs_ok = test("Report status", d.get("status") == 1)
if rs_ok:
    dd = d.get("datas", {})
    test("  has_report field", "has_report" in dd, str(dd.get("has_report")))
    test("  generating field", "generating" in dd, str(dd.get("generating")))

# Similar cases
r = requests.post(f"{BASE}/api/task/{TASK_ID}/similar", headers=H, timeout=REQ_TIMEOUT)
d = r.json()
test("Similar cases search", d.get("status") == 1,
     f"similar={len(d.get('datas',dict()).get('similar_tasks',[]))}")

# ═══════════════════════════════════════════
# 14. Contour HTML standalone endpoint
# ═══════════════════════════════════════════
print("\n--- 14. HTML Endpoints ---", flush=True)
r = requests.get(f"{BASE}/api/task/{TASK_ID}/contour_html?indicator=chlorophyll&depth=1", headers=H, timeout=REQ_TIMEOUT)
is_html = r.text.strip().startswith("<")
test(f"  Contour HTML ({len(r.text)} bytes)", is_html)

r = requests.get(f"{BASE}/api/task/{TASK_ID}/depth_profile_html?indicator=chlorophyll", headers=H, timeout=REQ_TIMEOUT)
is_html = r.text.strip().startswith("<")
test(f"  Depth profile HTML ({len(r.text)} bytes)", is_html)

# ═══════════════════════════════════════════
# 15. Report Generation (Issue C fix) — slow, requires Milvus
# ═══════════════════════════════════════════
SKIP_SLOW = os.environ.get("SKIP_SLOW", "") == "1"
if SKIP_SLOW:
    print("\n--- 15. Report Generation (SKIPPED via SKIP_SLOW=1) ---", flush=True)
else:
    print("\n--- 15. Report Generation (ISSUE C) ---", flush=True)
    import subprocess
    reset_result = subprocess.run(["python", "tests/_reset_progress.py", TASK_ID],
                                   capture_output=True, cwd=r"D:\water_analysis", timeout=30)
    print(f"  Reset: {reset_result.stdout.decode('gbk', errors='replace').strip()}", flush=True)

    r = requests.post(f"{BASE}/api/task/{TASK_ID}/generate_report", headers=H, timeout=REQ_TIMEOUT)
    gen_started = r.json().get("status") == 1
    test("Trigger generation", gen_started, r.json().get("messages", ""))

    if gen_started:
        last_prog = -2
        for i in range(1, 11):
            time.sleep(12)
            r = requests.get(f"{BASE}/api/task/{TASK_ID}/report_status", headers=H, timeout=REQ_TIMEOUT)
            dd = r.json().get("datas", {})
            prog = dd.get("progress", -2)
            phase = dd.get("phase", "")
            print(f"  Poll {i} ({i*12}s): progress={prog}, phase={phase[:60]}", flush=True)
            last_prog = prog
            if prog == 100 or prog == -1:
                break

        r = requests.get(f"{BASE}/api/task/{TASK_ID}/report_status", headers=H, timeout=REQ_TIMEOUT)
        dd = r.json().get("datas", {})
        has_report = dd.get("has_report", False)
        final_prog = dd.get("progress", -2)
        test(f"  Report generated: has_report={has_report}, progress={final_prog}",
             has_report and final_prog == 100)

# ═══════════════════════════════════════════
# 16. Error Handling
# ═══════════════════════════════════════════
print("\n--- 16. Error Handling ---", flush=True)
r = requests.get(f"{BASE}/api/task/nonexistent-id-12345/status", headers=H, timeout=REQ_TIMEOUT)
test("404 for missing task", r.json().get("status") == 0, r.json().get("messages", ""))

r = requests.post(f"{BASE}/api/auth/login", json={"username": "nobody", "password": "wrongpassword"}, timeout=REQ_TIMEOUT)
test("401 for bad credentials", r.json().get("status") == 0)

r = requests.get(f"{BASE}/api/tasks?page=0", headers=H, timeout=REQ_TIMEOUT)
test("422 for page=0 validation", r.status_code == 422)

r = requests.get(f"{BASE}/api/task/{TASK_ID}/visualization?indicator=invalid_indicator", headers=H, timeout=REQ_TIMEOUT)
test("400 for invalid indicator", r.json().get("status") == 0)

# ═══════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════
print(f"\n{'=' * 60}", flush=True)
print(f"RESULTS: {PASS} PASS, {FAIL} FAIL, {PASS + FAIL} TOTAL", flush=True)
print(f"{'=' * 60}", flush=True)

if FAIL > 0:
    print("\nFAILURES:", flush=True)
    for r in RESULTS:
        if r.startswith("[FAIL]"):
            print(f"  {r}", flush=True)

print(f"\n{'=' * 60}", flush=True)
sys.exit(0 if FAIL == 0 else 1)
