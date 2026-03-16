#!/usr/bin/env python3
from __future__ import annotations

import base64
import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import tarfile
import zipfile
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple
from urllib.parse import quote


LOCAL_ROOT = Path("/root/workspace/_contracts_consolidation")
CONTRACTS_LOCAL_ROOT = LOCAL_ROOT / "STELLCODEX" / "Contracts"
REMOTE_ROOT = "gdrive:STELLCODEX/Contracts"
REMOTE_VERIFY_ROOT = "gdrive:STELLCODEX"

SERVER_ROOTS = [
    Path("/root/workspace"),
    Path("/var/www/stellcodex"),
    Path("/root/backup_before_v7_20260227_050900"),
    Path("/root/stell"),
    Path("/root/stellcodex_ops"),
]

SERVER_LOOSE_FILES = [
    Path("/root/generate_stellcodex_master.sh"),
    Path("/root/stellcodex_orchestrator_task.md"),
    Path("/root/stellcodex_restore_test.sh"),
    Path("/root/stellcodex_state_freeze.sh"),
    Path("/root/STELLCODEX_V7_ULTRA_PRODUCTION_READY_FULL_PACKAGE.zip"),
]

SERVER_ARCHIVES = [
    Path("/root/STELLCODEX_V7_ULTRA_PRODUCTION_READY_FULL_PACKAGE.zip"),
    Path("/root/backups/stellcodex_code_20260308T1457Z.tar.gz"),
    Path("/root/backups/stellcodex_full_backup_20260308T1458Z.tar.gz"),
]

DRIVE_REMOTES = [
    "gdrive:stellcodex",
    "gdrive:stellcodex-genois",
    "gdrive:STELL",
]

KEYWORDS = [
    "protocol",
    "contract",
    "context",
    "rule",
    "policy",
    "prompt",
    "execution",
    "master",
    "final",
    "locked",
    "hard-locked",
    "governance",
    "recovery",
    "restore",
    "release gate",
    "deployment",
    "architecture",
    "system rules",
    "source of truth",
    "stateless",
    "storage",
    "google drive",
    "github",
    "vercel",
    "cloudflare",
    "orchestra",
    "orchestrator",
    "tenant isolation",
    "artifact",
    "evidence",
    "compliance",
    "binding",
    "instruction",
    "playbook",
    "runbook",
    "standard",
    "folder structure",
    "naming",
    "canonical",
    "authoritative",
    "migration",
    "handoff",
    "constraints",
    "forbidden",
    "must not",
    "active version",
    "deprecated",
    "obsolete",
    "archive",
    "v7",
    "v8",
    "v8.2",
    "v8.4",
    "v8.5",
    "v9",
    "v10",
    "final execution",
    "master prompt",
    "absolute protocol",
    "system identity",
    "product identity",
    "operational intelligence",
    "stell-ai",
    "stellcodex",
    "ssot",
]

PATH_SIGNALS = [
    "docs/",
    "prompts/",
    "policies/",
    "playbooks/",
    "constitution",
    "contracts",
    "protocol",
    "security",
    "release",
    "deploy",
    "recovery",
    "restore",
    "backup",
    "drive",
    "cloudflare",
    "vercel",
    "truth",
    "ssot",
    "manuals/",
    "handoff/",
    "workflows/",
    "audit",
    "evidence",
    "govern",
    "policy",
    "context",
    "identity",
    "tenancy",
    "tenant",
]

ALLOWED_TEXT_EXTS = {
    ".md",
    ".txt",
    ".yaml",
    ".yml",
    ".json",
    ".toml",
    ".py",
    ".sh",
    ".js",
    ".ts",
    ".tsx",
    ".sql",
    ".conf",
    ".cfg",
    ".ini",
    ".env",
}

ALLOWED_BINARY_EXTS = {
    ".pdf",
    ".docx",
}

ALWAYS_INCLUDE_NAMES = {
    "README.md",
    "README_MASTER.md",
    "CLAUDE.md",
    "FINAL_REPORT_20260213.md",
    "FINAL_EVIDENCE_20260227.md",
    "RELEASE_GATE.md",
    "rbac.policy.json",
    "ACTIVE_PROMPT_MANIFEST.json",
    "MASTER_PROMPT_INVENTORY.json",
    "MASTER_PROMPT_INVENTORY.csv",
    "PROMPT_CONFLICT_REPORT.md",
    "PROMPT_CONFLICTS.json",
    "PROMPT_DUPLICATES.json",
}

CODE_HINTS = (
    "guard",
    "policy",
    "prompt",
    "contract",
    "protocol",
    "constitution",
    "release",
    "backup",
    "restore",
    "deploy",
    "identity",
    "tenant",
    "tenancy",
    "rbac",
    "permission",
    "workflow",
    "topology",
    "cleanup",
    "state_freeze",
    "orchestrator_task",
)

EXCLUDE_PARTS = {
    ".git",
    ".venv",
    "node_modules",
    "__pycache__",
    "site-packages",
    "dist",
    "build",
    ".next",
    "qdrant_db",
    "qdrant_store",
    "objects",
    ".minio.sys",
    "05_whatsapp_ingest",
    "blobs",
    "collection",
    "logs",
    "lib64",
}

PRIMARY_DIR_MAP = {
    "MASTER_ACTIVE": "01_ACTIVE_MASTER",
    "SUPPORTING_ACTIVE": "02_ACTIVE_SUPPORTING",
    "CONFLICTING": "03_CONFLICTING",
    "DEPRECATED_ARCHIVE": "04_DEPRECATED_ARCHIVE",
}

