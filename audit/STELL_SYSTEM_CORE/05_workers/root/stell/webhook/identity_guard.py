"""
identity_guard.py — STELLCODEX v6.2 Hard Gate
SSOT: /root/workspace/_truth/15_AGENT_GOVERNANCE_AND_IDENTITY.md
SEV-0: Only STELL-AI CORE may write to user-facing channels.
"""

from __future__ import annotations

import json
import re
import uuid
import hashlib
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

log = logging.getLogger("stell.guard")

# ─── Constants ────────────────────────────────────────────────────────────────

CORE_CALLER_ID = "stell_ai_core"

SECURITY_AUDIT_PATH = Path("/root/stell/genois/logs/security_audit.jsonl")

IDENTITY_VIOLATION_PATTERNS = [
    r"ben\s+(stell[\-\s]?ai|core|sistem)",
    r"i\s+am\s+(stell|core|the\s+system)",
    r"system\s+prompt",
    r"\boverride\b",
    r"ignore\s+previous",
    r"founder\s+ad[iı]na",
    r"full\s+access",
    r"ben\s+y[oö]neticiy[iy]m",
]

# ─── Audit Helpers ────────────────────────────────────────────────────────────

def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _load_last_security_hash() -> str:
    """Resume hash chain from last record in security_audit.jsonl after restart."""
    try:
        if SECURITY_AUDIT_PATH.exists():
            lines = SECURITY_AUDIT_PATH.read_text(encoding="utf-8").strip().splitlines()
            for line in reversed(lines):
                try:
                    rec = json.loads(line)
                    h = rec.get("chain_hash", "")
                    if isinstance(h, str) and len(h) == 64:
                        return h
                except Exception:
                    continue
    except Exception:
        pass
    return "0" * 64


_prev_security_hash: str = _load_last_security_hash()


def _write_audit(event_type: str, caller_id: str, reason: str,
                 action_taken: str, agent_id: str = "", job_id: str = "") -> None:
    """Append-only, tamper-evident security audit record (JSONL) with hash chain."""
    global _prev_security_hash
    record = {
        "timestamp": _utc_iso(),
        "event_type": event_type,
        "caller_id": caller_id,
        "agent_id": agent_id,
        "job_id": job_id,
        "reason": reason,
        "action_taken": action_taken,
    }
    # Hash chain: sha256(prev_hash + deterministic record JSON)
    base_str = json.dumps(record, ensure_ascii=False, sort_keys=True)
    new_hash = hashlib.sha256(f"{_prev_security_hash}{base_str}".encode()).hexdigest()
    _prev_security_hash = new_hash
    record["chain_hash"] = new_hash
    try:
        SECURITY_AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with SECURITY_AUDIT_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as exc:
        log.error("Security audit write failed: %s", exc)


def _emit_redis_event(event_type: str, caller_id: str, reason: str) -> None:
    """Emit CloudEvents-compliant security event to Redis stream (best-effort)."""
    try:
        import redis as _redis
        r = _redis.Redis(unix_socket_path="/tmp/redis.sock", decode_responses=True)
        payload = {
            "specversion": "1.0",
            "id": str(uuid.uuid4()),
            "source": "stell-guard",
            "type": event_type,
            "time": _utc_iso(),
            "caller_id": caller_id,
            "reason": reason,
        }
        r.xadd("stell:events:stream", {"data": json.dumps(payload, ensure_ascii=False)})
    except Exception:
        pass  # Redis unavailable → audit log is the primary record


# ─── Core Gate ────────────────────────────────────────────────────────────────

def require_core(caller_id: str) -> None:
    """Raise PermissionError if caller is not STELL-AI CORE.

    Usage (in user-output send path):
        require_core(caller_id)   # raises PermissionError if not core
    """
    if str(caller_id).strip().lower() != CORE_CALLER_ID:
        _write_audit(
            event_type="security.permission_denied",
            caller_id=caller_id,
            reason="require_core: caller is not stell_ai_core",
            action_taken="blocked",
        )
        _emit_redis_event("security.permission_denied", caller_id,
                          "require_core: caller is not stell_ai_core")
        raise PermissionError(
            f"STELL-GUARD: caller_id='{caller_id}' is not authorized to send user output. "
            f"Only '{CORE_CALLER_ID}' may write to user-facing channels."
        )


# ─── Identity Escalation Guard ────────────────────────────────────────────────

def identity_escalation_detected(text: str, caller_id: str = "unknown",
                                  job_id: str = "") -> bool:
    """Return True (and emit security event) if identity escalation detected."""
    lowered = (text or "").lower()
    for pattern in IDENTITY_VIOLATION_PATTERNS:
        if re.search(pattern, lowered):
            _write_audit(
                event_type="security.identity_violation.detected",
                caller_id=caller_id,
                reason=f"pattern matched: {pattern}",
                action_taken="blocked",
                job_id=job_id,
            )
            _emit_redis_event(
                "security.identity_violation.detected",
                caller_id,
                f"pattern matched: {pattern}",
            )
            log.warning("GUARD: identity_violation caller=%s pattern=%s", caller_id, pattern)
            return True
    return False


# ─── Agent Output Validator ───────────────────────────────────────────────────

def parse_agent_report(raw: str, caller_id: str = "unknown") -> dict:
    """Parse and validate agent JSON REPORT. Raises ValueError on invalid output.

    Agents MUST return only structured JSON REPORT — no plain text.
    """
    try:
        data = json.loads(raw)
    except Exception:
        _write_audit(
            event_type="security.agent_output_rejected",
            caller_id=caller_id,
            reason="INVALID_AGENT_OUTPUT: not JSON",
            action_taken="rejected",
        )
        raise ValueError("INVALID_AGENT_OUTPUT: not JSON")

    if not isinstance(data.get("status"), str) or not isinstance(data.get("facts"), list):
        _write_audit(
            event_type="security.agent_output_rejected",
            caller_id=caller_id,
            reason="INVALID_AGENT_OUTPUT: missing required fields (status, facts)",
            action_taken="rejected",
        )
        raise ValueError("INVALID_AGENT_OUTPUT: missing required fields (status, facts)")

    return data


# ─── User Output Hard Gate ────────────────────────────────────────────────────

def guard_user_output(text: str, caller_id: str) -> str:
    """Validate text for user output. Raises on identity escalation.

    Returns the original text if safe.
    """
    if identity_escalation_detected(text, caller_id=caller_id):
        raise PermissionError(
            f"STELL-GUARD: identity escalation detected in output from caller_id='{caller_id}'"
        )
    return text


def send_to_user(
    text: str,
    to: str,
    caller_id: str,
    send_fn,
    media_url: Optional[str] = None,
    media_type: str = "text",
) -> bool:
    """Hard gate for ALL user-facing output.

    Args:
        text:       Message text.
        to:         Recipient (E.164 phone or channel identifier).
        caller_id:  Must equal CORE_CALLER_ID ('stell_ai_core').
        send_fn:    Underlying send function (e.g., send_whatsapp).
        media_url:  Optional media URL.
        media_type: 'text' | 'image' | 'video'.

    Raises:
        PermissionError: If caller_id is not authorized or identity escalation detected.
    """
    # 1. Enforce CORE-only access
    require_core(caller_id)

    # 2. Identity escalation check on outbound text
    guard_user_output(text, caller_id=caller_id)

    # 3. Delegate to actual send
    return send_fn(to, text, media_url, media_type)
