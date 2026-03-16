import uuid
from datetime import datetime
from uuid import UUID as PyUUID

from sqlalchemy import Boolean, Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.db.base import Base


class RuleConfig(Base):
    __tablename__ = "rule_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = Column(String(128), nullable=False, unique=True, index=True)
    value_json = Column(JSONB, nullable=False, default=dict)
    enabled = Column(Boolean, nullable=False, default=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, onupdate=datetime.utcnow)

    def __init__(self, **kwargs):
        legacy_scope = kwargs.pop("scope", None)
        legacy_scope_id = kwargs.pop("scope_id", None)
        legacy_version = kwargs.pop("version", None)

        value_json = dict(kwargs.get("value_json") or {})
        if legacy_scope is not None and "scope" not in value_json:
            value_json["scope"] = legacy_scope
        if legacy_scope_id is not None and "scope_id" not in value_json:
            value_json["scope_id"] = str(legacy_scope_id)
        if legacy_version is not None and "version" not in value_json:
            value_json["version"] = str(legacy_version)
        kwargs["value_json"] = value_json

        if "enabled" not in kwargs:
            kwargs["enabled"] = True

        super().__init__(**kwargs)

    @property
    def scope(self) -> str:
        payload = self.value_json if isinstance(self.value_json, dict) else {}
        return str(payload.get("scope") or "global")

    @property
    def scope_id(self) -> PyUUID | None:
        payload = self.value_json if isinstance(self.value_json, dict) else {}
        raw = payload.get("scope_id")
        if raw in (None, "", "default"):
            return None
        try:
            return PyUUID(str(raw))
        except (TypeError, ValueError):
            return None

    @property
    def version(self) -> str:
        payload = self.value_json if isinstance(self.value_json, dict) else {}
        if self.key == "rule_version" and payload.get("value") not in (None, ""):
            return str(payload.get("value"))
        return str(payload.get("version") or "v0.0")