SOURCE_DIR_MAP = {
    "SERVER": "05_SOURCE_SERVER",
    "GITHUB": "06_SOURCE_GITHUB",
    "GDRIVE": "07_SOURCE_DRIVE_ORIGINAL",
}

TOPIC_PATTERNS = [
    ("IDENTITY", ("identity", "core", "single voice", "product identity", "stell-ai")),
    ("SECURITY", ("security", "rbac", "permission", "guard", "audit", "secret")),
    ("RECOVERY", ("recovery", "restore", "disaster", "rollback")),
    ("STORAGE", ("storage", "backup", "drive", "minio", "s3", "state", "persistence")),
    ("DEPLOYMENT", ("deploy", "deployment", "vercel", "cloudflare", "topology", "nginx")),
    ("RELEASE", ("release", "gate", "acceptance", "ship", "ci")),
    ("ARCHITECTURE", ("architecture", "topology", "design", "viewer", "event spine")),
    ("EXECUTION", ("execution", "phase", "handoff", "workflow", "task", "runbook")),
    ("GOVERNANCE", ("governance", "ssot", "binding", "source of truth", "constitution")),
    ("OPERATIONS", ("ops", "platform", "runtime", "system state", "orchestra")),
    ("CONTEXT", ("context", "manual", "knowledge", "prompt", "memory")),
    ("INFRA", ("infra", "docker", "compose", "pm2", "worker", "webhook")),
    ("INTEGRATIONS", ("integration", "cloudflare", "github", "google drive", "whatsapp")),
    ("TENANCY", ("tenant", "tenancy", "isolation")),
    ("AUDIT", ("audit", "evidence", "report", "checklist")),
]

AREA_RULES = {
    "server policy": ("system_state", "platform", "topology", "runtime", "rebuild execution"),
    "Google Drive policy": ("drive", "backup", "sync", "gdrive"),
    "GitHub policy": ("github", "knowledge sync", "hierarchy", "drift"),
    "deployment policy": ("deploy", "topology", "vercel", "cloudflare", "nginx"),
    "release policy": ("release", "gate", "acceptance", "checklist"),
    "recovery policy": ("recovery", "restore", "disaster"),
    "naming/folder standards": ("folder", "layout", "structure", "truth", "manifest"),
    "product identity": ("stellcodex v7 master", "master teknik", "product identity", "cad"),
    "STELL-AI identity": ("stell-ai", "master prompt", "core", "single voice"),
    "storage truth": ("storage", "backup", "decision_json", "rule_configs", "drive"),
    "stateless server rule": ("stateless", "cleanup", "server rebuildable"),
    "persistent data rule": ("persistent", "drive", "backup", "storage"),
    "orchestration rule": ("orchestrator", "swarm", "judge", "event spine"),
    "tenant isolation rule": ("tenant isolation", "tenant", "scope"),
}


@dataclass
class Item:
    source_type: str
    source_location: str
    repo_or_drive_path: str
    server_path_if_any: str
    original_filename: str
    ext: str
    content_bytes: bytes
    is_text: bool
    text: str
    content_hash: str
    canonical_hash: str
    basename_key: str
    concept_key: str
    version_marker: str
    role: str
    inferred_status: str
    topical_class: str
    authority_score: str
    notes: List[str] = field(default_factory=list)
    discovered_id: str = ""
    normalized_filename: str = ""
    duplicate_group_id: str = ""
    conflicts_with: List[str] = field(default_factory=list)
    action_taken: str = ""
    copied_to_drive_path: str = ""
    local_primary_path: str = ""
    local_source_path: str = ""


def reset_output() -> None:
    if LOCAL_ROOT.exists():
        shutil.rmtree(LOCAL_ROOT)
    for rel in [
        "00_INDEX",
        "01_ACTIVE_MASTER",
        "02_ACTIVE_SUPPORTING",
        "03_CONFLICTING",
        "04_DEPRECATED_ARCHIVE",
        "05_SOURCE_SERVER",
        "06_SOURCE_GITHUB",
        "07_SOURCE_DRIVE_ORIGINAL",
        "08_MANIFESTS",
        "09_GAP_REPORT",
        "10_RENAME_MAP",
        "11_VERSION_MAP",
        "12_AUTHORITY_MAP",
    ]:
        (CONTRACTS_LOCAL_ROOT / rel).mkdir(parents=True, exist_ok=True)


def run_cmd(args: Sequence[str], binary: bool = False, allow_fail: bool = False) -> bytes | str:
    proc = subprocess.run(args, capture_output=True)
    if proc.returncode != 0 and not allow_fail:
        raise RuntimeError(f"command failed: {' '.join(args)}\n{proc.stderr.decode(errors='ignore')}")
    if binary:
        return proc.stdout
    return proc.stdout.decode("utf-8", errors="ignore")


def stable_id(seed: str) -> str:
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]


def short_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:8]


def detect_ext(name: str) -> str:
    lower = name.lower()
    if lower.endswith(".env.example"):
        return ".env.example"
    for suffix in sorted(ALLOWED_TEXT_EXTS | ALLOWED_BINARY_EXTS, key=len, reverse=True):
        if lower.endswith(suffix):
            return suffix
    return Path(name).suffix.lower()


def slugify(text: str, limit: int = 48) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    slug = re.sub(r"_+", "_", slug)
    return slug[:limit] or "item"


