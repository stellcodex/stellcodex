#!/usr/bin/env python3
from __future__ import annotations

import csv
import datetime as dt
import json
import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple


WORKDIR = Path("/root/workspace/audit")
OUTPUT_DIR = WORKDIR / "output"
CENTRAL_DIR = WORKDIR / "STELL_SYSTEM_CORE"

FOCUSED_INVENTORY_CSV = OUTPUT_DIR / "focused_inventory.csv"

MASTER_INVENTORY_CSV = OUTPUT_DIR / "MASTER_PROMPT_INVENTORY.csv"
MASTER_INVENTORY_JSON = OUTPUT_DIR / "MASTER_PROMPT_INVENTORY.json"
DUPLICATES_JSON = OUTPUT_DIR / "PROMPT_DUPLICATES.json"
CONFLICTS_JSON = OUTPUT_DIR / "PROMPT_CONFLICTS.json"

COPY_LOG_CSV = CENTRAL_DIR / "10_reports" / "COPY_ACTION_LOG.csv"
CONFLICT_REPORT_MD = CENTRAL_DIR / "10_reports" / "PROMPT_CONFLICT_REPORT.md"
FINAL_REPORT_MD = CENTRAL_DIR / "10_reports" / "FINAL_STELL_AUDIT_REPORT.md"
MANIFEST_JSON = CENTRAL_DIR / "ACTIVE_PROMPT_MANIFEST.json"
CENTRAL_MASTER_INVENTORY_CSV = CENTRAL_DIR / "10_reports" / "MASTER_PROMPT_INVENTORY.csv"
CENTRAL_MASTER_INVENTORY_JSON = CENTRAL_DIR / "10_reports" / "MASTER_PROMPT_INVENTORY.json"
CENTRAL_DUPLICATES_JSON = CENTRAL_DIR / "10_reports" / "PROMPT_DUPLICATES.json"
CENTRAL_CONFLICTS_JSON = CENTRAL_DIR / "10_reports" / "PROMPT_CONFLICTS.json"


CENTRAL_SUBDIRS = [
    "01_identity",
    "02_constitution",
    "03_global_policies",
    "04_roles",
    "05_workers",
    "06_tasks",
    "07_output_contracts",
    "08_tool_policies",
    "09_legacy_archive",
    "10_reports",
]


SOURCE_PREFIXES = (
    "/root/workspace/",
    "/root/stell/",
    "/var/www/stellcodex/",
    "/root/stellcodex_output/",
)

NOISE_PATTERNS = [
    "/node_modules/",
    "/.git/",
    "/.next/",
    "/.venv/",
    "/site-packages/",
    "/__pycache__/",
    "/audit/output/",
    "/audit/scripts/",
    "/_archive/noncanonical_retired_",
]

LEGACY_PATTERNS = [
    "/_backups/",
    "/_archive/",
    "/_runs/",
    "/evidence/",
    "/genois/05_whatsapp_ingest/",
    "/_jobs/backups/",
]

EXPLICIT_LEGACY_PATHS = {
    "/root/workspace/_knowledge/manuals/STELLCODEX_MASTER_PROMPT_v8.0.md",
    "/var/www/stellcodex/docs/v6/V6_00_CONSTITUTION.md",
    "/var/www/stellcodex/docs/v6/V6_08_CODEX_MEGA_PROMPT_V6.md",
    "/root/stell/webhook_main.py",
}

