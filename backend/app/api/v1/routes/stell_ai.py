from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.format_registry import get_rule_for_filename
from app.core.ids import format_scx_file_id, normalize_scx_file_id, normalize_scx_id
from app.core.storage import get_s3_client
from app.db.session import get_db
from app.models.file import UploadFile as UploadFileModel
from app.security.deps import Principal, get_current_principal
from app.services.web_knowledge import search_technical_references

router = APIRouter(prefix="/stell-ai", tags=["stell-ai"])

_PLUGIN_REGISTRY_PATH = Path(__file__).resolve().parents[3] / "data" / "stell_ai_plugins.json"

AGENT_CATALOG: list[dict[str, Any]] = [
    {
        "agent_id": "geometry_agent",
        "name": "Geometry Agent",
        "description": "Interprets CAD geometry, bbox, topology and assembly metadata.",
        "capabilities": ["geometry", "bbox", "assembly", "feature-extraction"],
    },
    {
        "agent_id": "manufacturing_agent",
        "name": "Manufacturing Agent",
        "description": "Evaluates DFM findings (draft, wall thickness, undercut, complexity).",
        "capabilities": ["dfm", "manufacturing", "tooling-risk"],
    },
    {
        "agent_id": "cad_repair_agent",
        "name": "CAD Repair Agent",
        "description": "Suggests conversion and artifact-repair actions when viewer contracts are incomplete.",
        "capabilities": ["repair", "conversion", "artifact-validation"],
    },
    {
        "agent_id": "document_agent",
        "name": "Document Agent",
        "description": "Extracts document/archive-level metadata for engineering records.",
        "capabilities": ["document-summary", "metadata", "archive-preview"],
    },
    {
        "agent_id": "web_research_agent",
        "name": "Web Research Agent",
        "description": "Retrieves external technical references to support engineering reasoning.",
        "capabilities": ["web-knowledge", "reference-search"],
    },
    {
        "agent_id": "data_analysis_agent",
        "name": "Data Analysis Agent",
        "description": "Produces deterministic file/data quality and sizing summaries.",
        "capabilities": ["data-profile", "statistics", "quality-check"],
    },
]


class KnowledgeSearchIn(BaseModel):
    query: str = Field(min_length=2, max_length=240)
    max_results: int = Field(default=5, ge=1, le=10)


class AgentRunIn(BaseModel):
    agent_id: str = Field(min_length=2, max_length=64)
    file_id: str | None = None
    prompt: str | None = Field(default=None, max_length=2000)
    include_web_context: bool = False
    web_query: str | None = Field(default=None, max_length=240)


class AgentTaskIn(BaseModel):
    agent_id: str = Field(min_length=2, max_length=64)
    file_id: str | None = None
    prompt: str | None = Field(default=None, max_length=2000)


class AgentOrchestrateIn(BaseModel):
    tasks: list[AgentTaskIn] = Field(default_factory=list, min_length=1, max_length=8)
    include_web_context: bool = False
    web_query: str | None = Field(default=None, max_length=240)


class PluginRegisterIn(BaseModel):
    plugin_id: str = Field(min_length=2, max_length=64, pattern=r"^[a-z0-9_\-]+$")
    name: str = Field(min_length=2, max_length=120)
    plugin_type: str = Field(min_length=2, max_length=48)
    description: str = Field(min_length=2, max_length=500)
    entrypoint: str = Field(min_length=2, max_length=240)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_file_uuid(value: str) -> UUID:
    try:
        return normalize_scx_file_id(value)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid file id")


def _public_file_id(value: str) -> str:
    try:
        return normalize_scx_id(value)
    except ValueError:
        return value


def _get_file_by_identifier(db: Session, value: str) -> UploadFileModel | None:
    uid = _normalize_file_uuid(value)
    canonical = format_scx_file_id(uid)
    legacy = str(uid)
    return db.query(UploadFileModel).filter(UploadFileModel.file_id.in_((canonical, legacy))).first()


