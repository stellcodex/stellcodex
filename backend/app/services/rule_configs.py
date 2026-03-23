from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.hybrid_v1_config import hybrid_v1_config_dict
from app.models.rule_config import RuleConfig

HYBRID_V1_RULE_CONFIG_KEY = "hybrid_v1"
REQUIRED_RULE_KEYS = set(hybrid_v1_config_dict().keys())


class RuleConfigMissingError(RuntimeError):
    pass


def _parse_uuid(value: str | UUID | None) -> UUID | None:
    if value in (None, "", "default"):
        return None
    if isinstance(value, UUID):
        return value
    try:
        return UUID(str(value))
    except (TypeError, ValueError):
        return None


def _merge_config(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        merged[key] = value
    return merged


def _load_rows(db: Session) -> list[RuleConfig]:
    try:
        return list(db.query(RuleConfig).filter(RuleConfig.enabled.is_(True)).all())
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass
        return []


def _apply_rule_row(
    config: dict[str, Any],
    version: str,
    row: RuleConfig,
) -> tuple[dict[str, Any], str]:
    if row.key == HYBRID_V1_RULE_CONFIG_KEY:
        if isinstance(row.value_json, dict):
            config = _merge_config(config, row.value_json)
            version = str(row.version or version)
        return config, version

    payload = row.value_json if isinstance(row.value_json, dict) else {}
    value = payload.get("value")
    payload_version = payload.get("version")

    if row.key == "rule_version":
        if value not in (None, ""):
            version = str(value)
        elif payload_version not in (None, ""):
            version = str(payload_version)
        return config, version

    if row.key in config and value is not None:
        config[row.key] = value
    elif row.key == "allow_hot_runner" and value is not None:
        config["hot_runner"] = "allowed" if bool(value) else "needs_approval"

    if payload_version not in (None, "") and version == "v0.0":
        version = str(payload_version)

    return config, version


def load_hybrid_v1_config(
    db: Session | None,
    *,
    project_id: str | UUID | None = None,
) -> tuple[dict[str, Any], str]:
    config: dict[str, Any] = {}
    version = ""
    if db is None:
        raise RuleConfigMissingError("rule_configs unavailable: database session missing")

    project_uuid = _parse_uuid(project_id)
    rows = _load_rows(db)
    if not rows:
        raise RuleConfigMissingError("rule_configs is empty")

    global_rows: list[RuleConfig] = []
    project_rows: list[RuleConfig] = []
    for row in rows:
        if row.scope == "global":
            global_rows.append(row)
            continue
        if row.scope == "project" and row.scope_id == project_uuid:
            project_rows.append(row)

    for row in global_rows:
        config, version = _apply_rule_row(config, version, row)

    if project_uuid is not None:
        for row in project_rows:
            config, version = _apply_rule_row(config, version, row)

    missing_keys = sorted(REQUIRED_RULE_KEYS.difference(config.keys()))
    if missing_keys:
        raise RuleConfigMissingError(f"rule_configs missing required keys: {', '.join(missing_keys)}")
    if not version:
        raise RuleConfigMissingError("rule_configs missing rule_version")

    return config, version