AUTHORITATIVE_SOURCES = {
    "identity": [
        "/root/workspace/_truth/STELLCODEX_MASTER_PROMPT_v8.0.md",
        "/root/stell/prompts/system/stell-core.md",
    ],
    "constitution": [
        "/root/workspace/_truth/15_AGENT_GOVERNANCE_AND_IDENTITY.md",
        "/var/www/stellcodex/docs/constitution/STELLCODEX_V7_MASTER.md",
        "/var/www/stellcodex/docs/constitution/V7_ENFORCEMENT_PROTOCOL.md",
    ],
    "global_policies": [
        "/root/workspace/_truth/09_SECURITY_AND_ACCESS.md",
        "/root/stell/policies/security/access.md",
        "/root/stell/policies/approval/required-approvals.md",
        "/root/stell/policies/channels/whatsapp.md",
    ],
    "roles": [
        "/root/workspace/ops/orchestra/orchestrator/router.py",
        "/root/workspace/ops/orchestra/state/model_profiles.json",
        "/root/stell/playbooks/delegation/ai-routing.md",
    ],
    "workers": [
        "/root/workspace/ops/orchestra/orchestrator/app.py",
        "/root/workspace/ops/orchestra/orchestrator/profiler.py",
        "/root/workspace/ops/orchestra/litellm.config.yaml",
        "/root/stell/webhook/main.py",
        "/root/stell/webhook/identity_guard.py",
        "/root/stell/cloudflare/worker.js",
    ],
    "tasks": [
        "/root/workspace/ops/orchestra/orchestra.sh",
        "/root/workspace/ops/orchestra/autopilot.sh",
    ],
    "output_contracts": [
        "/root/workspace/_truth/05_API_CONTRACTS.md",
        "/var/www/stellcodex/docs/data_model/SCHEMA_POLICY.md",
        "/var/www/stellcodex/docs/constitution/HIERARCHY.md",
    ],
    "tool_policies": [
        "/root/stell/knowledge-map.json",
        "/root/stell/STELL_KNOWLEDGE_SYNC.md",
        "/root/workspace/_truth/07_BACKUP_AND_DRIVE_SYNC.md",
        "/root/workspace/_truth/03_STELL_AI_OPERATING_MODEL.md",
    ],
}


def utc_now() -> str:
    return dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def is_noise(path: str) -> bool:
    p = path.lower()
    return any(tok in p for tok in NOISE_PATTERNS)


def is_in_scope(path: str) -> bool:
    return path.startswith(SOURCE_PREFIXES)


def is_legacy(path: str) -> bool:
    p = path.lower()
    return path in EXPLICIT_LEGACY_PATHS or any(tok in p for tok in LEGACY_PATTERNS)


def classify(path: str) -> str:
    p = path.lower()
    name = os.path.basename(p)

    if "stellcodex_master_prompt" in p or name == "stell-core.md":
        return "Identity/Core"
    if (
        "constitution" in p
        or "v7_enforcement_protocol" in p
        or "v7_master" in p
        or "v6_00_constitution" in p
        or "15_agent_governance_and_identity" in p
    ):
        return "Constitution"
    if (
        "/policies/" in p
        or "09_security_and_access" in p
        or "required-approvals" in p
        or "whatsapp.md" in p
        or "rbac.policy.json" in p
    ):
        return "Global policies"
    if "/playbooks/" in p:
        return "Playbooks"
    if (
        "role-permission-template" in p
        or "orchestrator/router.py" in p
        or "model_profiles.json" in p
        or "ai-routing.md" in p
    ):
        return "Role definitions"
    if (
        "orchestrator/app.py" in p
        or "orchestrator/profiler.py" in p
        or "litellm.config.yaml" in p
        or "/backend/app/workers/" in p
        or name in {"worker.py", "worker_main.py", "stell_worker.py"}
        or "webhook/main.py" in p
        or "webhook_main.py" in p
        or "identity_guard.py" in p
        or "cloudflare/worker.js" in p
    ):
        return "Worker prompts"
    if "/_jobs/inbox/" in p or "/_jobs/done/" in p or "/_jobs/failed/" in p or name in {
        "orchestra.sh",
        "autopilot.sh",
    }:
        return "Task prompts"
    if (
        "api_contract" in p
        or "schema_policy" in p
        or "contract" in p
        or "hierarchy.md" in p
    ):
        return "Output contracts"
    if (
        "knowledge-map.json" in p
        or "stell_knowledge_sync" in p
        or "backup_and_drive_sync" in p
        or "disaster_recovery_runbook" in p
        or "operating_model" in p
    ):
        return "Tool policies"
    return "Unknown/Unclassified"


def category_to_dir(category: str, status: str) -> str:
    if status.startswith("legacy"):
        return "09_legacy_archive"
    mapping = {
        "Identity/Core": "01_identity",
        "Constitution": "02_constitution",
        "Global policies": "03_global_policies",
        "Role definitions": "04_roles",
        "Worker prompts": "05_workers",
        "Task prompts": "06_tasks",
        "Playbooks": "06_tasks",
        "Output contracts": "07_output_contracts",
        "Tool policies": "08_tool_policies",
        "Unknown/Unclassified": "09_legacy_archive",
    }
    return mapping.get(category, "09_legacy_archive")