def conceptify(path_or_name: str) -> str:
    lowered = path_or_name.lower()
    lowered = re.sub(r"\.[a-z0-9.]+$", "", lowered)
    lowered = re.sub(r"\b(v\d+(?:\.\d+)*)\b", " ", lowered)
    lowered = re.sub(r"\b(final|master|ssot|locked|hard_locked|hard-locked|absolute|copy|current|latest)\b", " ", lowered)
    lowered = re.sub(r"[\d]{8,}", " ", lowered)
    lowered = re.sub(r"[^a-z]+", " ", lowered)
    parts = [p for p in lowered.split() if p not in {"md", "txt", "json", "yaml", "yml", "repo", "root", "docs"}]
    return "_".join(parts[:6]) or slugify(path_or_name, 24)


def canonicalize_text(text: str) -> str:
    lowered = text.lower()
    lowered = re.sub(r"[0-9]{4}-[0-9]{2}-[0-9]{2}[^\s]*", " ", lowered)
    lowered = re.sub(r"[0-9]{8,}", " ", lowered)
    lowered = re.sub(r"\s+", " ", lowered)
    return lowered.strip()


def should_exclude(path_str: str) -> bool:
    parts = [part.lower() for part in Path(path_str).parts]
    return any(part in EXCLUDE_PARTS for part in parts)


def path_signal(path_str: str) -> bool:
    lowered = path_str.lower()
    if Path(path_str).name in ALWAYS_INCLUDE_NAMES:
        return True
    if any(signal in lowered for signal in PATH_SIGNALS):
        return True
    ext = detect_ext(path_str)
    if ext in {".py", ".sh", ".js", ".ts", ".tsx"} and any(hint in lowered for hint in CODE_HINTS):
        return True
    return False


def content_signal(text: str) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in KEYWORDS)


def is_text_ext(ext: str) -> bool:
    return ext in ALLOWED_TEXT_EXTS or ext == ".env.example"


def active_signals(text: str, lowered_path: str) -> List[str]:
    signals: List[str] = []
    lowered = text.lower()
    if any(token in lowered for token in ["binding", "ssot", "source of truth", "canonical", "single voice"]):
        signals.append("binding")
    if "only v7_master is binding" in lowered:
        signals.append("v7_binding")
    if "master prompt" in lowered or "constitution" in lowered:
        signals.append("master")
    if any(part in lowered_path for part in ["/01_truth/", "/constitution/", "/contracts/", "/prompts/"]):
        signals.append("truth_path")
    return signals


def deprecated_signals(text: str, lowered_path: str) -> List[str]:
    signals: List[str] = []
    lowered = text.lower()
    if any(token in lowered_path for token in ["/archive/", "/archive_legacy/", "/legacy_", "/deprecated", "/v6/"]):
        signals.append("path_archive")
    if any(token in lowered for token in ["deprecated", "obsolete", "legacy", "archived", "superseded"]):
        signals.append("content_archive")
    return signals


def detect_version(path_str: str, text: str) -> str:
    lowered = f"{path_str}\n{text}".lower()
    markers: List[str] = []
    for token in ["hard-locked", "locked", "absolute", "final", "master"]:
        if token in lowered:
            markers.append(token.upper().replace("-", "_"))
    versions = re.findall(r"\bv(\d+(?:\.\d+)*)\b", lowered)
    for version in versions:
        marker = f"V{version}"
        if marker not in markers:
            markers.append(marker)
    return "|".join(markers) if markers else "UNVERSIONED"


def classify_topic(path_str: str, text: str) -> str:
    lowered = f"{path_str}\n{text}".lower()
    for topic, patterns in TOPIC_PATTERNS:
        if any(pattern in lowered for pattern in patterns):
            return topic
    return "GOVERNANCE"


def classify_role_and_status(path_str: str, text: str) -> Tuple[str, str, List[str]]:
    lowered_path = path_str.lower()
    notes: List[str] = []
    active = active_signals(text, lowered_path)
    deprecated = deprecated_signals(text, lowered_path)
    if deprecated and not active:
        if any(token in lowered_path for token in ["/archive/", "/backup", "/handoff/"]):
            notes.append("archival path")
            return "ARCHIVAL", "ARCHIVAL", notes
        notes.append("deprecated/legacy signals")
        return "DEPRECATED", "DEPRECATED", notes
    if active or any(token in lowered_path for token in ["constitution", "master_prompt", "01_truth", "_truth"]):
        notes.append("binding or SSOT signals")
        return "MASTER", "ACTIVE", notes
    if any(token in lowered_path for token in ["contracts", "protocol", "policy", "playbook", "release", "deploy", "security", "ops", "manuals", "workflows"]):
        notes.append("supporting governance path")
        return "SUPPORTING", "ACTIVE", notes
    if any(token in lowered_path for token in ["/reports/", "/evidence/", "/handoff/", "/archive/"]):
        notes.append("historical or evidentiary path")
        return "ARCHIVAL", "ARCHIVAL", notes
    notes.append("unclear role")
    return "UNCLEAR", "UNCLEAR", notes


def authority_score(role: str, status: str, path_str: str, text: str) -> str:
    lowered = f"{path_str}\n{text}".lower()
    if role == "MASTER" and status == "ACTIVE":
        return "HIGH - active binding or SSOT authority"
    if any(token in lowered for token in ["binding", "ssot", "single voice", "source of truth"]):
        return "HIGH - explicit authority language"
    if role in {"SUPPORTING", "MASTER"} and status in {"ACTIVE", "UNCLEAR"}:
        return "MEDIUM - supporting operational authority"
    return "LOW - historical, archival, or ambiguous"


