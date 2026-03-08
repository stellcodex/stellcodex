from __future__ import annotations

from typing import Any

from app.knowledge.schemas import MemoryRecord


def enforce_tenant_scope(record: MemoryRecord, tenant_id: str) -> bool:
    if record.tenant_id is None:
        return False
    return str(record.tenant_id) == str(tenant_id)


def record_matches_filters(record: MemoryRecord, filters: dict[str, Any] | None) -> bool:
    if not isinstance(filters, dict):
        return True
    if filters.get("tenant_id") is not None and str(record.tenant_id) != str(filters.get("tenant_id")):
        return False
    if filters.get("project_id") is not None and str(record.project_id) != str(filters.get("project_id")):
        return False
    if filters.get("record_type") is not None and str(record.record_type) != str(filters.get("record_type")):
        return False
    if filters.get("security_class") is not None and str(record.security_class) != str(filters.get("security_class")):
        return False
    source_type = str(record.metadata.get("source_type") or "")
    if filters.get("source_type") is not None and source_type != str(filters.get("source_type")):
        return False
    tags_filter = filters.get("tags")
    if isinstance(tags_filter, list) and tags_filter:
        normalized_record_tags = {str(item) for item in record.tags}
        normalized_filter_tags = {str(item) for item in tags_filter}
        if not (normalized_record_tags & normalized_filter_tags):
            return False
    return True


def allowed_security_classes(filters: dict[str, Any] | None) -> set[str]:
    if not isinstance(filters, dict):
        return {"public", "internal", "restricted", "system"}
    value = filters.get("security_class")
    if isinstance(value, str) and value.strip():
        return {value.strip()}
    if isinstance(value, list):
        out = {str(item).strip() for item in value if str(item).strip()}
        if out:
            return out
    return {"public", "internal", "restricted", "system"}
