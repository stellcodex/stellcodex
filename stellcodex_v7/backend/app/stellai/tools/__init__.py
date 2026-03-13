from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from sqlalchemy.orm import Session

from app.core.orchestrator import ensure_session_decision
from app.models.file import UploadFile
from app.stellai.retrieval import RetrievalEngine
from app.stellai.tools.audit import ToolAuditLogger
from app.stellai.tools.security import ToolSecurityPolicy
from app.stellai.tools_registry import ToolDefinition, ToolRegistry, register_default_tools
from app.stellai.types import RuntimeContext, ToolExecution

GLOBAL_ALLOWLIST: frozenset[str] = frozenset(
    {
        "runtime.echo",
        "upload.status",
        "upload.decision",
        "orchestrator.recompute",
        "system_info",
        "runtime_status",
        "process_status",
        "disk_usage",
        "read_file",
        "write_file",
        "list_directory",
        "search_files",
        "csv_reader",
        "data_summary",
        "data_filter",
        "json_transform",
        "mesh_info",
        "mesh_volume",
        "mesh_surface_area",
        "mesh_bounds",
        "cad_load",
        "mesh_analyze",
        "volume_compute",
        "surface_area_compute",
        "feature_extract",
        "dfm_precheck",
        "doc_search",
        "repo_search",
        "knowledge_lookup",
        "text_summary",
    }
)


@dataclass
class ToolCall:
    name: str
    params: dict[str, Any]