def read_local_file(path: Path) -> Optional[Tuple[bytes, bool, str]]:
    try:
        raw = path.read_bytes()
    except Exception:
        return None
    ext = detect_ext(path.name)
    if is_text_ext(ext):
        text = raw.decode("utf-8", errors="ignore")
        return raw, True, text
    return raw, False, ""


def make_item(
    source_type: str,
    source_location: str,
    repo_or_drive_path: str,
    server_path_if_any: str,
    original_filename: str,
    content_bytes: bytes,
    is_text: bool,
    text: str,
) -> Item:
    ext = detect_ext(original_filename)
    canonical_text = canonicalize_text(text) if is_text else ""
    role, status, role_notes = classify_role_and_status(source_location, text)
    topic = classify_topic(source_location, text)
    version = detect_version(source_location, text)
    auth = authority_score(role, status, source_location, text)
    basename_key = slugify(Path(original_filename).stem, 64)
    concept_key = conceptify(source_location)
    return Item(
        source_type=source_type,
        source_location=source_location,
        repo_or_drive_path=repo_or_drive_path,
        server_path_if_any=server_path_if_any,
        original_filename=original_filename,
        ext=ext,
        content_bytes=content_bytes,
        is_text=is_text,
        text=text,
        content_hash=hashlib.sha256(content_bytes).hexdigest(),
        canonical_hash=hashlib.sha256(canonical_text.encode("utf-8")).hexdigest() if canonical_text else hashlib.sha256(content_bytes).hexdigest(),
        basename_key=basename_key,
        concept_key=concept_key,
        version_marker=version,
        role=role,
        inferred_status=status,
        topical_class=topic,
        authority_score=auth,
        notes=role_notes,
    )


def discover_server_files() -> List[Item]:
    items: List[Item] = []
    seen_locations: set[str] = set()
    for root in SERVER_ROOTS:
        if not root.exists():
            continue
        for current_root, dirs, files in os.walk(root):
            dirs[:] = [d for d in dirs if d.lower() not in EXCLUDE_PARTS]
            for filename in files:
                path = Path(current_root) / filename
                path_str = str(path)
                if path_str in seen_locations or should_exclude(path_str):
                    continue
                ext = detect_ext(filename)
                if ext not in ALLOWED_TEXT_EXTS and ext not in ALLOWED_BINARY_EXTS and filename not in ALWAYS_INCLUDE_NAMES:
                    continue
                path_has_signal = path_signal(path_str)
                file_read = read_local_file(path)
                if not file_read:
                    continue
                raw, is_text, text = file_read
                if not path_has_signal and not (is_text and content_signal(text)):
                    continue
                item = make_item(
                    source_type="SERVER",
                    source_location=path_str,
                    repo_or_drive_path=path_str,
                    server_path_if_any=path_str,
                    original_filename=filename,
                    content_bytes=raw,
                    is_text=is_text,
                    text=text,
                )
                items.append(item)
                seen_locations.add(path_str)
    for loose in SERVER_LOOSE_FILES:
        if loose.exists() and str(loose) not in seen_locations and loose.is_file():
            file_read = read_local_file(loose)
            if file_read:
                raw, is_text, text = file_read
                item = make_item(
                    source_type="SERVER",
                    source_location=str(loose),
                    repo_or_drive_path=str(loose),
                    server_path_if_any=str(loose),
                    original_filename=loose.name,
                    content_bytes=raw,
                    is_text=is_text,
                    text=text,
                )
                items.append(item)
                seen_locations.add(str(loose))
    return items


def discover_server_archives() -> List[Item]:
    items: List[Item] = []
    for archive_path in SERVER_ARCHIVES:
        if not archive_path.exists():
            continue
        if archive_path.suffix.lower() == ".zip":
            with zipfile.ZipFile(archive_path) as zf:
                for member in zf.infolist():
                    if member.is_dir():
                        continue
                    member_path = member.filename
                    if should_exclude(member_path):
                        continue
                    ext = detect_ext(member.filename)
                    if ext not in ALLOWED_TEXT_EXTS and ext not in ALLOWED_BINARY_EXTS:
                        continue
                    if not path_signal(member_path):
                        continue
                    raw = zf.read(member)
                    is_text = is_text_ext(ext)
                    text = raw.decode("utf-8", errors="ignore") if is_text else ""
                    item = make_item(
                        source_type="SERVER",
                        source_location=f"zip:{archive_path}!{member_path}",
                        repo_or_drive_path=f"zip:{archive_path}!{member_path}",
                        server_path_if_any=f"{archive_path}!{member_path}",
                        original_filename=Path(member_path).name,
                        content_bytes=raw,
                        is_text=is_text,
                        text=text,
                    )
                    item.notes.append("archive member")
                    items.append(item)
        elif archive_path.suffixes[-2:] == [".tar", ".gz"] or archive_path.suffix.lower() == ".tar":
            with tarfile.open(archive_path, "r:*") as tf:
                for member in tf.getmembers():
                    if not member.isfile():
                        continue
                    member_path = member.name
                    if should_exclude(member_path):
                        continue
                    ext = detect_ext(member_path)
                    if ext not in ALLOWED_TEXT_EXTS and ext not in ALLOWED_BINARY_EXTS:
                        continue
                    if not path_signal(member_path):
                        continue
                    extracted = tf.extractfile(member)
                    if extracted is None:
                        continue
                    raw = extracted.read()
                    is_text = is_text_ext(ext)
                    text = raw.decode("utf-8", errors="ignore") if is_text else ""
                    item = make_item(
                        source_type="SERVER",
                        source_location=f"tar:{archive_path}!{member_path}",
                        repo_or_drive_path=f"tar:{archive_path}!{member_path}",
                        server_path_if_any=f"{archive_path}!{member_path}",
                        original_filename=Path(member_path).name,
                        content_bytes=raw,
                        is_text=is_text,
                        text=text,
                    )
                    item.notes.append("archive member")
                    items.append(item)
    return items