def repo_ref(path: str) -> Tuple[str, str]:
    if path.startswith("/root/stell/"):
        return ("stellcodex/stell-assistant", "master")
    if path.startswith("/var/www/stellcodex/"):
        return ("stellcodex/stellcodex", "main")
    if path.startswith("/root/workspace/"):
        return ("stellcodex/stellcodex", "master")
    return ("", "")


SECRET_KEY_PATTERN = re.compile(
    r"([A-Z0-9_]*(?:TOKEN|KEY|SECRET|PASSWORD|API[_]?KEY|ACCESS[_]?KEY)[A-Z0-9_]*)\s*=\s*[^,\s]+",
    re.IGNORECASE,
)


def sanitize_snippet(path: str, snippet: str) -> str:
    p = path.lower()
    if "/.env" in p or p.endswith(".env") or "/secrets" in p:
        return "[REDACTED_SENSITIVE_SNIPPET]"
    if not snippet:
        return ""
    redacted = SECRET_KEY_PATTERN.sub(r"\1=[REDACTED]", snippet)
    return redacted


@dataclass
class Row:
    source: str
    path: str
    filename: str
    ext: str
    mime: str
    size_bytes: int
    sha256: str
    mtime_utc: str
    snippet: str
    classification: str
    status: str
    repo: str
    branch: str
    include_for_centralization: bool
    notes: str


def read_inventory() -> List[Row]:
    rows: List[Row] = []
    with FOCUSED_INVENTORY_CSV.open("r", encoding="utf-8", errors="replace", newline="") as f:
        reader = csv.DictReader(f)
        for raw in reader:
            path = raw.get("path", "")
            if not path or not is_in_scope(path):
                continue
            if is_noise(path):
                continue

            cls = classify(path)
            legacy = is_legacy(path)
            status = "legacy/deprecated" if legacy else "active"

            # v6 docs are explicitly deprecated by v7 hierarchy docs.
            if path.startswith("/var/www/stellcodex/docs/v6/"):
                status = "legacy/deprecated"

            notes = ""
            if path in EXPLICIT_LEGACY_PATHS:
                notes = "explicit_legacy_override"
            if "/_knowledge/manuals/" in path:
                notes = (notes + "; " if notes else "") + "manuals_copy_non_authoritative"

            include = cls != "Unknown/Unclassified" or path in EXPLICIT_LEGACY_PATHS

            repo, branch = repo_ref(path)
            try:
                size = int(raw.get("size_bytes", "0") or "0")
            except ValueError:
                size = 0

            row = Row(
                source=raw.get("source", ""),
                path=path,
                filename=raw.get("filename", ""),
                ext=raw.get("ext", ""),
                mime=raw.get("mime", ""),
                size_bytes=size,
                sha256=(raw.get("sha256", "") or "").strip(),
                mtime_utc=raw.get("mtime_utc", ""),
                snippet=sanitize_snippet(path, raw.get("snippet", "")),
                classification=cls,
                status=status,
                repo=repo,
                branch=branch,
                include_for_centralization=include,
                notes=notes,
            )
            rows.append(row)

    # Force-include authoritative files that may be absent from keyword-driven discovery.
    existing = {r.path for r in rows}
    forced_sources = sorted({p for v in AUTHORITATIVE_SOURCES.values() for p in v if p.startswith("/")})
    for src in forced_sources:
        if src in existing:
            continue
        fp = Path(src)
        if not fp.exists() or not fp.is_file():
            continue
        try:
            stat = fp.stat()
            size = int(stat.st_size)
            mtime = dt.datetime.utcfromtimestamp(stat.st_mtime).replace(microsecond=0).isoformat() + "Z"
        except Exception:
            size = 0
            mtime = ""
        try:
            import hashlib

            sha = hashlib.sha256(fp.read_bytes()).hexdigest()
        except Exception:
            sha = ""
        try:
            snippet_raw = " ".join(
                [ln.strip() for ln in fp.read_text(encoding="utf-8", errors="ignore").splitlines()[:5]]
            )
        except Exception:
            snippet_raw = ""
        repo, branch = repo_ref(src)
        rows.append(
            Row(
                source="forced_authoritative",
                path=src,
                filename=fp.name,
                ext=fp.suffix.lstrip("."),
                mime="",
                size_bytes=size,
                sha256=sha,
                mtime_utc=mtime,
                snippet=sanitize_snippet(src, snippet_raw[:240]),
                classification=classify(src),
                status="legacy/deprecated" if is_legacy(src) else "active",
                repo=repo,
                branch=branch,
                include_for_centralization=True,
                notes="forced_authoritative_include",
            )
        )
    return rows