def _assert_file_access(f: UploadFileModel, principal: Principal) -> None:
    if principal.typ == "guest":
        owner_sub = principal.owner_sub or ""
        if f.owner_anon_sub != owner_sub and f.owner_sub != owner_sub:
            raise HTTPException(status_code=403, detail="Forbidden")
        return
    if str(f.owner_user_id or "") != str(principal.user_id or ""):
        raise HTTPException(status_code=403, detail="Forbidden")


def _kind_mode(file_row: UploadFileModel) -> tuple[str, str]:
    meta = file_row.meta if isinstance(file_row.meta, dict) else {}
    rule = get_rule_for_filename(file_row.original_filename)
    kind = str(meta.get("kind") or (rule.kind if rule else "3d"))
    mode = str(meta.get("mode") or (rule.mode if rule else "brep"))
    return kind, mode


def _read_json_from_s3(bucket: str, key: str) -> dict[str, Any] | None:
    try:
        s3 = get_s3_client(settings)
        obj = s3.get_object(Bucket=bucket, Key=key)
        payload = json.loads(obj["Body"].read().decode("utf-8"))
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def _assembly_summary(file_row: UploadFileModel, meta: dict[str, Any]) -> dict[str, Any]:
    tree = meta.get("assembly_tree")
    if not isinstance(tree, list):
        assembly_key = meta.get("assembly_meta_key")
        if isinstance(assembly_key, str) and assembly_key:
            payload = _read_json_from_s3(file_row.bucket, assembly_key)
            if isinstance(payload, dict):
                occ = payload.get("occurrences")
                tree = occ if isinstance(occ, list) else []

    if not isinstance(tree, list):
        tree = []

    def count_nodes(nodes: list[Any]) -> int:
        total = 0
        for node in nodes:
            if not isinstance(node, dict):
                continue
            total += 1
            children = node.get("children")
            if isinstance(children, list):
                total += count_nodes(children)
        return total

    return {
        "node_count": count_nodes(tree),
        "root_count": len([x for x in tree if isinstance(x, dict)]),
        "tree": tree,
    }


def _build_engineering_analysis(file_row: UploadFileModel, include_web_context: bool = False, web_query: str | None = None) -> dict[str, Any]:
    meta = file_row.meta if isinstance(file_row.meta, dict) else {}
    kind, mode = _kind_mode(file_row)
    geometry = meta.get("geometry_meta_json") if isinstance(meta.get("geometry_meta_json"), dict) else {}
    geometry_report = meta.get("geometry_report") if isinstance(meta.get("geometry_report"), dict) else {}
    dfm_findings = meta.get("dfm_findings") if isinstance(meta.get("dfm_findings"), dict) else {}

    bbox = geometry.get("bbox") if isinstance(geometry.get("bbox"), dict) else {}
    holes = geometry.get("holes") if isinstance(geometry.get("holes"), list) else []
    threads = geometry.get("has_threads")
    part_count = meta.get("part_count") if isinstance(meta.get("part_count"), int) else geometry.get("part_count")

    geometry_section = {
        "units": geometry.get("units") or "unknown",
        "bbox": bbox,
        "diagonal": geometry.get("diagonal"),
        "part_count": int(part_count) if isinstance(part_count, int) else None,
        "hole_count": len([h for h in holes if isinstance(h, dict)]),
        "threads_detected": bool(threads) if isinstance(threads, bool) else None,
    }

    report_geometry = geometry_report.get("geometry") if isinstance(geometry_report.get("geometry"), dict) else {}
    findings = dfm_findings.get("findings") if isinstance(dfm_findings.get("findings"), list) else []
    manufacturing_section = {
        "status_gate": dfm_findings.get("status_gate") if isinstance(dfm_findings.get("status_gate"), str) else "UNKNOWN",
        "risk_flags": dfm_findings.get("risk_flags") if isinstance(dfm_findings.get("risk_flags"), list) else [],
        "wall_mm_min": report_geometry.get("wall_mm_min"),
        "wall_mm_max": report_geometry.get("wall_mm_max"),
        "draft_deg_min": report_geometry.get("draft_deg_min"),
        "has_undercut": report_geometry.get("has_undercut"),
        "findings": findings,
    }

    assembly = _assembly_summary(file_row, meta)
    recommendations: list[str] = []
    if kind == "3d" and not file_row.gltf_key:
        recommendations.append("Missing GLTF derivative: re-run conversion pipeline.")
    if kind == "archive" and not isinstance(meta.get("archive_manifest_key"), str):
        recommendations.append("Archive manifest missing: re-run archive processing.")
    if manufacturing_section["status_gate"] == "NEEDS_APPROVAL":
        recommendations.append("Manufacturing review required due to DFM blockers.")
    if not recommendations:
        recommendations.append("Model is analyzable and ready for downstream workflows.")

    web_context = []
    if include_web_context:
        q = (web_query or file_row.original_filename or "engineering reference").strip()
        web_context = search_technical_references(q, max_results=5)

    return {
        "file_id": _public_file_id(file_row.file_id),
        "filename": file_row.original_filename,
        "content_type": file_row.content_type,
        "status": file_row.status,
        "kind": kind,
        "mode": mode,
        "geometry": geometry_section,
        "assembly": assembly,
        "manufacturing": manufacturing_section,
        "features": {
            "holes": holes,
            "surface_breakdown": geometry.get("surfaces") if isinstance(geometry.get("surfaces"), dict) else {},
            "complexity": geometry.get("complexity") if isinstance(geometry.get("complexity"), dict) else {},
        },
        "recommendations": recommendations,
        "web_context": web_context,
        "generated_at": _now().isoformat(),
    }