def rclone_list(remote: str) -> List[str]:
    output = run_cmd(["rclone", "lsf", "-R", remote], allow_fail=True)
    return [line.strip() for line in str(output).splitlines() if line.strip()]


def rclone_cat(remote_with_path: str) -> bytes:
    return run_cmd(["rclone", "cat", remote_with_path], binary=True)


def discover_drive_files() -> List[Item]:
    items: List[Item] = []
    for remote in DRIVE_REMOTES:
        try:
            paths = rclone_list(remote)
        except Exception:
            continue
        for rel_path in paths:
            if rel_path.endswith("/"):
                continue
            full = f"{remote}/{rel_path}"
            if should_exclude(rel_path):
                continue
            ext = detect_ext(rel_path)
            if ext not in ALLOWED_TEXT_EXTS and ext not in ALLOWED_BINARY_EXTS and Path(rel_path).name not in ALWAYS_INCLUDE_NAMES:
                continue
            if not path_signal(rel_path):
                continue
            try:
                raw = rclone_cat(full)
            except Exception:
                continue
            is_text = is_text_ext(ext)
            text = raw.decode("utf-8", errors="ignore") if is_text else ""
            if not path_signal(rel_path) and not (is_text and content_signal(text)):
                continue
            item = make_item(
                source_type="GDRIVE",
                source_location=full,
                repo_or_drive_path=full,
                server_path_if_any="",
                original_filename=Path(rel_path).name,
                content_bytes=raw,
                is_text=is_text,
                text=text,
            )
            items.append(item)
    return items


def gh_json(args: Sequence[str]) -> object:
    text = run_cmd(args)
    return json.loads(str(text))


def github_repos() -> List[Tuple[str, str]]:
    repos = gh_json(
        [
            "gh",
            "repo",
            "list",
            "stellcodex",
            "--limit",
            "100",
            "--json",
            "nameWithOwner,isPrivate,defaultBranchRef,url",
        ]
    )
    results: List[Tuple[str, str]] = []
    for entry in repos:
        name = entry["nameWithOwner"]
        default_branch = entry.get("defaultBranchRef", {}).get("name") or "main"
        results.append((name, default_branch))
    return results


def github_branches(repo: str, default_branch: str) -> List[str]:
    if repo == "stellcodex/stellcodex":
        output = run_cmd(
            ["gh", "api", f"repos/{repo}/branches?per_page=100", "--jq", ".[].name"],
            allow_fail=True,
        )
        lines = [line.strip() for line in str(output).splitlines() if line.strip()]
        filtered = [
            branch
            for branch in lines
            if branch in {"main", "master"}
            or branch.startswith("release/")
            or branch.startswith("backup/")
            or branch.startswith("fix/")
            or branch.startswith("codex/")
        ]
        return filtered or [default_branch]
    return [default_branch]


def github_branch_sha(repo: str, branch: str) -> Optional[str]:
    api_path = f"repos/{repo}/branches/{quote(branch, safe='')}"
    try:
        payload = gh_json(["gh", "api", api_path])
    except Exception:
        return None
    return payload.get("commit", {}).get("sha")


def github_tree(repo: str, sha: str) -> List[str]:
    output = run_cmd(["gh", "api", f"repos/{repo}/git/trees/{sha}?recursive=1", "--jq", ".tree[].path"], allow_fail=True)
    return [line.strip() for line in str(output).splitlines() if line.strip()]


def github_raw(repo: str, path: str, branch: str) -> bytes:
    return run_cmd(
        [
            "gh",
            "api",
            "-H",
            "Accept: application/vnd.github.raw",
            f"repos/{repo}/contents/{path}?ref={quote(branch, safe='')}",
        ],
        binary=True,
    )


def discover_github_files() -> List[Item]:
    items: List[Item] = []
    for repo, default_branch in github_repos():
        for branch in github_branches(repo, default_branch):
            sha = github_branch_sha(repo, branch)
            if not sha:
                continue
            paths = github_tree(repo, sha)
            for rel_path in paths:
                if should_exclude(rel_path):
                    continue
                ext = detect_ext(rel_path)
                if ext not in ALLOWED_TEXT_EXTS and ext not in ALLOWED_BINARY_EXTS and Path(rel_path).name not in ALWAYS_INCLUDE_NAMES:
                    continue
                if not path_signal(rel_path):
                    continue
                try:
                    raw = github_raw(repo, rel_path, branch)
                except Exception:
                    continue
                is_text = is_text_ext(ext)
                text = raw.decode("utf-8", errors="ignore") if is_text else ""
                if not path_signal(rel_path) and not (is_text and content_signal(text)):
                    continue
                item = make_item(
                    source_type="GITHUB",
                    source_location=f"https://github.com/{repo}/blob/{branch}/{rel_path}",
                    repo_or_drive_path=f"{repo}@{branch}:{rel_path}",
                    server_path_if_any="",
                    original_filename=Path(rel_path).name,
                    content_bytes=raw,
                    is_text=is_text,
                    text=text,
                )
                if branch != default_branch:
                    item.notes.append(f"branch:{branch}")
                items.append(item)
    return items


