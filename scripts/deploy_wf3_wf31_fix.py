#!/usr/bin/env python3
"""
DEPLOYMENT AUTHORIZATION — MINIMAL FIX ONLY
Targets:
  WF3/1 8f3c2a91-7d64-4e52-b8a1-91c7f4e62d30
  WF3   heshly-ai-action-booking-v1

Steps:
 1. GET live state for both workflows (id, active, versionId, activeVersionId, nodes, connections)
 2. Backup live definitions
 3. Fix WF3/1 Switch — Availability Status to handle ERPNext message wrapper
 4. Fix WF3 Prepare WhatsApp Response to be case-robust + final fallback
 5. Verify connections preserved
 6. PUT minimally (name, nodes, connections, settings:{executionOrder})
 7. Activate only targets if needed
 8. Verify live state
 9. Production-safe test via PRODUCTION webhook (Meta-shaped payload)
10. Final report

Requires: N8N_API_KEY, N8N_API_URL (default https://n8n.heshly.com)
Usage: N8N_API_KEY=... python scripts/deploy_wf3_wf31_fix.py
       N8N_API_KEY=... python scripts/deploy_wf3_wf31_fix.py --dry-run
"""
import os
import sys
import json
import time
import requests
from datetime import datetime
from pathlib import Path

API_URL = os.getenv("N8N_API_URL", "https://n8n.heshly.com/api/v1")
API_KEY = os.getenv("N8N_API_KEY", "")
DRY_RUN = "--dry-run" in sys.argv
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://n8n.heshly.com/webhook/heshly/whatsapp/incoming")

WF31_ID = "8f3c2a91-7d64-4e52-b8a1-91c7f4e62d30"
WF3_ID_OR_NAME = "heshly-ai-action-booking-v1"
WF1_ID = "9db30e75-031f-4a83-83d6-2face7441ba0"

HEADERS = {"X-N8N-API-KEY": API_KEY, "Content-Type": "application/json", "Accept": "application/json"}

def fail(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)

def api_get(path):
    r = requests.get(f"{API_URL}{path}", headers=HEADERS, timeout=30)
    if r.status_code != 200:
        fail(f"GET {path} failed {r.status_code}: {r.text[:2000]}")
    return r.json()

def api_put(path, data):
    r = requests.put(f"{API_URL}{path}", headers=HEADERS, json=data, timeout=30)
    if r.status_code not in (200, 201):
        fail(f"PUT {path} failed {r.status_code}: {r.text[:3000]}")
    return r.json()

def api_post(path, data=None):
    r = requests.post(f"{API_URL}{path}", headers=HEADERS, json=data or {}, timeout=30)
    if r.status_code not in (200, 201, 204):
        fail(f"POST {path} failed {r.status_code}: {r.text[:3000]}")
    try:
        return r.json()
    except:
        return {}

def unwrap(data):
    if isinstance(data, dict) and "data" in data and "nodes" not in data:
        return data["data"]
    return data

def get_workflow_by_id_or_name(identifier):
    # Try direct GET by ID first
    try:
        w = api_get(f"/workflows/{identifier}")
        w = unwrap(w)
        if w.get("id"):
            return w
    except SystemExit:
        pass
    # Fallback: list and find by name or id
    data = api_get("/workflows")
    workflows = data.get("data", data) if isinstance(data, dict) else data
    if isinstance(workflows, dict) and "data" in workflows:
        workflows = workflows["data"]
    for w in workflows:
        if w.get("id") == identifier or w.get("name") == identifier:
            # Fetch full definition
            full = api_get(f"/workflows/{w.get('id')}")
            return unwrap(full)
    fail(f"Workflow not found: {identifier}")

def get_node(workflow, nid):
    for n in workflow.get("nodes", []):
        if n.get("id") == nid:
            return n
    return None

def find_node_by_name(workflow, name_substr):
    for n in workflow.get("nodes", []):
        if name_substr.lower() in n.get("name", "").lower():
            return n
    return None