def write_master_inventory(rows: List[Row]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    fields = [
        "source",
        "path",
        "filename",
        "ext",
        "mime",
        "size_bytes",
        "sha256",
        "mtime_utc",
        "classification",
        "status",
        "repo",
        "branch",
        "include_for_centralization",
        "notes",
        "snippet",
    ]
    with MASTER_INVENTORY_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow(
                {
                    "source": r.source,
                    "path": r.path,
                    "filename": r.filename,
                    "ext": r.ext,
                    "mime": r.mime,
                    "size_bytes": r.size_bytes,
                    "sha256": r.sha256,
                    "mtime_utc": r.mtime_utc,
                    "classification": r.classification,
                    "status": r.status,
                    "repo": r.repo,
                    "branch": r.branch,
                    "include_for_centralization": str(r.include_for_centralization).lower(),
                    "notes": r.notes,
                    "snippet": r.snippet,
                }
            )

    with MASTER_INVENTORY_JSON.open("w", encoding="utf-8") as f:
        json.dump([r.__dict__ for r in rows], f, ensure_ascii=False, indent=2)


def build_duplicates(rows: List[Row]) -> List[Dict[str, object]]:
    by_sha: Dict[str, List[Row]] = {}
    for r in rows:
        if not r.sha256:
            continue
        by_sha.setdefault(r.sha256, []).append(r)

    groups: List[Dict[str, object]] = []
    for sha, members in by_sha.items():
        if len(members) < 2:
            continue
        groups.append(
            {
                "sha256": sha,
                "count": len(members),
                "paths": [m.path for m in members],
                "active_count": sum(1 for m in members if m.status == "active"),
                "legacy_count": sum(1 for m in members if m.status != "active"),
            }
        )
    groups.sort(key=lambda x: int(x["count"]), reverse=True)
    with DUPLICATES_JSON.open("w", encoding="utf-8") as f:
        json.dump(groups, f, ensure_ascii=False, indent=2)
    return groups


def build_conflicts(rows: List[Row]) -> List[Dict[str, object]]:
    key_map: Dict[Tuple[str, str], List[Row]] = {}
    for r in rows:
        if r.classification == "Unknown/Unclassified":
            continue
        key = (r.filename.lower(), r.classification)
        key_map.setdefault(key, []).append(r)

    conflicts: List[Dict[str, object]] = []
    for (filename, classification), members in key_map.items():
        shas = {m.sha256 for m in members if m.sha256}
        if len(shas) > 1:
            conflicts.append(
                {
                    "filename": filename,
                    "classification": classification,
                    "unique_hashes": sorted(shas),
                    "paths": [m.path for m in members],
                    "active_paths": [m.path for m in members if m.status == "active"],
                    "legacy_paths": [m.path for m in members if m.status != "active"],
                }
            )

    # Add explicit semantic conflicts.
    semantic_conflicts = [
        {
            "filename": "STELLCODEX_MASTER_PROMPT_v8.0.md",
            "classification": "Identity/Core",
            "reason": "truth vs manuals copies diverge",
            "paths": [
                "/root/workspace/_truth/STELLCODEX_MASTER_PROMPT_v8.0.md",
                "/root/workspace/_knowledge/manuals/STELLCODEX_MASTER_PROMPT_v8.0.md",
            ],
        },
        {
            "filename": "constitution_family",
            "classification": "Constitution",
            "reason": "v7 constitution supersedes v6 constitution",
            "paths": [
                "/var/www/stellcodex/docs/constitution/STELLCODEX_V7_MASTER.md",
                "/var/www/stellcodex/docs/v6/V6_00_CONSTITUTION.md",
                "/var/www/stellcodex/docs/v6/V6_08_CODEX_MEGA_PROMPT_V6.md",
            ],
        },
        {
            "filename": "webhook_main_duplication",
            "classification": "Worker prompts",
            "reason": "duplicate runtime entrypoint files with identical content",
            "paths": [
                "/root/stell/webhook/main.py",
                "/root/stell/webhook_main.py",
            ],
        },
    ]
    conflicts.extend(semantic_conflicts)

    with CONFLICTS_JSON.open("w", encoding="utf-8") as f:
        json.dump(conflicts, f, ensure_ascii=False, indent=2)
    return conflicts


def ensure_structure() -> None:
    for sub in CENTRAL_SUBDIRS:
        (CENTRAL_DIR / sub).mkdir(parents=True, exist_ok=True)


def copy_files(rows: List[Row]) -> List[Dict[str, str]]:
    ensure_structure()
    log_rows: List[Dict[str, str]] = []

    for r in rows:
        if not r.include_for_centralization:
            continue
        src = Path(r.path)
        if not src.exists() or not src.is_file():
            continue
        subdir = category_to_dir(r.classification, r.status)
        rel = r.path.lstrip("/")
        dst = CENTRAL_DIR / subdir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(src, dst)
            outcome = "copied"
            error = ""
        except Exception as exc:  # pragma: no cover - best effort copy
            outcome = "error"
            error = str(exc)
        log_rows.append(
            {
                "source_path": r.path,
                "destination_path": str(dst),
                "classification": r.classification,
                "status": r.status,
                "sha256": r.sha256,
                "action": outcome,
                "reason": "active" if r.status == "active" else "legacy_or_conflict",
                "error": error,
            }
        )

    with COPY_LOG_CSV.open("w", encoding="utf-8", newline="") as f:
        fields = [
            "source_path",
            "destination_path",
            "classification",
            "status",
            "sha256",
            "action",
            "reason",
            "error",
        ]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in log_rows:
            w.writerow(row)
    return log_rows


def manifest_path_for_source(src_path: str, classification: str, status: str) -> str:
    subdir = category_to_dir(classification, status)
    return str(CENTRAL_DIR / subdir / src_path.lstrip("/"))


def build_manifest(rows: List[Row], duplicates: List[Dict[str, object]], conflicts: List[Dict[str, object]]) -> None:
    row_by_path = {r.path: r for r in rows}

    authoritative: Dict[str, List[Dict[str, str]]] = {}
    for category, sources in AUTHORITATIVE_SOURCES.items():
        items: List[Dict[str, str]] = []
        for src in sources:
            r = row_by_path.get(src)
            if not r:
                items.append(
                    {
                        "source_path": src,
                        "destination_path": "",
                        "sha256": "",
                        "status": "missing_from_inventory",
                    }
                )
                continue
            items.append(
                {
                    "source_path": src,
                    "destination_path": manifest_path_for_source(src, r.classification, r.status),
                    "sha256": r.sha256,
                    "status": r.status,
                }
            )
        authoritative[category] = items

    manifest = {
        "generated_at_utc": utc_now(),
        "central_root_local": str(CENTRAL_DIR),
        "central_root_drive": "gdrive:STELL_SYSTEM_CORE",
        "inventory_files": {
            "master_inventory_csv": str(CENTRAL_MASTER_INVENTORY_CSV),
            "master_inventory_json": str(CENTRAL_MASTER_INVENTORY_JSON),
            "duplicates_json": str(CENTRAL_DUPLICATES_JSON),
            "conflicts_json": str(CENTRAL_CONFLICTS_JSON),
            "copy_log_csv": str(COPY_LOG_CSV),
        },
        "authoritative": authoritative,
        "stats": {
            "duplicate_groups": len(duplicates),
            "conflict_groups": len(conflicts),
        },
    }

    with MANIFEST_JSON.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)


