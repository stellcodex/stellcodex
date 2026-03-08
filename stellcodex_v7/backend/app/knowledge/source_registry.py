from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceRegistryItem:
    source_type: str
    input_format: str
    parser: str
    security_class_default: str
    chunk_strategy: str
    enabled: bool
    version: str


SOURCE_REGISTRY: dict[str, SourceRegistryItem] = {
    "ssot_markdown": SourceRegistryItem(
        source_type="ssot_markdown",
        input_format="md",
        parser="markdown_parser",
        security_class_default="internal",
        chunk_strategy="heading_aware",
        enabled=True,
        version="v1",
    ),
    "report_json": SourceRegistryItem(
        source_type="report_json",
        input_format="json",
        parser="json_parser",
        security_class_default="internal",
        chunk_strategy="json_block",
        enabled=True,
        version="v1",
    ),
    "audit_event": SourceRegistryItem(
        source_type="audit_event",
        input_format="json",
        parser="json_parser",
        security_class_default="restricted",
        chunk_strategy="json_block",
        enabled=True,
        version="v1",
    ),
    "decision_record": SourceRegistryItem(
        source_type="decision_record",
        input_format="json",
        parser="json_parser",
        security_class_default="restricted",
        chunk_strategy="json_block",
        enabled=True,
        version="v1",
    ),
    "dfm_report": SourceRegistryItem(
        source_type="dfm_report",
        input_format="json",
        parser="json_parser",
        security_class_default="internal",
        chunk_strategy="json_block",
        enabled=True,
        version="v1",
    ),
    "solved_case": SourceRegistryItem(
        source_type="solved_case",
        input_format="md",
        parser="markdown_parser",
        security_class_default="internal",
        chunk_strategy="heading_aware",
        enabled=True,
        version="v1",
    ),
    "ops_log": SourceRegistryItem(
        source_type="ops_log",
        input_format="log",
        parser="log_parser",
        security_class_default="system",
        chunk_strategy="log_block",
        enabled=True,
        version="v1",
    ),
    "imported_doc": SourceRegistryItem(
        source_type="imported_doc",
        input_format="text",
        parser="text_parser",
        security_class_default="internal",
        chunk_strategy="default",
        enabled=True,
        version="v1",
    ),
}


def get_source_registry_item(source_type: str) -> SourceRegistryItem:
    key = str(source_type or "").strip().lower()
    item = SOURCE_REGISTRY.get(key)
    if item is None:
        raise ValueError(f"unsupported source_type: {source_type}")
    if not item.enabled:
        raise ValueError(f"source_type is disabled: {source_type}")
    return item


def list_source_registry() -> list[dict]:
    return [item.__dict__.copy() for item in SOURCE_REGISTRY.values()]
