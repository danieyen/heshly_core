#!/usr/bin/env python3
"""
Fix LIVE n8n WhatsApp response path via n8n API.
- Backs up current live workflows
- Verifies WF3/1 Switch fallbackOutput and WF4 HTTP neverError
- Fixes BOOK_APPOINTMENT silent-drop (WF3 Prepare guarantee + WF4 neverError)
- Verifies versionId bump and active=true
Requires: N8N_API_KEY env, N8N_API_URL (default https://n8n.heshly.com/api/v1)
Usage: python scripts/fix_live_n8n_whatsapp_response.py [--dry-run]
"""
import os
import sys
import json
import requests
from datetime import datetime
from pathlib import Path

API_URL = os.getenv("N8N_API_URL", "https://n8n.heshly.com/api/v1")
API_KEY = os.getenv("N8N_API_KEY", "")
DRY_RUN = "--dry-run" in sys.argv

WF31_ID = "8f3c2a91-7d64-4e52-b8a1-91c7f4e62d30"
WF4_ID = "37bdbe49-2f7c-44ff-9132-4b2c9e3d33fd"
WF3_ID = "heshly-ai-action-booking-v1"

HEADERS = {"X-N8N-API-KEY": API_KEY, "Content-Type": "application/json", "Accept": "application/json"}

def fail(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)

def api_get(path):
    r = requests.get(f"{API_URL}{path}", headers=HEADERS, timeout=30)
    if r.status_code != 200:
        fail(f"GET {path} failed {r.status_code}: {r.text[:500]}")
    return r.json()

def api_put(path, data):
    r = requests.put(f"{API_URL}{path}", headers=HEADERS, json=data, timeout=30)
    if r.status_code not in (200, 201):
        fail(f"PUT {path} failed {r.status_code}: {r.text[:1000]}")
    return r.json()

def api_post(path, data=None):
    r = requests.post(f"{API_URL}{path}", headers=HEADERS, json=data or {}, timeout=30)
    if r.status_code not in (200, 201, 204):
        fail(f"POST {path} failed {r.status_code}: {r.text[:1000]}")
    try:
        return r.json()
    except:
        return {}