def assign_duplicate_groups(items: List[Item]) -> None:
    exact_groups: Dict[str, List[Item]] = {}
    canon_groups: Dict[str, List[Item]] = {}
    for item in items:
        exact_groups.setdefault(item.content_hash, []).append(item)
        canon_groups.setdefault(item.canonical_hash, []).append(item)
    for digest, group in exact_groups.items():
        if len(group) > 1:
            group_id = f"EXACT_{digest[:8]}"
            for item in group:
                item.duplicate_group_id = group_id
                item.notes.append("exact duplicate group")
    for digest, group in canon_groups.items():
        if len(group) > 1:
            group_id = f"CANON_{digest[:8]}"
            for item in group:
                if not item.duplicate_group_id:
                    item.duplicate_group_id = group_id
                    item.notes.append("canonical duplicate group")


def assign_conflicts(items: List[Item]) -> None:
    concept_groups: Dict[Tuple[str, str], List[Item]] = {}
    for item in items:
        concept_groups.setdefault((item.concept_key, item.topical_class), []).append(item)
    for (_concept, _topic), group in concept_groups.items():
        if len(group) < 2:
            continue
        hashes = {item.content_hash for item in group}
        if len(hashes) == 1:
            continue
        active_like = [item for item in group if item.inferred_status in {"ACTIVE", "UNCLEAR"}]
        if len(active_like) < 2:
            continue
        names = {item.original_filename for item in group}
        if len(names) == 1 or any(item.version_marker != active_like[0].version_marker for item in active_like):
            ids = [item.discovered_id for item in active_like]
            for item in active_like:
                item.conflicts_with = [other for other in ids if other != item.discovered_id]
                if item.role not in {"ARCHIVAL", "DEPRECATED"}:
                    item.role = "CONFLICTING"
                    item.inferred_status = "CONFLICTING"
                    item.notes.append("concept overlap or version divergence")
    drive_root_docs = [item for item in items if "drive" in item.source_location.lower() and "backup" in item.source_location.lower()]
    remotes: Dict[str, List[Item]] = {}
    for item in drive_root_docs:
        match = re.findall(r"gdrive:[a-zA-Z0-9._-]+", item.text)
        for remote in match:
            remotes.setdefault(remote, []).append(item)
    if len(remotes) > 1:
        ids = sorted({item.discovered_id for group in remotes.values() for item in group})
        for group in remotes.values():
            for item in group:
                item.conflicts_with = [other for other in ids if other != item.discovered_id]
                if item.role not in {"ARCHIVAL", "DEPRECATED"}:
                    item.role = "CONFLICTING"
                    item.inferred_status = "CONFLICTING"
                    item.notes.append("drive root divergence")


def choose_primary_dir(item: Item) -> str:
    if item.inferred_status == "CONFLICTING" or item.role == "CONFLICTING":
        return PRIMARY_DIR_MAP["CONFLICTING"]
    if item.role in {"DEPRECATED", "ARCHIVAL"} or item.inferred_status in {"DEPRECATED", "ARCHIVAL"}:
        return PRIMARY_DIR_MAP["DEPRECATED_ARCHIVE"]
    if item.role == "MASTER" and item.inferred_status == "ACTIVE":
        return PRIMARY_DIR_MAP["MASTER_ACTIVE"]
    return PRIMARY_DIR_MAP["SUPPORTING_ACTIVE"]


def make_normalized_name(item: Item) -> str:
    role = item.role if item.role != "UNCLEAR" else "SUPPORTING"
    topic = item.topical_class
    version = item.version_marker.replace("|", "_")
    source = item.source_type
    slug = slugify(Path(item.original_filename).stem)
    return f"{role}__{topic}__{version}__{source}__{slug}__{short_hash(item.content_bytes)}{item.ext or ''}"


def write_item_files(items: List[Item]) -> None:
    for index, item in enumerate(items, start=1):
        item.discovered_id = f"D{index:04d}"
    for item in items:
        item.normalized_filename = make_normalized_name(item)
        primary_dir = choose_primary_dir(item)
        source_dir = SOURCE_DIR_MAP[item.source_type]
        primary_path = CONTRACTS_LOCAL_ROOT / primary_dir / item.normalized_filename
        source_path = CONTRACTS_LOCAL_ROOT / source_dir / item.normalized_filename
        primary_path.write_bytes(item.content_bytes)
        source_path.write_bytes(item.content_bytes)
        item.local_primary_path = str(primary_path)
        item.local_source_path = str(source_path)
        item.copied_to_drive_path = f"{REMOTE_ROOT}/{primary_dir}/{item.normalized_filename}"
        item.action_taken = f"copied_to_{primary_dir}_and_{source_dir}"


def build_gap_report(items: List[Item]) -> List[str]:
    notes: List[str] = []
    if not Path("/root/workspace/_truth").exists():
        notes.append("Referenced local SSOT directory `/root/workspace/_truth` is absent on the server; multiple STELL files reference it as canonical.")
    tenant_docs = [
        item
        for item in items
        if "tenant isolation" in item.text.lower()
        or "tenant" in item.source_location.lower() and item.role in {"MASTER", "SUPPORTING"}
    ]
    if not tenant_docs:
        notes.append("No clear standalone governing document for tenant isolation was found; current evidence is mostly code, tests, and evidence artifacts.")
    stateless_docs = [item for item in items if "stateless" in item.text.lower() or "server rebuildable" in item.text.lower()]
    if not stateless_docs:
        notes.append("No explicit active stateless-server policy document was found; server hygiene is encoded in scripts and evidence, not in one clear authority document.")
    drive_roots = sorted({remote for item in items for remote in re.findall(r"gdrive:[a-zA-Z0-9._-]+", item.text)})
    if len(drive_roots) > 1:
        notes.append(f"Multiple Drive roots are simultaneously referenced as canonical or primary: {', '.join(drive_roots)}.")
    return notes


