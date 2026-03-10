from __future__ import annotations

from app.tools.registry import ToolRegistry


def register_all_builtins(registry: ToolRegistry) -> None:
    from app.tools.builtins.health_tool import HealthTool
    from app.tools.builtins.files_tool import FilesTool
    from app.tools.builtins.jobs_tool import JobsTool
    from app.tools.builtins.orchestrator_tool import OrchestratorTool
    from app.tools.builtins.dfm_tool import DfmTool
    from app.tools.builtins.knowledge_tool import KnowledgeTool
    from app.tools.builtins.audit_tool import AuditTool
    from app.tools.builtins.report_tool import ReportTool

    for tool in [
        HealthTool(),
        FilesTool(),
        JobsTool(),
        OrchestratorTool(),
        DfmTool(),
        KnowledgeTool(),
        AuditTool(),
        ReportTool(),
    ]:
        registry.register(tool)