def backup_live(workflows):
    Path("backups").mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    p = Path(f"backups/live_active_workflows_backup_{ts}.json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump(workflows, f, indent=2, ensure_ascii=False)
    print(f"[BACKUP] Saved {len(workflows)} workflows to {p}")
    return p

def find_workflow(workflows, wid):
    for w in workflows:
        if w.get("id") == wid:
            return w
    return None

def get_node(workflow, nid):
    for n in workflow.get("nodes", []):
        if n.get("id") == nid:
            return n
    return None

def check_wf31(workflow):
    n = get_node(workflow, "wf31-switch")
    if not n:
        return False, "node wf31-switch not found"
    fb = n.get("parameters", {}).get("options", {}).get("fallbackOutput", "")
    ok = fb == "unavailable"
    return ok, f"fallbackOutput={repr(fb)} expected 'unavailable'"

def check_wf4_http(workflow):
    n = get_node(workflow, "send-whatsapp-reply")
    if not n:
        return False, "node send-whatsapp-reply not found"
    opts = n.get("parameters", {}).get("options", {})
    resp = opts.get("response", {}).get("response", {})
    never = resp.get("neverError") is True
    always = opts.get("alwaysOutputData") is True
    ok = never and always
    return ok, f"neverError={resp.get('neverError')} alwaysOutputData={opts.get('alwaysOutputData')}"

def check_wf3_prepare(workflow):
    n = get_node(workflow, "wf3-prepare-whatsapp-response")
    if not n:
        return False, "node wf3-prepare-whatsapp-response not found"
    code = n.get("parameters", {}).get("jsCode", "")
    ok = 'if (!response) {' in code and 'I can help you book' in code
    return ok, f"has_final_fallback={ok}"

def fix_wf31(workflow):
    n = get_node(workflow, "wf31-switch")
    if n is None:
        return False
    opts = n.setdefault("parameters", {}).setdefault("options", {})
    if opts.get("fallbackOutput") == "unavailable":
        return False
    opts["fallbackOutput"] = "unavailable"
    print(f"[FIX] WF3/1 wf31-switch fallbackOutput -> 'unavailable'")
    return True

def fix_wf4_http(workflow):
    n = get_node(workflow, "send-whatsapp-reply")
    if n is None:
        return False
    params = n.setdefault("parameters", {})
    opts = params.setdefault("options", {})
    resp = opts.setdefault("response", {}).setdefault("response", {})
    changed = False
    if resp.get("neverError") is not True:
        resp["neverError"] = True
        resp["responseFormat"] = "json"
        changed = True
    if opts.get("alwaysOutputData") is not True:
        opts["alwaysOutputData"] = True
        changed = True
    if changed:
        print(f"[FIX] WF4 send-whatsapp-reply neverError=true alwaysOutputData=true")
    return changed

def fix_wf3_prepare(workflow):
    n = get_node(workflow, "wf3-prepare-whatsapp-response")
    if n is None:
        return False
    code = n.get("parameters", {}).get("jsCode", "")
    if 'if (!response) {' in code and 'I can help you book' in code:
        return False
    # Inject final fallback before appointment_booked block
    old = "const appointment_booked"
    new = 'if (!response) {\n  response = original.response || "I can help you book an appointment. Please share your preferred date (YYYY-MM-DD) and time.";\n}\n\nconst appointment_booked'
    if old in code:
        n["parameters"]["jsCode"] = code.replace(old, new)
        print(f"[FIX] WF3 wf3-prepare-whatsapp-response added final fallback guarantee")
        return True
    return False

def prepare_update_payload(workflow):
    # n8n PUT /workflows/{id} rejects read-only/additional properties:
    # - 400: request/body/active is read-only
    # - 400: request/body/settings must NOT have additional properties
    # For this deployment we only need to update nodes/connections for WF3/1, WF4, WF3.
    # Send minimal payload with only required fields.
    payload = {
        "name": workflow["name"],
        "nodes": workflow["nodes"],
        "connections": workflow["connections"],
    }
    return payload

def main():
    if not API_KEY:
        fail("N8N_API_KEY not set")
    print(f"[INFO] API_URL={API_URL}")
    print(f"[INFO] DRY_RUN={DRY_RUN}")

    # 1. Read CURRENT live workflows
    print("\n=== LIVE BEFORE ===")
    data = api_get("/workflows")
    workflows = data.get("data", data) if isinstance(data, dict) else data
    if isinstance(workflows, dict) and "data" in workflows:
        workflows = workflows["data"]
    print(f"[LIVE] Found {len(workflows)} workflows")
    for w in workflows:
        print(f"  - {w.get('id')} | {w.get('name')} | active={w.get('active')} | versionId={w.get('versionId')}")

    backup_live(workflows)

    wf31_live = api_get(f"/workflows/{WF31_ID}")
    wf4_live = api_get(f"/workflows/{WF4_ID}")
    wf3_live = api_get(f"/workflows/{WF3_ID}")

    # Normalize if API wraps in data
    if isinstance(wf31_live, dict) and "data" in wf31_live and "nodes" not in wf31_live:
        wf31_live = wf31_live["data"]
    if isinstance(wf4_live, dict) and "data" in wf4_live and "nodes" not in wf4_live:
        wf4_live = wf4_live["data"]
    if isinstance(wf3_live, dict) and "data" in wf3_live and "nodes" not in wf3_live:
        wf3_live = wf3_live["data"]

    print(f"\n[CHECK] WF3/1 {WF31_ID} versionId={wf31_live.get('versionId')} active={wf31_live.get('active')}")
    ok31, msg31 = check_wf31(wf31_live)
    print(f"  Switch fallbackOutput: {msg31} -> {'PASS' if ok31 else 'FAIL'}")

    print(f"\n[CHECK] WF4 {WF4_ID} versionId={wf4_live.get('versionId')} active={wf4_live.get('active')}")
    ok4, msg4 = check_wf4_http(wf4_live)
    print(f"  HTTP neverError: {msg4} -> {'PASS' if ok4 else 'FAIL'}")

    print(f"\n[CHECK] WF3 {WF3_ID} versionId={wf3_live.get('versionId')} active={wf3_live.get('active')}")
    ok3, msg3 = check_wf3_prepare(wf3_live)
    print(f"  Prepare fallback: {msg3} -> {'PASS' if ok3 else 'FAIL'}")

    # Also inspect connections for BOOK_APPOINTMENT silent drop
    print("\n[CHECK] WF3 connections BOOK_APPOINTMENT -> Prepare -> WF4")
    conns = wf3_live.get("connections", {})
    has_prepare = "Prepare WhatsApp Response" in conns or "wf3-prepare-whatsapp-response" in str(conns)
    print(f"  Prepare->WF4 connection present: {has_prepare}")

    needs_fix = not (ok31 and ok4 and ok3)
    if not needs_fix:
        print("\n=== LIVE CHANGES MADE: NONE (already correct) ===")
        print("\n=== LIVE AFTER: same as BEFORE ===")
        print("\n=== TEST RESULT: PASS - WhatsApp path guaranteed ===")
        return

    print("\n=== LIVE CHANGES MADE ===")
    changed31 = fix_wf31(wf31_live)
    changed4 = fix_wf4_http(wf4_live)
    changed3 = fix_wf3_prepare(wf3_live)

    if DRY_RUN:
        print("[DRY-RUN] Would PUT updated workflows, skipping")
        print("\n=== LIVE AFTER: DRY-RUN (no change) ===")
        return

    # Deploy via PUT - preserve active state separately (PUT rejects read-only "active")
    if changed31:
        was_active31 = wf31_live.get("active") is True
        payload = prepare_update_payload(wf31_live)
        res = api_put(f"/workflows/{WF31_ID}", payload)
        print(f"[DEPLOY] WF3/1 updated versionId {wf31_live.get('versionId')} -> {res.get('versionId', res.get('data', {}).get('versionId'))}")
        if was_active31 and not res.get("active"):
            api_post(f"/workflows/{WF31_ID}/activate")
            print(f"[ACTIVATE] WF3/1 activated")

    if changed4:
        was_active4 = wf4_live.get("active") is True
        payload = prepare_update_payload(wf4_live)
        res = api_put(f"/workflows/{WF4_ID}", payload)
        print(f"[DEPLOY] WF4 updated versionId {wf4_live.get('versionId')} -> {res.get('versionId', res.get('data', {}).get('versionId'))}")
        if was_active4 and not res.get("active"):
            api_post(f"/workflows/{WF4_ID}/activate")
            print(f"[ACTIVATE] WF4 activated")

    if changed3:
        was_active3 = wf3_live.get("active") is True
        payload = prepare_update_payload(wf3_live)
        res = api_put(f"/workflows/{WF3_ID}", payload)
        print(f"[DEPLOY] WF3 updated versionId {wf3_live.get('versionId')} -> {res.get('versionId', res.get('data', {}).get('versionId'))}")
        if was_active3 and not res.get("active"):
            api_post(f"/workflows/{WF3_ID}/activate")
            print(f"[ACTIVATE] WF3 activated")

    # Verify after
    print("\n=== LIVE AFTER ===")
    wf31_after = api_get(f"/workflows/{WF31_ID}")
    wf4_after = api_get(f"/workflows/{WF4_ID}")
    wf3_after = api_get(f"/workflows/{WF3_ID}")
    if isinstance(wf31_after, dict) and "data" in wf31_after and "nodes" not in wf31_after:
        wf31_after = wf31_after["data"]
    if isinstance(wf4_after, dict) and "data" in wf4_after and "nodes" not in wf4_after:
        wf4_after = wf4_after["data"]
    if isinstance(wf3_after, dict) and "data" in wf3_after and "nodes" not in wf3_after:
        wf3_after = wf3_after["data"]

    print(f"WF3/1 versionId {wf31_after.get('versionId')} active={wf31_after.get('active')}")
    ok31a, msg31a = check_wf31(wf31_after)
    print(f"  Switch: {msg31a} -> {'PASS' if ok31a else 'FAIL'}")

    print(f"WF4 versionId {wf4_after.get('versionId')} active={wf4_after.get('active')}")
    ok4a, msg4a = check_wf4_http(wf4_after)
    print(f"  HTTP: {msg4a} -> {'PASS' if ok4a else 'FAIL'}")

    print(f"WF3 versionId {wf3_after.get('versionId')} active={wf3_after.get('active')}")
    ok3a, msg3a = check_wf3_prepare(wf3_after)
    print(f"  Prepare: {msg3a} -> {'PASS' if ok3a else 'FAIL'}")

    print("\n=== TEST RESULT ===")
    if ok31a and ok4a and ok3a:
        print("PASS - All LIVE fixes verified. WhatsApp response path now guaranteed for CHECK_AVAILABILITY and BOOK_APPOINTMENT (fallback + neverError).")
        print("Next: send live WhatsApp 'book tomorrow' and verify reply received.")
    else:
        print("FAIL - Some fixes still missing, check logs")
        sys.exit(1)

if __name__ == "__main__":
    main()