def _load_plugins() -> list[dict[str, Any]]:
    if not _PLUGIN_REGISTRY_PATH.exists():
        return []
    try:
        payload = json.loads(_PLUGIN_REGISTRY_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []
    if not isinstance(payload, list):
        return []
    return [row for row in payload if isinstance(row, dict)]


def _save_plugins(items: list[dict[str, Any]]) -> None:
    _PLUGIN_REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    _PLUGIN_REGISTRY_PATH.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


def _agent_exists(agent_id: str) -> bool:
    return any(row.get("agent_id") == agent_id for row in AGENT_CATALOG)


def _run_agent(
    payload: AgentRunIn,
    principal: Principal,
    db: Session,
) -> dict[str, Any]:
    agent_id = payload.agent_id.strip()
    if not _agent_exists(agent_id):
        raise HTTPException(status_code=404, detail="Agent not found")

    file_row: UploadFileModel | None = None
    if payload.file_id:
        file_row = _get_file_by_identifier(db, payload.file_id)
        if not file_row:
            raise HTTPException(status_code=404, detail="File not found")
        _assert_file_access(file_row, principal)

    prompt = (payload.prompt or "").strip()
    web_query = (payload.web_query or prompt or (file_row.original_filename if file_row else "engineering standards")).strip()

    if agent_id in {"geometry_agent", "manufacturing_agent", "cad_repair_agent", "document_agent", "data_analysis_agent"} and file_row is None:
        raise HTTPException(status_code=400, detail="file_id is required for this agent")

    if agent_id == "geometry_agent":
        analysis = _build_engineering_analysis(file_row, include_web_context=payload.include_web_context, web_query=web_query)
        return {
            "agent_id": agent_id,
            "status": "ok",
            "summary": "Geometry analysis completed.",
            "findings": [
                f"part_count={analysis['geometry'].get('part_count')}",
                f"bbox={analysis['geometry'].get('bbox')}",
                f"assembly_nodes={analysis['assembly'].get('node_count')}",
            ],
            "data": analysis,
            "generated_at": _now().isoformat(),
        }

    if agent_id == "manufacturing_agent":
        analysis = _build_engineering_analysis(file_row, include_web_context=payload.include_web_context, web_query=web_query)
        mfg = analysis.get("manufacturing", {})
        findings = [str(item.get("message")) for item in mfg.get("findings", []) if isinstance(item, dict) and item.get("message")]
        return {
            "agent_id": agent_id,
            "status": "ok",
            "summary": f"Manufacturing gate={mfg.get('status_gate', 'UNKNOWN')}",
            "findings": findings or ["No blocking DFM finding reported."],
            "data": {"manufacturing": mfg, "recommendations": analysis.get("recommendations", [])},
            "generated_at": _now().isoformat(),
        }

    if agent_id == "cad_repair_agent":
        kind, _mode = _kind_mode(file_row)
        missing: list[str] = []
        meta = file_row.meta if isinstance(file_row.meta, dict) else {}
        if kind == "3d":
            if not file_row.gltf_key:
                missing.append("gltf_key")
            if not isinstance(meta.get("assembly_meta_key"), str):
                missing.append("assembly_meta_key")
            if not isinstance(meta.get("preview_jpg_keys"), list):
                missing.append("preview_jpg_keys")
        if kind == "archive" and not isinstance(meta.get("archive_manifest_key"), str):
            missing.append("archive_manifest_key")
        summary = "No repair action required." if not missing else "Repair actions suggested."
        findings = [f"Missing artifact: {name}" for name in missing] or ["Artifact contract is complete."]
        actions = ["enqueue_convert_file", "check_worker_health", "validate_source_format"] if missing else ["none"]
        return {
            "agent_id": agent_id,
            "status": "ok",
            "summary": summary,
            "findings": findings,
            "data": {"file_id": _public_file_id(file_row.file_id), "kind": kind, "suggested_actions": actions},
            "generated_at": _now().isoformat(),
        }

    if agent_id == "document_agent":
        analysis = _build_engineering_analysis(file_row, include_web_context=payload.include_web_context, web_query=web_query)
        meta = file_row.meta if isinstance(file_row.meta, dict) else {}
        findings = [
            f"kind={analysis.get('kind')}",
            f"status={analysis.get('status')}",
            f"pdf_preview={'yes' if isinstance(meta.get('pdf_key'), str) else 'no'}",
            f"archive_manifest={'yes' if isinstance(meta.get('archive_manifest_key'), str) else 'no'}",
        ]
        return {
            "agent_id": agent_id,
            "status": "ok",
            "summary": "Document/archive metadata prepared.",
            "findings": findings,
            "data": analysis,
            "generated_at": _now().isoformat(),
        }

    if agent_id == "web_research_agent":
        refs = search_technical_references(web_query or "engineering reference", max_results=payload.include_web_context and 7 or 5)
        return {
            "agent_id": agent_id,
            "status": "ok",
            "summary": f"Collected {len(refs)} external references.",
            "findings": [row.get("title", "reference") for row in refs],
            "data": {"query": web_query, "results": refs},
            "generated_at": _now().isoformat(),
        }

    if agent_id == "data_analysis_agent":
        meta = file_row.meta if isinstance(file_row.meta, dict) else {}
        geometry = meta.get("geometry_meta_json") if isinstance(meta.get("geometry_meta_json"), dict) else {}
        sample_stats = {
            "size_bytes": int(file_row.size_bytes),
            "status": file_row.status,
            "kind": _kind_mode(file_row)[0],
            "part_count": meta.get("part_count") if isinstance(meta.get("part_count"), int) else geometry.get("part_count"),
            "bbox": geometry.get("bbox") if isinstance(geometry.get("bbox"), dict) else {},
        }
        return {
            "agent_id": agent_id,
            "status": "ok",
            "summary": "Deterministic data profile generated.",
            "findings": [f"size_bytes={sample_stats['size_bytes']}", f"status={sample_stats['status']}"],
            "data": sample_stats,
            "generated_at": _now().isoformat(),
        }

    raise HTTPException(status_code=500, detail="Agent runtime error")


@router.get("/capabilities")
def capabilities(principal: Principal = Depends(get_current_principal)):
    _ = principal
    return {
        "platform": "STELL-AI",
        "target_intelligence_level": "7-8",
        "modules": [
            "AI Engineering Assistant",
            "Universal CAD/Document Viewer",
            "Engineering Analysis Engine",
            "Agent System",
            "Document Processing",
            "Web Knowledge Integration",
            "Plugin System",
        ],
        "agent_count": len(AGENT_CATALOG),
        "generated_at": _now().isoformat(),
    }


@router.get("/agents")
def list_agents(principal: Principal = Depends(get_current_principal)):
    _ = principal
    return {"items": AGENT_CATALOG, "total": len(AGENT_CATALOG)}


@router.post("/knowledge/search")
def knowledge_search(data: KnowledgeSearchIn, principal: Principal = Depends(get_current_principal)):
    _ = principal
    results = search_technical_references(data.query, max_results=data.max_results)
    return {"query": data.query, "results": results, "total": len(results)}


@router.get("/analysis/{file_id}")
def file_analysis(
    file_id: str,
    include_web_context: bool = False,
    web_query: str | None = None,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    row = _get_file_by_identifier(db, file_id)
    if not row:
        raise HTTPException(status_code=404, detail="File not found")
    _assert_file_access(row, principal)
    return _build_engineering_analysis(row, include_web_context=include_web_context, web_query=web_query)


@router.post("/agents/run")
def run_agent(
    data: AgentRunIn,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    return _run_agent(data, principal=principal, db=db)


@router.post("/agents/orchestrate")
def orchestrate_agents(
    data: AgentOrchestrateIn,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    runs = []
    for task in data.tasks:
        run = _run_agent(
            AgentRunIn(
                agent_id=task.agent_id,
                file_id=task.file_id,
                prompt=task.prompt,
                include_web_context=data.include_web_context,
                web_query=data.web_query,
            ),
            principal=principal,
            db=db,
        )
        runs.append(run)

    summaries = [row.get("summary", "") for row in runs if isinstance(row.get("summary"), str)]
    return {
        "status": "ok",
        "runs": runs,
        "summary": " | ".join([s for s in summaries if s]) or "Orchestration completed.",
        "generated_at": _now().isoformat(),
    }


@router.get("/plugins")
def list_plugins(principal: Principal = Depends(get_current_principal)):
    _ = principal
    builtins = [
        {
            "plugin_id": "core.geometry",
            "name": "Core Geometry Analyzer",
            "plugin_type": "analysis",
            "description": "Built-in geometry extraction and reporting.",
            "entrypoint": "app.core.hybrid_v1_geometry.build_geometry_report_for_step",
            "built_in": True,
        },
        {
            "plugin_id": "core.dfm",
            "name": "Core DFM Rules",
            "plugin_type": "analysis",
            "description": "Built-in manufacturing gate rules.",
            "entrypoint": "app.core.hybrid_v1_rules.evaluate_hybrid_v1_rules",
            "built_in": True,
        },
    ]
    custom = _load_plugins()
    return {"items": builtins + custom, "total": len(builtins) + len(custom)}


@router.post("/plugins/register", status_code=201)
def register_plugin(data: PluginRegisterIn, principal: Principal = Depends(get_current_principal)):
    if principal.typ != "user":
        raise HTTPException(status_code=403, detail="Only authenticated users can register plugins")

    items = _load_plugins()
    if any(str(item.get("plugin_id")) == data.plugin_id for item in items):
        raise HTTPException(status_code=409, detail="plugin_id already exists")

    row = {
        "plugin_id": data.plugin_id,
        "name": data.name,
        "plugin_type": data.plugin_type,
        "description": data.description,
        "entrypoint": data.entrypoint,
        "built_in": False,
        "created_at": _now().isoformat(),
    }
    items.append(row)
    _save_plugins(items)
    return row