def backup_workflow(workflow, suffix):
    Path("backups").mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    p = Path(f"backups/live_{workflow.get('id')}_{suffix}_{ts}.json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)
    print(f"[BACKUP] {workflow.get('id')} -> {p}")
    return p

def prepare_update_payload(workflow):
    # Minimal valid payload per n8n API: name, nodes, connections, settings:{executionOrder}
    # Do NOT send: active, id, versionId, createdAt, updatedAt, staticData, pinData, binaryMode
    settings = workflow.get("settings") or {}
    execution_order = settings.get("executionOrder") or "v1"
    return {
        "name": workflow["name"],
        "nodes": workflow["nodes"],
        "connections": workflow["connections"],
        "settings": {"executionOrder": execution_order},
    }

def fix_wf31_switch(workflow):
    n = get_node(workflow, "wf31-switch")
    if not n:
        n = find_node_by_name(workflow, "Switch — Availability Status")
    if not n:
        fail("WF3/1 Switch — Availability Status not found")
    print(f"[FIX WF3/1] Found node: {n.get('id')} | {n.get('name')}")
    params = n.setdefault("parameters", {})
    rules = params.setdefault("rules", {}).setdefault("values", [])
    # Ensure 2 rules exist
    if len(rules) < 2:
        fail(f"WF3/1 Switch expected 2 rules, found {len(rules)}")
    # Fix leftValue to handle message wrapper, compare as STRING
    for rule in rules:
        conds = rule.get("conditions", {}).get("conditions", [])
        for c in conds:
            c["leftValue"] = "={{ String($json.message?.available ?? $json.available) }}"
            # Ensure operator is string equals
            op = c.setdefault("operator", {})
            op["type"] = "string"
            op["operation"] = "equals"
        # Ensure rightValue is string "true"/"false"
        if rule.get("outputKey") == "available":
            for c in rule.get("conditions", {}).get("conditions", []):
                c["rightValue"] = "true"
        elif rule.get("outputKey") == "unavailable":
            for c in rule.get("conditions", {}).get("conditions", []):
                c["rightValue"] = "false"
    # Set fallbackOutput to unavailable
    opts = params.setdefault("options", {})
    before = opts.get("fallbackOutput")
    opts["fallbackOutput"] = "unavailable"
    print(f"[FIX WF3/1] fallbackOutput: {repr(before)} -> 'unavailable'")
    print(f"[FIX WF3/1] leftValue -> String($json.message?.available ?? $json.available) STRING compare")
    return True

def fix_wf3_prepare(workflow):
    n = get_node(workflow, "wf3-prepare-whatsapp-response")
    if not n:
        n = find_node_by_name(workflow, "Prepare WhatsApp Response")
    if not n:
        fail("WF3 Prepare WhatsApp Response not found")
    print(f"[FIX WF3] Found node: {n.get('id')} | {n.get('name')}")
    # Robust code handling case-insensitive action and string/boolean available, plus final fallback
    robust_code = """const action = $input.first().json || {};
const original = $("Set — Normalize Action Input").item.json || {};

let response = action.message || action.response || original.response || "";

const actionName = String(
  action.action || action.next_action || original.next_action || ""
).toUpperCase();

const available =
  action.available === true ||
  String(action.available).toLowerCase() === "true";

const unavailable =
  action.available === false ||
  String(action.available).toLowerCase() === "false";

if (!response && actionName === "CHECK_AVAILABILITY") {
  if (available && Array.isArray(action.slots) && action.slots.length) {
    response = `The requested service is available. Available times: ${action.slots.join(", ")}`;
  } else if (unavailable) {
    response = "Unfortunately, that time is not available.";
  }
}

if (!response && actionName === "BOOK_APPOINTMENT") {
  if (action.success === true || String(action.success).toLowerCase() === "true") {
    response = action.message || "Your appointment has been booked successfully.";
  } else if (action.success === false || String(action.success).toLowerCase() === "false") {
    response = action.message || "Sorry, we could not book your appointment. Please try another time.";
  }
}

if (!response && actionName === "UPDATE_LEAD_CUSTOMER") {
  if (action.success === true || String(action.success).toLowerCase() === "true") {
    response = action.message || "Your details have been updated successfully.";
  }
}

if (!response) {
  response = original.response || "I can help you book an appointment. Please share your preferred date (YYYY-MM-DD) and time.";
}

const appointment_booked = !!(action.success === true && action.appointment_id);
const appointment_id = action.appointment_id || null;
const appointment_conversion = appointment_id ? { appointment_id, service: action.service || original.service || "", scheduled_time: action.scheduled_time || null } : null;
const conversion_outcome = appointment_booked ? "appointment_booked" : "";

return [{
  json: {
    business: original.business || {},
    customer: original.customer || {},
    lead: original.lead || {},
    conversation: original.conversation || {},
    response,
    intent: original.intent || "",
    next_action: original.next_action || action.next_action || action.action || "OTHER",
    phone_number: original.phone_number || "",
    phone_number_id: original.phone_number_id || "",
    tenant_id: original.tenant_id || original.business?.tenant_id || original.business?.id || "",
    appointment_booked,
    appointment_id,
    appointment_conversion,
    conversion_outcome,
    action_result: action
  }
}];"""
    before = n.get("parameters", {}).get("jsCode", "")[:120]
    n.setdefault("parameters", {})["jsCode"] = robust_code
    print(f"[FIX WF3] jsCode replaced (before snippet: {repr(before[:80])}...)")
    print(f"[FIX WF3] Now uses String(action.action).toUpperCase() === \"CHECK_AVAILABILITY\" and String(action.available).toLowerCase() === \"true\" + final fallback")
    return True

def verify_connections_wf31(workflow):
    conns = workflow.get("connections", {})
    sw = conns.get("Switch — Availability Status", {})
    if not sw:
        print("[WARN] WF3/1 connections missing Switch — Availability Status")
        return False
    mains = sw.get("main", [])
    ok = len(mains) == 2
    if ok:
        print(f"[VERIFY WF3/1] Switch outputs: {len(mains)} -> Return — Available / Return — Unavailable OK")
        # Check fallback is set
        n = get_node(workflow, "wf31-switch")
        fb = n.get("parameters", {}).get("options", {}).get("fallbackOutput")
        print(f"[VERIFY WF3/1] fallbackOutput={repr(fb)}")
    else:
        print(f"[VERIFY WF3/1] FAIL: expected 2 outputs, got {len(mains)}")
    return ok

def verify_connections_wf3(workflow):
    conns = workflow.get("connections", {})
    # Check Execute WF3/1 -> Prepare
    found = False
    for src, dests in conns.items():
        if "WF3/1" in src:
            mains = dests.get("main", [])
            for branch in mains:
                for conn in branch:
                    if "Prepare WhatsApp Response" in conn.get("node", ""):
                        found = True
    if found:
        print("[VERIFY WF3] Execute Workflow — WF3/1 -> Prepare WhatsApp Response OK")
    else:
        print("[WARN] WF3 connection Execute WF3/1 -> Prepare not found (checking alternative)")
        # Alternative check via string search
        if "Prepare WhatsApp Response" in json.dumps(conns):
            print("[VERIFY WF3] Prepare connection present via string search")
            found = True
    return found

def main():
    if not API_KEY:
        fail("N8N_API_KEY not set")
    print(f"[INFO] API_URL={API_URL}")
    print(f"[INFO] WEBHOOK_URL={WEBHOOK_URL}")
    print(f"[INFO] DRY_RUN={DRY_RUN}")

    # STEP 1 — READ LIVE STATE
    print("\n=== STEP 1 — READ LIVE STATE ===")
    wf31_live = get_workflow_by_id_or_name(WF31_ID)
    wf3_live = get_workflow_by_id_or_name(WF3_ID_OR_NAME)
    wf1_live = get_workflow_by_id_or_name(WF1_ID)

    for w in [wf31_live, wf3_live, wf1_live]:
        print(f"  {w.get('id')} | {w.get('name')} | active={w.get('active')} | versionId={w.get('versionId')} | activeVersionId={w.get('activeVersionId', 'N/A')}")

    # Record relevant nodes
    print("\n[WF3/1 nodes]")
    for n in wf31_live.get("nodes", []):
        if "Switch" in n.get("name", "") or "Check Availability" in n.get("name", "") or "Return" in n.get("name", ""):
            print(f"  - {n.get('id')} | {n.get('name')} | type={n.get('type')}")
            if "Switch" in n.get("name", ""):
                print(f"    params: {json.dumps(n.get('parameters', {}).get('options', {}))}")
                print(f"    rules: {json.dumps(n.get('parameters', {}).get('rules', {}), indent=6)[:2000]}")

    print("\n[WF3 nodes]")
    for n in wf3_live.get("nodes", []):
        if "Prepare" in n.get("name", "") or "Normalize Action" in n.get("name", "") or "WF3/1" in n.get("name", ""):
            print(f"  - {n.get('id')} | {n.get('name')} | type={n.get('type')}")
            if "Prepare" in n.get("name", ""):
                code = n.get("parameters", {}).get("jsCode", "")
                print(f"    jsCode snippet: {code[:300].replace(chr(10), ' | ')}...")

    print("\n[WF3/1 connections]")
    print(json.dumps(wf31_live.get("connections", {}), indent=2))
    print("\n[WF3 connections]")
    print(json.dumps(wf3_live.get("connections", {}), indent=2))

    # STEP 2 — BACKUP
    print("\n=== STEP 2 — BACKUP LIVE DEFINITIONS ===")
    backup_workflow(wf31_live, "before")
    backup_workflow(wf3_live, "before")
    backup_workflow(wf1_live, "before_no_change")

    # STEP 3 & 4 — FIX
    print("\n=== STEP 3 — FIX WF3/1 ONLY ===")
    fix_wf31_switch(wf31_live)

    print("\n=== STEP 4 — FIX WF3 ONLY ===")
    fix_wf3_prepare(wf3_live)

    # STEP 5 — PRESERVE CONNECTIONS
    print("\n=== STEP 5 — VERIFY CONNECTIONS PRESERVED ===")
    verify_connections_wf31(wf31_live)
    verify_connections_wf3(wf3_live)

    if DRY_RUN:
        print("\n[DRY-RUN] Would PUT workflows, skipping deployment")
        print("\n=== STEP 8 — VERIFY LIVE STATE (DRY-RUN, no change) ===")
        return

    # STEP 6 — DEPLOY MINIMALLY
    print("\n=== STEP 6 — DEPLOY MINIMALLY ===")
    # WF3/1 first (leaf, no dependency on WF3)
    was_active31 = wf31_live.get("active") is True
    payload31 = prepare_update_payload(wf31_live)
    print(f"[PUT] WF3/1 {WF31_ID} payload keys: {list(payload31.keys())} settings={payload31['settings']}")
    res31 = api_put(f"/workflows/{WF31_ID}", payload31)
    print(f"[PUT OK] WF3/1 versionId {wf31_live.get('versionId')} -> {res31.get('versionId', unwrap(res31).get('versionId'))}")

    was_active3 = wf3_live.get("active") is True
    payload3 = prepare_update_payload(wf3_live)
    print(f"[PUT] WF3 {wf3_live.get('id')} payload keys: {list(payload3.keys())} settings={payload3['settings']}")
    res3 = api_put(f"/workflows/{wf3_live.get('id')}", payload3)
    print(f"[PUT OK] WF3 versionId {wf3_live.get('versionId')} -> {res3.get('versionId', unwrap(res3).get('versionId'))}")

    # Verify after PUT
    print("\n[VERIFY AFTER PUT]")
    wf31_after = unwrap(api_get(f"/workflows/{WF31_ID}"))
    wf3_after = unwrap(api_get(f"/workflows/{wf3_live.get('id')}"))
    # Check fixes exist
    n31 = get_node(wf31_after, "wf31-switch") or find_node_by_name(wf31_after, "Switch — Availability Status")
    fb = n31.get("parameters", {}).get("options", {}).get("fallbackOutput")
    lv = n31.get("parameters", {}).get("rules", {}).get("values", [{}])[0].get("conditions", {}).get("conditions", [{}])[0].get("leftValue")
    print(f"  WF3/1 fallbackOutput={repr(fb)} leftValue={repr(lv)} -> {'PASS' if fb=='unavailable' and 'message?.available' in lv else 'FAIL'}")
    n3 = get_node(wf3_after, "wf3-prepare-whatsapp-response") or find_node_by_name(wf3_after, "Prepare WhatsApp Response")
    code_after = n3.get("parameters", {}).get("jsCode", "")
    ok_code = 'String(action.action).toUpperCase() === "CHECK_AVAILABILITY"' in code_after or 'actionName === "CHECK_AVAILABILITY"' in code_after
    ok_fallback = 'I can help you book an appointment' in code_after
    print(f"  WF3 Prepare robust check: {ok_code} final fallback: {ok_fallback} -> {'PASS' if ok_code and ok_fallback else 'FAIL'}")

    # STEP 7 — ACTIVATE ONLY TARGETS
    print("\n=== STEP 7 — ACTIVATE ONLY TARGETS ===")
    # Check if activation needed (PUT deactivates if was active)
    wf31_check = unwrap(api_get(f"/workflows/{WF31_ID}"))
    wf3_check = unwrap(api_get(f"/workflows/{wf3_live.get('id')}"))
    if was_active31 and not wf31_check.get("active"):
        print(f"[ACTIVATE] WF3/1 was active, now inactive -> POST /workflows/{WF31_ID}/activate")
        api_post(f"/workflows/{WF31_ID}/activate")
    else:
        print(f"[ACTIVATE] WF3/1 active={wf31_check.get('active')} (was_active={was_active31}) -> no action needed")
    if was_active3 and not wf3_check.get("active"):
        print(f"[ACTIVATE] WF3 was active, now inactive -> POST /workflows/{wf3_live.get('id')}/activate")
        api_post(f"/workflows/{wf3_live.get('id')}/activate")
    else:
        print(f"[ACTIVATE] WF3 active={wf3_check.get('active')} (was_active={was_active3}) -> no action needed")
    print("[SKIP] WF1 not activated (already healthy)")
    print("[SKIP] WF4/WF5 not activated (not required for this fix)")

    # STEP 8 — VERIFY LIVE STATE
    print("\n=== STEP 8 — VERIFY LIVE STATE ===")
    wf31_final = unwrap(api_get(f"/workflows/{WF31_ID}"))
    wf3_final = unwrap(api_get(f"/workflows/{wf3_live.get('id')}"))
    print(f"WF3/1: id={wf31_final.get('id')} active={wf31_final.get('active')} versionId={wf31_final.get('versionId')} activeVersionId={wf31_final.get('activeVersionId', 'N/A')}")
    print(f"WF3:   id={wf3_final.get('id')} active={wf3_final.get('active')} versionId={wf3_final.get('versionId')} activeVersionId={wf3_final.get('activeVersionId', 'N/A')}")
    # Confirm fixes in active version
    n31f = get_node(wf31_final, "wf31-switch") or find_node_by_name(wf31_final, "Switch — Availability Status")
    print(f"  WF3/1 Switch fallbackOutput={repr(n31f.get('parameters', {}).get('options', {}).get('fallbackOutput'))}")
    n3f = get_node(wf3_final, "wf3-prepare-whatsapp-response") or find_node_by_name(wf3_final, "Prepare WhatsApp Response")
    print(f"  WF3 Prepare contains final fallback: {'I can help you book' in n3f.get('parameters', {}).get('jsCode', '')}")

    # STEP 9 — PRODUCTION-SAFE TEST
    print("\n=== STEP 9 — PRODUCTION-SAFE TEST (PRODUCTION webhook) ===")
    payload = {
        "entry": [{
            "changes": [{
                "value": {
                    "metadata": {"phone_number_id": "1192499907286007"},
                    "contacts": [{"profile": {"name": "Dan Test"}, "wa_id": "254700000000"}],
                    "messages": [{"from": "254700000000", "id": f"test-{int(time.time())}", "type": "text", "text": {"body": "I'd like to book an appointment tomorrow."}}]
                }
            }]
        }]
    }
    print(f"[TEST] POST {WEBHOOK_URL}")
    print(f"[TEST] payload phone_number_id=1192499907286007 phone=254700000000 text=\"I'd like to book an appointment tomorrow.\"")
    try:
        r = requests.post(WEBHOOK_URL, json=payload, timeout=30)
        print(f"[TEST] Webhook response: {r.status_code} {r.text[:1000]}")
    except Exception as e:
        print(f"[TEST] Webhook POST failed: {e}")
        print("[TEST] Will still inspect recent executions")

    # Poll executions
    print("\n[TEST] Polling recent executions (waiting 8s for async chain)...")
    time.sleep(8)
    for wid, name in [(WF1_ID, "WF1"), (wf3_final.get('id'), "WF3"), (WF31_ID, "WF3/1")]:
        try:
            data = api_get(f"/executions?limit=5&workflowId={wid}")
            execs = data.get("data", data) if isinstance(data, dict) else data
            if isinstance(execs, dict) and "data" in execs:
                execs = execs["data"]
            print(f"\n  {name} {wid} recent executions:")
            for ex in execs[:3]:
                print(f"    id={ex.get('id')} status={ex.get('status')} startedAt={ex.get('startedAt')} stoppedAt={ex.get('stoppedAt')} workflowVersionId={ex.get('workflowVersionId')}")
                # Fetch execution detail for latest
                if ex == execs[0]:
                    try:
                        detail = api_get(f"/executions/{ex.get('id')}")
                        detail = unwrap(detail)
                        # Try to extract node execution summary
                        nodes_data = detail.get("data", {}).get("resultData", {}).get("runData", {})
                        if nodes_data:
                            print(f"      nodes executed: {list(nodes_data.keys())}")
                            # Check WF3/1 Switch output
                            if wid == WF31_ID:
                                for node_name, runs in nodes_data.items():
                                    if "Switch" in node_name:
                                        for run in runs:
                                            out = run.get("data", {}).get("main", [])
                                            print(f"      Switch output branches: {len(out)} (expected 2, one with data)")
                                            for i, branch in enumerate(out):
                                                print(f"        branch {i}: {len(branch) if branch else 0} items")
                                    if "HTTP Request" in node_name:
                                        for run in runs:
                                            data_main = run.get("data", {}).get("main", [])
                                            if data_main and data_main[0]:
                                                j = data_main[0][0].get("json", {})
                                                print(f"      HTTP response keys: {list(j.keys())[:10]} message keys: {list(j.get('message', {}).keys()) if isinstance(j.get('message'), dict) else 'N/A'}")
                            if wid == wf3_final.get('id'):
                                for node_name, runs in nodes_data.items():
                                    if "Prepare WhatsApp Response" in node_name:
                                        for run in runs:
                                            data_main = run.get("data", {}).get("main", [])
                                            if data_main and data_main[0]:
                                                j = data_main[0][0].get("json", {})
                                                print(f"      Prepare response: {repr(j.get('response', '')[:200])}")
                                                print(f"      Prepare executed: YES")
                                            else:
                                                print(f"      Prepare executed: NO (no output)")
                    except Exception as e:
                        print(f"      detail fetch failed: {e}")
        except Exception as e:
            print(f"  {name} poll failed: {e}")

    # STEP 10 — FINAL REPORT
    print("\n=== STEP 10 — FINAL REPORT ===")
    print("1. exact changes deployed:")
    print("   - WF3/1 wf31-switch: leftValue -> String($json.message?.available ?? $json.available) STRING compare, rightValue true/false, fallbackOutput -> unavailable")
    print("   - WF3 wf3-prepare-whatsapp-response: String(action.action).toUpperCase() === CHECK_AVAILABILITY, String(action.available).toLowerCase() === true, final fallback response")
    print(f"2. WF3 active version: versionId={wf3_final.get('versionId')} activeVersionId={wf3_final.get('activeVersionId', 'N/A')} active={wf3_final.get('active')}")
    print(f"3. WF3/1 active version: versionId={wf31_final.get('versionId')} activeVersionId={wf31_final.get('activeVersionId', 'N/A')} active={wf31_final.get('active')}")
    print("4. test execution IDs: see polling output above")
    print("5. whether WF3/1 returned an item: see Switch output branches above (expected 1 branch with 1 item)")
    print("6. whether Prepare WhatsApp Response executed: see Prepare response above")
    print("7. final response generated: see Prepare response above")
    print("8. any remaining error: if Switch still [] then fallback not live; if Prepare not executed then WF3/1 still returns 0 items")

if __name__ == "__main__":
    main()