def build_conflict_report(
    rows: List[Row],
    duplicates: List[Dict[str, object]],
    conflicts: List[Dict[str, object]],
) -> None:
    total = len(rows)
    active = sum(1 for r in rows if r.status == "active")
    legacy = total - active
    cls_counts: Dict[str, int] = {}
    for r in rows:
        cls_counts[r.classification] = cls_counts.get(r.classification, 0) + 1

    lines: List[str] = []
    lines.append("# PROMPT_CONFLICT_REPORT")
    lines.append("")
    lines.append(f"- Generated: {utc_now()}")
    lines.append(f"- Inventory rows (filtered): {total}")
    lines.append(f"- Active rows: {active}")
    lines.append(f"- Legacy rows: {legacy}")
    lines.append(f"- Duplicate hash groups: {len(duplicates)}")
    lines.append(f"- Conflict groups: {len(conflicts)}")
    lines.append("")
    lines.append("## Classification Counts")
    lines.append("")
    for k in sorted(cls_counts):
        lines.append(f"- {k}: {cls_counts[k]}")
    lines.append("")
    lines.append("## High-Impact Conflicts")
    lines.append("")
    lines.append("1. `_truth/STELLCODEX_MASTER_PROMPT_v8.0.md` vs `_knowledge/manuals/STELLCODEX_MASTER_PROMPT_v8.0.md` differ.")
    lines.append("2. V7 constitution is binding, but V6 constitution/mega prompt still exists under deployed docs.")
    lines.append("3. `webhook/main.py` and `webhook_main.py` are duplicate runtime entrypoints with identical hashes.")
    lines.append("4. Orchestrator instructions are embedded in code (`orchestrator/app.py`) in addition to markdown prompt files.")
    lines.append("")
    lines.append("## Duplicate Hash Samples")
    lines.append("")
    for group in duplicates[:20]:
        lines.append(f"- sha256 `{group['sha256']}` count={group['count']}")
        for p in group["paths"][:5]:
            lines.append(f"  - {p}")
    lines.append("")
    lines.append("## Recommended Actions")
    lines.append("")
    lines.append("- Keep `_truth` files authoritative for STELLCODEX core governance and master prompt.")
    lines.append("- Keep `/root/stell/prompts/system/stell-core.md` as channel-specific identity for webhook/assistant stack.")
    lines.append("- Archive V6 constitutional docs and manuals copies under legacy with explicit superseded notes.")
    lines.append("- Remove runtime ambiguity by deprecating `/root/stell/webhook_main.py` and keeping `/root/stell/webhook/main.py`.")
    lines.append("- Externalize embedded orchestrator prompt strings to versioned files under centralized prompt core in a follow-up.")
    lines.append("")

    CONFLICT_REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def build_final_report(
    rows: List[Row],
    duplicates: List[Dict[str, object]],
    conflicts: List[Dict[str, object]],
    copy_log: List[Dict[str, str]],
) -> None:
    total = len(rows)
    active = sum(1 for r in rows if r.status == "active")
    legacy = total - active
    copied = sum(1 for r in copy_log if r["action"] == "copied")
    copy_errors = sum(1 for r in copy_log if r["action"] != "copied")

    # Aggregate per source root.
    by_root: Dict[str, int] = {"/root/workspace": 0, "/root/stell": 0, "/var/www/stellcodex": 0}
    for r in rows:
        for root in by_root:
            if r.path.startswith(root + "/"):
                by_root[root] += 1

    lines: List[str] = []
    lines.append("# FINAL_STELL_AUDIT_REPORT")
    lines.append("")
    lines.append(f"Generated (UTC): {utc_now()}")
    lines.append("")
    lines.append("## 1. Summary")
    lines.append("")
    lines.append(f"- Discovery inventory rows (filtered, in-scope): {total}")
    lines.append(f"- Active rows: {active}")
    lines.append(f"- Legacy/deprecated rows: {legacy}")
    lines.append(f"- Duplicate hash groups: {len(duplicates)}")
    lines.append(f"- Conflict groups: {len(conflicts)}")
    lines.append(f"- Files copied into central core tree: {copied}")
    lines.append(f"- Copy errors: {copy_errors}")
    lines.append("")
    lines.append("Scope roots covered:")
    for root, count in by_root.items():
        lines.append(f"- {root}: {count} rows")
    lines.append("")
    lines.append("## 2. Inventory")
    lines.append("")
    lines.append("Full machine-readable inventory is stored at:")
    lines.append(f"- `{CENTRAL_MASTER_INVENTORY_CSV}`")
    lines.append(f"- `{CENTRAL_MASTER_INVENTORY_JSON}`")
    lines.append("")
    lines.append("## 3. Duplicates & Conflicts")
    lines.append("")
    lines.append("Detailed conflict report:")
    lines.append(f"- `{CONFLICT_REPORT_MD}`")
    lines.append("")
    lines.append("Key decisions:")
    lines.append("- `_truth/STELLCODEX_MASTER_PROMPT_v8.0.md` selected as authoritative over manuals copy.")
    lines.append("- V7 constitution selected as authoritative over V6 docs.")
    lines.append("- `webhook/main.py` selected as authoritative runtime entrypoint over duplicate `webhook_main.py`.")
    lines.append("- Embedded orchestrator prompts kept active (no runtime refactor done in this audit).")
    lines.append("")
    lines.append("## 4. New Central Structure")
    lines.append("")
    lines.append("`/STELL_SYSTEM_CORE` folders created:")
    for sub in CENTRAL_SUBDIRS:
        lines.append(f"- {sub}")
    lines.append("")
    lines.append("## 5. Changes & Fixes")
    lines.append("")
    lines.append("- Built full focused discovery inventory with sha256/snippets.")
    lines.append("- Classified files into identity/constitution/policy/role/worker/task/tool/legacy categories.")
    lines.append("- Copied active and legacy files into centralized folder tree (local staging + Drive sync target).")
    lines.append("- Generated `ACTIVE_PROMPT_MANIFEST.json`, duplicate/conflict JSON artifacts, and copy-action log.")
    lines.append("")
    lines.append("## 6. External Services Audit Notes")
    lines.append("")
    lines.append("- Google Drive: accessible via `rclone` (`gdrive:` remote), existing root `stellcodex-genois` discovered.")
    lines.append("- Cloudflare Workers: local worker source and deployment docs found; live Cloudflare API record enumeration not executed from this run.")
    lines.append("- Vercel: active `frontend/vercel.json` discovered and analyzed; no local Vercel CLI auth metadata found.")
    lines.append("- DNS: A/AAAA/NS records enumerated for discovered domains (`stellcodex.com`, `api.stellcodex.com`, `stell.stellcodex.com`, workers.dev host).")
    lines.append("")
    lines.append("## 7. High-Risk Findings")
    lines.append("")
    lines.append("- Plain-text secret-bearing `.env` files are present in active paths and historical backups (values intentionally omitted).")
    lines.append("- Multiple instruction authorities coexist (`_truth`, `docs/constitution`, `/root/stell/prompts`, and embedded code prompts).")
    lines.append("- Legacy prompt/policy copies in backups and manuals can cause operator confusion if not clearly marked.")
    lines.append("")
    lines.append("## 8. Outstanding Items")
    lines.append("")
    lines.append("- Cloudflare DNS/Worker inventory via provider API remains pending if API token-backed live audit is required.")
    lines.append("- Vercel project/env API inventory remains pending if token-backed live audit is required.")
    lines.append("- Runtime refactor to remove embedded prompts from `orchestrator/app.py` was not applied in this audit.")
    lines.append("")
    lines.append("## 9. Recommendations")
    lines.append("")
    lines.append("1. Enforce `_truth/` as STELLCODEX governance SSOT and mark manuals as read-only mirrors.")
    lines.append("2. Move orchestrator embedded prompt strings into versioned files under centralized core.")
    lines.append("3. Add CI checks that fail on new duplicate `*prompt*` or `*constitution*` files outside central core.")
    lines.append("4. Schedule recurring monthly audit to refresh duplicate/conflict manifests and external endpoint mapping.")
    lines.append("5. Rotate exposed secrets and remove plain-text secret files from tracked/deployed directories.")
    lines.append("")

    FINAL_REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    if not FOCUSED_INVENTORY_CSV.exists():
        raise SystemExit(f"Missing inventory file: {FOCUSED_INVENTORY_CSV}")

    rows = read_inventory()
    write_master_inventory(rows)

    duplicates = build_duplicates(rows)
    conflicts = build_conflicts(rows)

    if CENTRAL_DIR.exists():
        shutil.rmtree(CENTRAL_DIR)
    ensure_structure()
    copy_log = copy_files(rows)

    # Persist core data artifacts inside centralized reports folder as well.
    shutil.copy2(MASTER_INVENTORY_CSV, CENTRAL_MASTER_INVENTORY_CSV)
    shutil.copy2(MASTER_INVENTORY_JSON, CENTRAL_MASTER_INVENTORY_JSON)
    shutil.copy2(DUPLICATES_JSON, CENTRAL_DUPLICATES_JSON)
    shutil.copy2(CONFLICTS_JSON, CENTRAL_CONFLICTS_JSON)

    build_conflict_report(rows, duplicates, conflicts)
    build_manifest(rows, duplicates, conflicts)
    build_final_report(rows, duplicates, conflicts, copy_log)

    summary = {
        "generated_at_utc": utc_now(),
        "rows_total": len(rows),
        "rows_active": sum(1 for r in rows if r.status == "active"),
        "rows_legacy": sum(1 for r in rows if r.status != "active"),
        "duplicates": len(duplicates),
        "conflicts": len(conflicts),
        "files_copied": sum(1 for r in copy_log if r["action"] == "copied"),
        "copy_errors": sum(1 for r in copy_log if r["action"] != "copied"),
        "manifest": str(MANIFEST_JSON),
        "final_report": str(FINAL_REPORT_MD),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
