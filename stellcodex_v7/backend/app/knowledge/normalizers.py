from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any

from app.knowledge.types import CanonicalKnowledgeRecord, INDEX_STATUS_PENDING, INDEX_VERSION_DEFAULT


_TOKEN_RE = re.compile(r"[a-z0-9_]+")
_SENSITIVE_KEY_MARKERS = (
    "storage_key",
    "object_key",
    "bucket",
    "revision_id",
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _is_sensitive_key(key: str) -> bool:
    lowered = str(key or "").strip().lower()
    if not lowered:
        return False
    return any(marker in lowered for marker in _SENSITIVE_KEY_MARKERS)


def sanitize_public_payload(payload: Any) -> Any:
    if isinstance(payload, dict):
        out: dict[str, Any] = {}
        for key, value in payload.items():
            text_key = str(key)
            if _is_sensitive_key(text_key):
                continue
            out[text_key] = sanitize_public_payload(value)
        return out
    if isinstance(payload, list):
        return [sanitize_public_payload(item) for item in payload]
    if isinstance(payload, str):
        lowered = payload.lower()
        if "s3://" in lowered or "r2://" in lowered:
            return "[redacted]"
        return payload
    return payload


def summarize_text(text: str, *, max_chars: int = 280) -> str:
    compact = " ".join(str(text or "").split())
    return compact[:max_chars]


def stable_content_hash(*, text: str, metadata: dict[str, Any]) -> str:
    canonical = json.dumps(
        {"text": str(text or ""), "metadata": sanitize_public_payload(metadata)},
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_record_id(*, tenant_id: str, source_ref: str, hash_sha256: str, index_version: str) -> str:
    seed = f"{tenant_id}|{source_ref}|{hash_sha256}|{index_version}".encode("utf-8")
    return "kr_" + hashlib.sha256(seed).hexdigest()[:32]


def canonical_record(
    *,
    tenant_id: str,
    project_id: str | None,
    file_id: str | None,
    source_type: str,
    source_subtype: str,
    source_ref: str,
    title: str,
    text: str,
    metadata: dict[str, Any],
    tags: list[str] | None = None,
    security_class: str = "internal",
    index_version: str = INDEX_VERSION_DEFAULT,
) -> CanonicalKnowledgeRecord:
    clean_metadata = sanitize_public_payload(metadata) if isinstance(metadata, dict) else {}
    normalized_text = str(text or "").strip()
    hash_sha256 = stable_content_hash(text=normalized_text, metadata=clean_metadata)
    record_id = build_record_id(
        tenant_id=str(tenant_id),
        source_ref=str(source_ref),
        hash_sha256=hash_sha256,
        index_version=index_version,
    )
    timestamp = _now_iso()
    return CanonicalKnowledgeRecord(
        record_id=record_id,
        tenant_id=str(tenant_id or "0"),
        project_id=str(project_id) if project_id else None,
        file_id=str(file_id) if file_id else None,
        source_type=str(source_type),
        source_subtype=str(source_subtype),
        source_ref=str(source_ref),
        title=str(title or source_subtype),
        text=normalized_text,
        summary=summarize_text(normalized_text),
        metadata=clean_metadata,
        tags=[str(item) for item in (tags or []) if str(item).strip()],
        security_class=str(security_class or "internal"),
        hash_sha256=hash_sha256,
        index_version=str(index_version or INDEX_VERSION_DEFAULT),
        embedding_status=INDEX_STATUS_PENDING,
        created_at=timestamp,
        updated_at=timestamp,
    )


def _as_list_of_str(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    for item in value:
        text = str(item or "").strip()
        if text:
            out.append(text)
    return out


def _keywords(value: str) -> list[str]:
    return sorted(set(_TOKEN_RE.findall(str(value or "").lower())))


def normalize_decision_json(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("decision_json payload must be an object")
    out = {
        "manufacturing_method": str(payload.get("manufacturing_method") or ""),
        "mode": str(payload.get("mode") or ""),
        "confidence": float(payload.get("confidence") or 0.0),
        "rule_version": str(payload.get("rule_version") or ""),
        "rule_explanations": _as_list_of_str(payload.get("rule_explanations")),
        "conflict_flags": _as_list_of_str(payload.get("conflict_flags")),
        "risk_flags": _as_list_of_str(payload.get("risk_flags")),
    }
    text = json.dumps(out, ensure_ascii=False, sort_keys=True)
    return {
        "title": "Deterministic decision_json",
        "text": text,
        "summary": summarize_text(text),
        "metadata": out,
        "tags": ["decision_json", "deterministic", *(_keywords(out.get("mode", "")))],
    }


def normalize_dfm_report(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("dfm_report payload must be an object")
    risks_raw = payload.get("risks")
    risk_categories: list[str] = []
    severity: list[str] = []
    if isinstance(risks_raw, list):
        for item in risks_raw:
            if not isinstance(item, dict):
                continue
            category = str(item.get("category") or item.get("rule_id") or "").strip()
            sev = str(item.get("severity") or "").strip()
            if category:
                risk_categories.append(category)
            if sev:
                severity.append(sev)
    recommendations = _as_list_of_str(payload.get("recommendations"))
    decision_json = payload.get("decision_json") if isinstance(payload.get("decision_json"), dict) else {}
    out = {
        "risk_categories": sorted(set(risk_categories)),
        "severity": sorted(set(severity)),
        "recommendations": recommendations,
        "mode": str(decision_json.get("mode") or payload.get("mode") or ""),
        "confidence": float(decision_json.get("confidence") or payload.get("confidence") or 0.0),
        "rule_version": str(decision_json.get("rule_version") or payload.get("rule_version") or ""),
    }
    text = json.dumps(out, ensure_ascii=False, sort_keys=True)
    return {
        "title": "Deterministic DFM report",
        "text": text,
        "summary": summarize_text(text),
        "metadata": out,
        "tags": ["dfm_report", "deterministic", *(_keywords(" ".join(out["risk_categories"])))],
    }


def normalize_assembly_meta(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("assembly_meta payload must be an object")
    occurrences = payload.get("occurrences")
    if not isinstance(occurrences, list):
        occurrences = []
    component_names: list[str] = []
    part_identifiers: list[str] = []
    searchable_labels: list[str] = []
    occurrence_tree: dict[str, list[str]] = {}
    for raw in occurrences:
        if not isinstance(raw, dict):
            continue
        node_kind = str(raw.get("node_type") or raw.get("kind") or "").lower()
        name = str(raw.get("name") or raw.get("label") or raw.get("occurrence_id") or "").strip()
        if "mesh" in node_kind or "mesh" in name.lower():
            continue
        occ_id = str(raw.get("occurrence_id") or "").strip()
        parent_id = str(raw.get("parent_occurrence_id") or "root").strip() or "root"
        part_id = str(
            raw.get("part_identifier")
            or raw.get("part_id")
            or raw.get("component_id")
            or raw.get("part_number")
            or ""
        ).strip()
        if name:
            component_names.append(name)
            searchable_labels.append(name.lower())
        if part_id:
            part_identifiers.append(part_id)
            searchable_labels.append(part_id.lower())
        if occ_id:
            occurrence_tree.setdefault(parent_id, []).append(occ_id)
    out = {
        "component_names": sorted(set(component_names)),
        "occurrence_tree": occurrence_tree,
        "part_identifiers": sorted(set(part_identifiers)),
        "searchable_part_labels": sorted(set(searchable_labels)),
    }
    text = json.dumps(out, ensure_ascii=False, sort_keys=True)
    return {
        "title": "Assembly meta",
        "text": text,
        "summary": summarize_text(text),
        "metadata": out,
        "tags": ["assembly_meta", "viewer_ready", "parts"],
    }


def normalize_audit_event(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("audit/event payload must be an object")
    actor = str(payload.get("actor") or payload.get("actor_user_id") or payload.get("actor_anon_sub") or "")
    event_type = str(payload.get("event_type") or payload.get("type") or "")
    file_id = str(payload.get("file_id") or "")
    target_type = "file" if file_id else str(payload.get("target_type") or "event")
    target_id = file_id or str(payload.get("target_id") or payload.get("id") or "")
    timestamp = str(payload.get("timestamp") or payload.get("created_at") or payload.get("time") or "")
    out = {
        "actor": actor,
        "event_type": event_type,
        "target_type": target_type,
        "target_id": target_id,
        "timestamp": timestamp,
    }
    text = json.dumps(out, ensure_ascii=False, sort_keys=True)
    return {
        "title": f"Audit event {event_type or 'unknown'}",
        "text": text,
        "summary": summarize_text(text),
        "metadata": out,
        "tags": ["audit_event", *(["approval"] if event_type.startswith("approval.") else [])],
    }


def normalize_rule_config(*, key: str, value_json: dict[str, Any], updated_at: str | None = None) -> dict[str, Any]:
    payload = value_json if isinstance(value_json, dict) else {}
    out = {
        "threshold_key": str(key or ""),
        "scope": str(payload.get("scope") or "global"),
        "value": payload.get("value", payload),
        "version": str(payload.get("version") or updated_at or ""),
    }
    text = json.dumps(out, ensure_ascii=False, sort_keys=True)
    return {
        "title": f"Rule config {out['threshold_key']}",
        "text": text,
        "summary": summarize_text(text),
        "metadata": out,
        "tags": ["rule_config", "threshold"],
    }


def normalize_document(*, path: str, content: str) -> dict[str, Any]:
    text = str(content or "").strip()
    if not text:
        raise ValueError("document is empty")
    metadata = {"path": str(path)}
    return {
        "title": f"Document {path}",
        "text": text,
        "summary": summarize_text(text),
        "metadata": metadata,
        "tags": ["document", *_keywords(path)],
    }
