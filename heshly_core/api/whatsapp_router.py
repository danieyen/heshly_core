from __future__ import annotations

import json
from typing import Any

import frappe


CENTRAL_PHONE_NUMBER_ID = "1192499907286007"
EXISTING_N8N_WEBHOOK = "https://n8n.heshly.com/webhook/heshly/whatsapp/incoming"


def _raw_body() -> bytes:
    data = getattr(getattr(frappe, "request", None), "data", None)

    if isinstance(data, bytes):
        return data

    if isinstance(data, str):
        return data.encode("utf-8")

    payload = getattr(frappe, "request", None)
    payload = getattr(payload, "json", None)

    if payload is not None:
        return json.dumps(
            payload,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")

    return b""


def _headers() -> dict[str, str]:
    request = getattr(frappe, "request", None)
    headers = getattr(request, "headers", {}) or {}

    return {str(k).lower(): str(v) for k, v in headers.items()}


def _extract_waba_id(payload: Any) -> str | None:
    """Extract top-level WABA ID (entry[0].id) for observability only."""
    if not isinstance(payload, dict):
        return None
    entry = payload.get("entry")
    if isinstance(entry, list) and entry:
        first = entry[0]
        if isinstance(first, dict):
            wid = first.get("id")
            if wid:
                return str(wid).strip()
    return None


def _extract_phone_number_id(payload: Any) -> str | None:
    if not isinstance(payload, dict):
        return None

    entry = payload.get("entry")

    if isinstance(entry, list) and entry:
        first_entry = entry[0]

        if isinstance(first_entry, dict):
            changes = first_entry.get("changes")

            if isinstance(changes, list) and changes:
                change = changes[0]

                if isinstance(change, dict):
                    value = change.get("value")

                    if isinstance(value, dict):
                        metadata = value.get("metadata")

                        if isinstance(metadata, dict):
                            phone_number_id = metadata.get("phone_number_id")

                            if phone_number_id:
                                return str(phone_number_id).strip()

                        phone_number_id = value.get("phone_number_id")

                        if phone_number_id:
                            return str(phone_number_id).strip()

    phone_number_id = payload.get("phone_number_id") or payload.get("phoneNumberId")

    if phone_number_id:
        return str(phone_number_id).strip()

    return None


def _json_payload() -> dict:
    request = getattr(frappe, "request", None)

    try:
        payload = request.get_json(silent=True)

        if isinstance(payload, dict):
            return payload
    except Exception:
        pass

    raw = _raw_body()

    if raw:
        try:
            payload = json.loads(raw.decode("utf-8"))

            if isinstance(payload, dict):
                return payload
        except Exception:
            pass

    return {}


def _resolve_number_meta(phone_number_id: str | None, waba_id: str | None) -> dict:
    """Best-effort lookup for observability — never blocks routing. No secrets."""
    out: dict = {"found": False, "tenant_id": None, "business_id": None, "waba_id_match": None}
    if not phone_number_id:
        return out
    try:
        row = frappe.db.get_value(
            "Heshly WhatsApp Number",
            {"phone_number_id": str(phone_number_id).strip(), "active": 1},
            ["tenant_id", "business_id", "waba_id", "phone_number", "connection_status"],
            as_dict=True,
        )
        if row:
            out["found"] = True
            out["tenant_id"] = str(row.tenant_id or "").strip() or None
            out["business_id"] = str(row.business_id or "").strip() or None
            out["waba_id_stored"] = str(row.waba_id or "").strip() or None
            out["phone_number"] = str(row.phone_number or "").strip() or None
            out["connection_status"] = str(row.connection_status or "").strip() or None
            if waba_id:
                out["waba_id_match"] = (str(row.waba_id or "").strip() == str(waba_id).strip())
            # also fetch config business_account_id for comparison
            try:
                cfg = frappe.db.get_value(
                    "Heshly WhatsApp Configuration",
                    {"phone_number_id": str(phone_number_id).strip(), "active": 1},
                    ["business_account_id", "display_phone_number"],
                    as_dict=True,
                )
                if cfg:
                    out["config_waba_id"] = str(cfg.business_account_id or "").strip() or None
            except Exception:
                pass
    except Exception:
        pass
    return out


def _set_json_response(data: dict, status_code: int = 200):
    frappe.local.response.http_status_code = status_code
    frappe.local.response["type"] = "json"
    frappe.local.response["message"] = data


@frappe.whitelist(allow_guest=True)
def whatsapp_router():
    """
    Permanent Heshly WhatsApp ingress router.

    Central Heshly number:
        Meta -> Layer 2 Network webhook

    Every other Heshly/client number:
        Meta -> existing n8n WF1 webhook

    WF1-WF6 are intentionally untouched.
    """

    request = getattr(frappe, "request", None)
    method = str(getattr(request, "method", "POST") or "POST").upper()

    # Meta webhook verification.
    if method == "GET":
        mode = (
            frappe.form_dict.get("hub.mode")
            or frappe.form_dict.get("hub_mode")
            or frappe.form_dict.get("mode")
            or ""
        )

        challenge = (
            frappe.form_dict.get("hub.challenge")
            or frappe.form_dict.get("hub_challenge")
            or frappe.form_dict.get("challenge")
            or ""
        )

        if mode == "subscribe" and challenge:
            # Meta expects raw challenge string as text/plain (not JSON).
            # Returning a Werkzeug Response bypasses frappe.utils.response.build_response
            # and is handled directly in frappe.handler.handle / frappe.api.handle.
            from werkzeug.wrappers import Response

            return Response(str(challenge), content_type="text/plain", status=200)

        _set_json_response(
            {
                "success": False,
                "message": "Verification failed",
            },
            403,
        )
        return

    if method != "POST":
        _set_json_response(
            {
                "success": False,
                "message": "Method not allowed",
            },
            405,
        )
        return

    payload = _json_payload()
    phone_number_id = _extract_phone_number_id(payload)
    waba_id = _extract_waba_id(payload)

    # Targeted observability — never log tokens/secrets.
    try:
        # Lightweight request trace for debugging Meta -> ERPNext delivery.
        # Keep payload keys only, not full body, to avoid PII explosion.
        keys = list(payload.keys()) if isinstance(payload, dict) else []
        entry_keys = []
        try:
            e0 = payload.get("entry", [{}])[0] if isinstance(payload.get("entry"), list) and payload.get("entry") else {}
            if isinstance(e0, dict):
                entry_keys = list(e0.keys())
        except Exception:
            entry_keys = []
        res_meta = _resolve_number_meta(phone_number_id, waba_id)
        frappe.logger("heshly_whatsapp_router").info(
            "whatsapp_router ingress method=%s phone_number_id=%s waba_id=%s keys=%s entry_keys=%s resolved=%s",
            method, phone_number_id, waba_id, keys, entry_keys, res_meta
        )
    except Exception:
        pass

    if not phone_number_id:
        try:
            frappe.logger("heshly_whatsapp_router").warning("whatsapp_router missing phone_number_id waba_id=%s", waba_id)
        except Exception:
            pass
        _set_json_response(
            {
                "success": False,
                "message": "phone_number_id not found in WhatsApp webhook payload",
            },
            400,
        )
        return

    # ------------------------------------------------------------
    # CENTRAL HESHLY NUMBER -> LAYER 2
    # ------------------------------------------------------------
    if phone_number_id == CENTRAL_PHONE_NUMBER_ID:
        try:
            frappe.logger("heshly_whatsapp_router").info(
                "whatsapp_router route=central phone_number_id=%s waba_id=%s forwarding to heshly_network_webhook",
                phone_number_id, waba_id
            )
        except Exception:
            pass
        from heshly_core.api.network_webhook import heshly_network_webhook

        try:
            result = heshly_network_webhook(payload)
        except Exception as exc:
            try:
                frappe.logger("heshly_whatsapp_router").error("whatsapp_router central handler exception phone_number_id=%s err=%s", phone_number_id, str(exc)[:500])
            except Exception:
                pass
            raise
        try:
            # Log outcome without PII/secrets
            frappe.logger("heshly_whatsapp_router").info(
                "whatsapp_router central result phone_number_id=%s success=%s mode=%s network_conversation_id=%s",
                phone_number_id, str((result or {}).get("success")) if isinstance(result, dict) else "unknown",
                str((result or {}).get("mode", "")) if isinstance(result, dict) else "",
                str((result or {}).get("network_conversation_id", "")) if isinstance(result, dict) else "",
            )
        except Exception:
            pass

        if isinstance(result, dict):
            _set_json_response(result, 200)
        else:
            _set_json_response(
                {
                    "success": True,
                    "message": "Network webhook processed",
                    "result": result,
                },
                200,
            )

        return

    # ------------------------------------------------------------
    # ALL EXISTING CLIENT NUMBERS -> EXISTING WF1
    # ------------------------------------------------------------
    try:
        import requests

        try:
            frappe.logger("heshly_whatsapp_router").info(
                "whatsapp_router route=layer1 phone_number_id=%s waba_id=%s forwarding to n8n %s",
                phone_number_id, waba_id, EXISTING_N8N_WEBHOOK
            )
        except Exception:
            pass

        raw = _raw_body()

        headers = _headers()

        forward_headers = {
            "Content-Type": headers.get(
                "content-type",
                "application/json",
            ),
        }

        signature = headers.get("x-hub-signature-256")

        if signature:
            forward_headers["X-Hub-Signature-256"] = signature

        response = requests.post(
            EXISTING_N8N_WEBHOOK,
            data=raw if raw else json.dumps(
                payload,
                separators=(",", ":"),
                ensure_ascii=False,
            ).encode("utf-8"),
            headers=forward_headers,
            timeout=20,
        )
        try:
            frappe.logger("heshly_whatsapp_router").info(
                "whatsapp_router layer1 upstream_status=%s ok=%s phone_number_id=%s",
                response.status_code, response.ok, phone_number_id
            )
        except Exception:
            pass

        try:
            result = response.json()
        except Exception:
            result = {
                "success": response.ok,
                "message": response.text[:1000],
            }

        _set_json_response(
            {
                "success": response.ok,
                "route": "layer1",
                "phone_number_id": phone_number_id,
                "upstream_status": response.status_code,
                "result": result,
            },
            200 if response.ok else 502,
        )

    except Exception as exc:
        try:
            frappe.logger("heshly_whatsapp_router").error("whatsapp_router layer1 forward failed phone_number_id=%s err=%s", phone_number_id, str(exc)[:500])
        except Exception:
            pass
        frappe.log_error(
            title="Heshly WhatsApp Router Error",
            message=str(exc),
        )

        _set_json_response(
            {
                "success": False,
                "route": "layer1",
                "phone_number_id": phone_number_id,
                "message": "Failed to forward webhook to existing WhatsApp pipeline",
            },
            502,
        )