class SafeToolExecutor:
    def __init__(
        self,
        *,
        allowlist: frozenset[str] | None = None,
        registry: ToolRegistry | None = None,
        retrieval_engine: RetrievalEngine | None = None,
        security_policy: ToolSecurityPolicy | None = None,
        audit_logger: ToolAuditLogger | None = None,
    ) -> None:
        self.retrieval_engine = retrieval_engine or RetrievalEngine()
        self.security_policy = security_policy or ToolSecurityPolicy()
        self.audit_logger = audit_logger or ToolAuditLogger()
        self.registry = registry or ToolRegistry()

        register_default_tools(
            self.registry,
            retrieval_engine=self.retrieval_engine,
            security_policy=self.security_policy,
        )
        self._bind_executor_core_handlers()
        registered_tools = {item.name for item in self.registry.list_tools(include_disabled=False)}
        default_allowlist = GLOBAL_ALLOWLIST & registered_tools
        self.allowlist = allowlist or frozenset(default_allowlist)

    def execute_calls(
        self,
        *,
        context: RuntimeContext,
        db: Session | None,
        calls: list[ToolCall],
    ) -> list[ToolExecution]:
        outputs: list[ToolExecution] = []
        for call in calls:
            outputs.append(self._execute_one(context=context, db=db, call=call))
        return outputs

    def list_tools(self, *, include_disabled: bool = False) -> list[dict[str, Any]]:
        return [item.to_dict() for item in self.registry.list_tools(include_disabled=include_disabled)]

    def _execute_one(self, *, context: RuntimeContext, db: Session | None, call: ToolCall) -> ToolExecution:
        tool_name = str(call.name or "").strip()
        if not tool_name:
            return self._error_result(tool_name=tool_name, status="denied", reason="missing_tool_name")

        params = call.params if isinstance(call.params, dict) else {}
        definition = self.registry.get_tool(tool_name)
        is_registered = definition is not None
        if not is_registered:
            definition = self._fallback_definition(tool_name)

        if tool_name not in self.allowlist:
            result = self._error_result(tool_name=tool_name, status="denied", reason="tool_not_allowlisted")
            self._audit(context=context, db=db, definition=definition, result=result, params=params)
            return result

        if not is_registered:
            result = self._error_result(tool_name=tool_name, status="denied", reason="tool_not_implemented")
            self._audit(context=context, db=db, definition=definition, result=result, params=params)
            return result

        if not definition.enabled:
            result = self._error_result(tool_name=tool_name, status="denied", reason="tool_disabled")
            self._audit(context=context, db=db, definition=definition, result=result, params=params)
            return result

        if definition.tenant_required and not str(context.tenant_id or "").strip():
            result = self._error_result(tool_name=tool_name, status="denied", reason="invalid_tenant_context")
            self._audit(context=context, db=db, definition=definition, result=result, params=params)
            return result

        if not self._is_tool_permitted_for_request(context=context, definition=definition):
            result = self._error_result(tool_name=tool_name, status="denied", reason="tool_not_permitted_for_request")
            self._audit(context=context, db=db, definition=definition, result=result, params=params)
            return result

        try:
            result = definition.handler(context, db, params)
            if not isinstance(result, ToolExecution):
                result = self._error_result(tool_name=tool_name, status="failed", reason="invalid_handler_output")
        except Exception:
            result = self._error_result(tool_name=tool_name, status="failed", reason="tool_error")

        self._audit(context=context, db=db, definition=definition, result=result, params=params)
        return result

    def _is_tool_permitted_for_request(self, *, context: RuntimeContext, definition: ToolDefinition) -> bool:
        requested = context.allowed_tools
        if definition.name in requested:
            return True
        if definition.permission_scope and definition.permission_scope in requested:
            return True
        if definition.permission_scope and f"scope:{definition.permission_scope}" in requested:
            return True
        if definition.category and f"category:{definition.category}" in requested:
            return True
        return False

    def _audit(
        self,
        *,
        context: RuntimeContext,
        db: Session | None,
        definition: ToolDefinition,
        result: ToolExecution,
        params: dict[str, Any],
    ) -> None:
        if not definition.audit_logging:
            return
        self.audit_logger.log_tool_result(
            context=context,
            definition=definition,
            db=db,
            status=result.status,
            reason=result.reason,
            params=params,
            output=result.output if isinstance(result.output, dict) else {},
        )

    @staticmethod
    def _fallback_definition(tool_name: str) -> ToolDefinition:
        return ToolDefinition(
            name=tool_name,
            description="fallback unknown tool definition",
            input_schema={},
            output_schema={},
            permission_scope="stellai.unknown",
            tenant_required=False,
            handler=lambda context, db, params: ToolExecution(
                tool_name=tool_name,
                status="denied",
                reason="tool_not_implemented",
            ),
            category="unknown",
            audit_logging=True,
            enabled=True,
        )

    def _bind_executor_core_handlers(self) -> None:
        mapping = {
            "runtime.echo": self._handle_runtime_echo,
            "upload.status": self._handle_upload_status,
            "upload.decision": self._handle_upload_decision,
            "orchestrator.recompute": self._handle_orchestrator_recompute,
        }
        for name, handler in mapping.items():
            definition = self.registry.get_tool(name)
            if definition is None:
                continue
            self.registry.register_tool(replace(definition, handler=handler))

    @staticmethod
    def _error_result(*, tool_name: str, status: str, reason: str) -> ToolExecution:
        return ToolExecution(
            tool_name=tool_name,
            status=status,
            reason=reason,
            output={"error": {"reason": reason}},
        )

    def _resolve_file_id(self, context: RuntimeContext, params: dict[str, Any]) -> str | None:
        explicit = str(params.get("file_id") or "").strip()
        if explicit:
            return explicit
        if context.file_ids:
            return context.file_ids[0]
        return None

    def _load_upload(self, db: Session | None, file_id: str) -> UploadFile | None:
        if db is None:
            return None
        return db.query(UploadFile).filter(UploadFile.file_id == file_id).first()

    def _validate_tenant(self, context: RuntimeContext, row: UploadFile) -> bool:
        return str(row.tenant_id) == str(context.tenant_id)

    def _handle_runtime_echo(self, context: RuntimeContext, db: Session | None, params: dict[str, Any]) -> ToolExecution:
        return ToolExecution(
            tool_name="runtime.echo",
            status="ok",
            output={
                "tenant_id": context.tenant_id,
                "project_id": context.project_id,
                "session_id": context.session_id,
                "message": str(params.get("message") or ""),
            },
        )

    def _handle_upload_status(self, context: RuntimeContext, db: Session | None, params: dict[str, Any]) -> ToolExecution:
        file_id = self._resolve_file_id(context, params)
        if not file_id:
            return ToolExecution(tool_name="upload.status", status="denied", reason="missing_file_id")
        row = self._load_upload(db, file_id)
        if row is None:
            return ToolExecution(tool_name="upload.status", status="failed", reason="file_not_found")
        if not self._validate_tenant(context, row):
            return ToolExecution(tool_name="upload.status", status="denied", reason="tenant_mismatch")
        return ToolExecution(
            tool_name="upload.status",
            status="ok",
            output={
                "file_id": row.file_id,
                "status": str(row.status),
                "original_filename": row.original_filename,
                "updated_at": row.updated_at.isoformat() if row.updated_at else None,
            },
        )

    def _handle_upload_decision(self, context: RuntimeContext, db: Session | None, params: dict[str, Any]) -> ToolExecution:
        file_id = self._resolve_file_id(context, params)
        if not file_id:
            return ToolExecution(tool_name="upload.decision", status="denied", reason="missing_file_id")
        row = self._load_upload(db, file_id)
        if row is None:
            return ToolExecution(tool_name="upload.decision", status="failed", reason="file_not_found")
        if not self._validate_tenant(context, row):
            return ToolExecution(tool_name="upload.decision", status="denied", reason="tenant_mismatch")
        decision = row.decision_json if isinstance(row.decision_json, dict) else {}
        return ToolExecution(
            tool_name="upload.decision",
            status="ok",
            output={
                "file_id": row.file_id,
                "state": str(decision.get("state") or decision.get("state_code") or ""),
                "approval_required": bool(decision.get("approval_required")),
                "risk_flags": decision.get("risk_flags") if isinstance(decision.get("risk_flags"), list) else [],
                "decision_json": decision,
            },
        )

    def _handle_orchestrator_recompute(
        self,
        context: RuntimeContext,
        db: Session | None,
        params: dict[str, Any],
    ) -> ToolExecution:
        file_id = self._resolve_file_id(context, params)
        if db is None:
            return ToolExecution(tool_name="orchestrator.recompute", status="failed", reason="db_unavailable")
        if not file_id:
            return ToolExecution(tool_name="orchestrator.recompute", status="denied", reason="missing_file_id")
        row = self._load_upload(db, file_id)
        if row is None:
            return ToolExecution(tool_name="orchestrator.recompute", status="failed", reason="file_not_found")
        if not self._validate_tenant(context, row):
            return ToolExecution(tool_name="orchestrator.recompute", status="denied", reason="tenant_mismatch")
        session, decision = ensure_session_decision(db, row)
        return ToolExecution(
            tool_name="orchestrator.recompute",
            status="ok",
            output={
                "file_id": row.file_id,
                "session_id": str(session.id),
                "state": str(decision.get("state") or ""),
                "approval_required": bool(decision.get("approval_required")),
            },
        )