def best_matches(items: List[Item], patterns: Iterable[str]) -> List[Item]:
    pattern_list = [pattern.lower() for pattern in patterns]
    scored: List[Tuple[int, Item]] = []
    for item in items:
        if item.inferred_status in {"DEPRECATED", "ARCHIVAL"}:
            continue
        corpus = f"{item.source_location}\n{item.text}".lower()
        score = sum(1 for pattern in pattern_list if pattern in corpus)
        if score:
            if item.authority_score.startswith("HIGH"):
                score += 10
            elif item.authority_score.startswith("MEDIUM"):
                score += 5
            scored.append((score, item))
    scored.sort(key=lambda pair: (-pair[0], pair[1].discovered_id))
    return [item for _score, item in scored[:3]]


def write_markdown(path: Path, body: str) -> None:
    path.write_text(body.rstrip() + "\n", encoding="utf-8")


def write_reports(items: List[Item]) -> Dict[str, str]:
    gaps = build_gap_report(items)
    exact_duplicates = len({item.duplicate_group_id for item in items if item.duplicate_group_id.startswith("EXACT_")})
    conflicts = [item for item in items if item.inferred_status == "CONFLICTING"]
    deprecated = [item for item in items if item.role in {"DEPRECATED", "ARCHIVAL"} or item.inferred_status in {"DEPRECATED", "ARCHIVAL"}]
    masters = [item for item in items if item.role == "MASTER" and item.inferred_status == "ACTIVE"]
    lines = [
        "# STELLCODEX Contracts Consolidation Summary",
        "",
        f"- Total discovered files: {len(items)}",
        f"- Total copied files: {len(items)}",
        f"- Exact duplicate groups: {exact_duplicates}",
        f"- Conflict items: {len(conflicts)}",
        f"- Deprecated or archival items: {len(deprecated)}",
        f"- Active master candidates: {len(masters)}",
        f"- Authority gaps: {len(gaps)}",
        "",
    ]
    active_lines = ["# Active Master Candidates", ""]
    for item in masters:
        active_lines.append(f"- {item.discovered_id} | `{item.original_filename}` | {item.source_type} | {item.source_location}")

    conflict_lines = ["# Conflict Report", ""]
    if conflicts:
        for item in conflicts:
            reason = "; ".join(sorted(set(item.notes)))
            conflict_lines.append(
                f"- {item.discovered_id} conflicts with {', '.join(item.conflicts_with)} | `{item.original_filename}` | {reason}"
            )
    else:
        conflict_lines.append("- No active conflicts detected by the consolidation heuristics.")

    deprecation_lines = ["# Deprecation Map", ""]
    for item in deprecated:
        supersedes = (
            "STELLCODEX_ARCHIVE_ROOT/01_CONSTITUTION_AND_PROTOCOLS/STELLCODEX_V10_ABSOLUTE_SYSTEM_CONSTITUTION.md"
            if "/v6/" in item.source_location.lower()
            else "unknown"
        )
        deprecation_lines.append(
            f"- {item.discovered_id} | `{item.original_filename}` | status={item.inferred_status} | likely superseded by `{supersedes}`"
        )
    if len(deprecation_lines) == 2:
        deprecation_lines.append("- No deprecated or archival items were detected.")

    authority_lines = ["# Authority Map", ""]
    active_pool = [item for item in items if item.inferred_status not in {"DEPRECATED", "ARCHIVAL"}]
    for area, patterns in AREA_RULES.items():
        matches = best_matches(active_pool, patterns)
        if matches:
            authority_lines.append(f"- {area}:")
            for item in matches:
                authority_lines.append(f"  - {item.discovered_id} | `{item.original_filename}` | {item.source_type} | {item.source_location}")
        else:
            authority_lines.append(f"- {area}: GAP")

    gap_lines = ["# Gap Report", ""]
    if gaps:
        for gap in gaps:
            gap_lines.append(f"- {gap}")
    else:
        gap_lines.append("- No explicit authority gaps were detected.")

    rename_csv = CONTRACTS_LOCAL_ROOT / "10_RENAME_MAP" / "RENAME_MAP.csv"
    with rename_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["discovered_id", "original_filename", "source_location", "normalized_filename"])
        for item in items:
            writer.writerow([item.discovered_id, item.original_filename, item.source_location, item.normalized_filename])

    version_md = CONTRACTS_LOCAL_ROOT / "11_VERSION_MAP" / "VERSION_MAP.md"
    version_lines = ["# Version Map", ""]
    grouped: Dict[str, List[Item]] = {}
    for item in items:
        grouped.setdefault(item.concept_key, []).append(item)
    for concept, group in sorted(grouped.items()):
        version_lines.append(f"## {concept}")
        for item in sorted(group, key=lambda current: current.discovered_id):
            version_lines.append(
                f"- {item.discovered_id} | {item.version_marker} | {item.role}/{item.inferred_status} | `{item.original_filename}` | {item.source_type}"
            )
        version_lines.append("")

    paths = {
        "summary": str(CONTRACTS_LOCAL_ROOT / "00_INDEX" / "CONSOLIDATION_SUMMARY.md"),
        "active": str(CONTRACTS_LOCAL_ROOT / "00_INDEX" / "ACTIVE_MASTER_CANDIDATES.md"),
        "conflicts": str(CONTRACTS_LOCAL_ROOT / "03_CONFLICTING" / "CONFLICT_REPORT.md"),
        "deprecations": str(CONTRACTS_LOCAL_ROOT / "04_DEPRECATED_ARCHIVE" / "DEPRECATION_MAP.md"),
        "authority": str(CONTRACTS_LOCAL_ROOT / "12_AUTHORITY_MAP" / "AUTHORITY_MAP.md"),
        "gaps": str(CONTRACTS_LOCAL_ROOT / "09_GAP_REPORT" / "GAP_REPORT.md"),
        "version_map": str(version_md),
        "rename_map": str(rename_csv),
    }
    write_markdown(Path(paths["summary"]), "\n".join(lines))
    write_markdown(Path(paths["active"]), "\n".join(active_lines))
    write_markdown(Path(paths["conflicts"]), "\n".join(conflict_lines))
    write_markdown(Path(paths["deprecations"]), "\n".join(deprecation_lines))
    write_markdown(Path(paths["authority"]), "\n".join(authority_lines))
    write_markdown(Path(paths["gaps"]), "\n".join(gap_lines))
    write_markdown(version_md, "\n".join(version_lines))
    return paths


def write_manifest(items: List[Item]) -> Dict[str, str]:
    csv_path = CONTRACTS_LOCAL_ROOT / "08_MANIFESTS" / "contracts_manifest.csv"
    md_path = CONTRACTS_LOCAL_ROOT / "08_MANIFESTS" / "contracts_manifest.md"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "discovered_id",
                "normalized_filename",
                "original_filename",
                "source_type",
                "source_location",
                "repository_or_drive_path",
                "server_path_if_any",
                "version_marker",
                "inferred_status",
                "topical_class",
                "authority_score",
                "duplicate_group_id",
                "conflicts_with",
                "action_taken",
                "copied_to_drive_path",
                "notes",
            ]
        )
        for item in items:
            writer.writerow(
                [
                    item.discovered_id,
                    item.normalized_filename,
                    item.original_filename,
                    item.source_type,
                    item.source_location,
                    item.repo_or_drive_path,
                    item.server_path_if_any,
                    item.version_marker,
                    item.inferred_status,
                    item.topical_class,
                    item.authority_score,
                    item.duplicate_group_id,
                    "|".join(item.conflicts_with),
                    item.action_taken,
                    item.copied_to_drive_path,
                    "; ".join(sorted(set(item.notes))),
                ]
            )

    md_lines = [
        "# Contracts Manifest",
        "",
        "| discovered_id | normalized_filename | source_type | version | status | topic | duplicate_group_id | conflicts_with |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in items:
        md_lines.append(
            f"| {item.discovered_id} | `{item.normalized_filename}` | {item.source_type} | {item.version_marker} | {item.inferred_status} | {item.topical_class} | {item.duplicate_group_id or '-'} | {', '.join(item.conflicts_with) or '-'} |"
        )
    write_markdown(md_path, "\n".join(md_lines))
    return {"csv": str(csv_path), "md": str(md_path)}


def sync_to_drive() -> None:
    run_cmd(["rclone", "mkdir", REMOTE_ROOT], allow_fail=True)
    run_cmd(["rclone", "copy", str(CONTRACTS_LOCAL_ROOT) + "/", REMOTE_ROOT])


def verify_drive_tree() -> str:
    return str(run_cmd(["rclone", "lsf", REMOTE_VERIFY_ROOT], allow_fail=True))


def dedupe_by_source(items: List[Item]) -> List[Item]:
    unique: Dict[Tuple[str, str], Item] = {}
    for item in items:
        key = (item.source_type, item.source_location)
        unique[key] = item
    return list(unique.values())


def sort_items(items: List[Item]) -> List[Item]:
    return sorted(items, key=lambda item: (item.source_type, item.source_location))


def main() -> int:
    reset_output()
    items = []
    items.extend(discover_server_files())
    items.extend(discover_server_archives())
    items.extend(discover_drive_files())
    items.extend(discover_github_files())
    items = sort_items(dedupe_by_source(items))
    assign_duplicate_groups(items)
    write_item_files(items)
    assign_conflicts(items)
    for item in items:
        if item.inferred_status == "CONFLICTING":
            primary_path = CONTRACTS_LOCAL_ROOT / PRIMARY_DIR_MAP["CONFLICTING"] / item.normalized_filename
            if Path(item.local_primary_path) != primary_path:
                shutil.copy2(item.local_primary_path, primary_path)
                item.local_primary_path = str(primary_path)
                item.copied_to_drive_path = f"{REMOTE_ROOT}/{PRIMARY_DIR_MAP['CONFLICTING']}/{item.normalized_filename}"
                item.action_taken = f"copied_to_{PRIMARY_DIR_MAP['CONFLICTING']}_and_{SOURCE_DIR_MAP[item.source_type]}"
    manifest_paths = write_manifest(items)
    report_paths = write_reports(items)
    sync_to_drive()
    verify_output = verify_drive_tree()
    meta = {
        "total_items": len(items),
        "manifest_paths": manifest_paths,
        "report_paths": report_paths,
        "remote_root": REMOTE_ROOT,
        "verify_root_listing": verify_output.splitlines(),
    }
    write_markdown(CONTRACTS_LOCAL_ROOT / "00_INDEX" / "RUN_METADATA.json", json.dumps(meta, indent=2))
    print(json.dumps(meta, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
