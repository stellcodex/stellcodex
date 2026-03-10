#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any


CANONICAL_ROOT = "STELL"
CANONICAL_FOLDERS = {
    "archive": "00_ARCHIVE",
    "backups": "01_BACKUPS",
    "datasets": "02_DATASETS",
    "evidence": "03_EVIDENCE",
    "reports": "04_REPORTS",
    "model_outputs": "05_MODEL_OUTPUTS",
    "company_docs": "06_COMPANY_DOCS",
    "exports": "07_EXPORTS",
    "stell_ai_memory": "08_STELL_AI_MEMORY",
    "stellcodex_artifacts": "09_STELLCODEX_ARTIFACTS",
    "orchestra_jobs": "10_ORCHESTRA_JOBS",
}


CATEGORY_KEYWORDS: list[tuple[str, tuple[str, ...]]] = [
    ("backups", ("backup", "dump", "restore", "snapshot")),
    ("datasets", ("dataset", "train", "eval", "embedding", "rag", "corpus")),
    ("evidence", ("evidence", "proof", "gate", "smoke", "schema", "contract")),
    ("reports", ("report", "summary", "audit_report", "monthly")),
    ("model_outputs", ("model_output", "inference", "prediction", "generation")),
    ("company_docs", ("contract", "invoice", "policy", "handbook", "legal")),
    ("stell_ai_memory", ("memory", "founder", "solved_case", "conversation")),
    ("stellcodex_artifacts", ("scx", "dfm", "quote", "share", "manufacturing")),
    ("orchestra_jobs", ("queue", "job", "worker", "retry", "dlq", "scheduler", "ingest")),
]


@dataclass
class InventoryItem:
    path: str
    checksum: str
    size_bytes: int
    modified_at: str


@dataclass
class ManifestAction:
    source_path: str
    target_path: str
    category: str
    action: str
    reason: str
    checksum: str
    size_bytes: int


def _load_jsonl(path: Path) -> list[InventoryItem]:
    rows: list[InventoryItem] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        rows.append(
            InventoryItem(
                path=str(payload.get("path") or payload.get("drive_path") or ""),
                checksum=str(payload.get("checksum") or payload.get("sha256") or ""),
                size_bytes=int(payload.get("size_bytes") or payload.get("size") or 0),
                modified_at=str(payload.get("modified_at") or payload.get("modified") or ""),
            )
        )
    return rows


def _load_csv(path: Path) -> list[InventoryItem]:
    rows: list[InventoryItem] = []
    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            rows.append(
                InventoryItem(
                    path=str(row.get("path") or row.get("drive_path") or ""),
                    checksum=str(row.get("checksum") or row.get("sha256") or ""),
                    size_bytes=int(row.get("size_bytes") or row.get("size") or 0),
                    modified_at=str(row.get("modified_at") or row.get("modified") or ""),
                )
            )
    return rows


def _load_inventory(path: Path) -> list[InventoryItem]:
    suffix = path.suffix.lower()
    if suffix == ".jsonl":
        return _load_jsonl(path)
    if suffix == ".csv":
        return _load_csv(path)
    raise ValueError(f"Unsupported inventory format: {path}")


def _strip_root(path: str) -> str:
    normalized = path.strip().lstrip("/")
    if normalized.startswith(f"{CANONICAL_ROOT}/"):
        normalized = normalized[len(CANONICAL_ROOT) + 1 :]
    return normalized


def _pick_category(path: str) -> str:
    lower = path.lower()
    for category, keywords in CATEGORY_KEYWORDS:
        if any(token in lower for token in keywords):
            return category
    return "exports"


def _canonical_target(category: str, source_path: str) -> str:
    folder = CANONICAL_FOLDERS[category]
    basename = Path(source_path).name
    return f"{CANONICAL_ROOT}/{folder}/{basename}"


def build_manifest(items: list[InventoryItem]) -> dict[str, Any]:
    seen_by_fingerprint: dict[str, ManifestAction] = {}
    actions: list[ManifestAction] = []

    for item in items:
        source = _strip_root(item.path)
        if not source:
            continue
        category = _pick_category(source)
        target = _canonical_target(category, source)
        fingerprint = f"{item.checksum}:{item.size_bytes}"

        if fingerprint in seen_by_fingerprint and item.checksum:
            archive_target = f"{CANONICAL_ROOT}/{CANONICAL_FOLDERS['archive']}/{Path(source).name}"
            actions.append(
                ManifestAction(
                    source_path=item.path,
                    target_path=archive_target,
                    category="archive",
                    action="archive_duplicate",
                    reason="duplicate_checksum_and_size",
                    checksum=item.checksum,
                    size_bytes=item.size_bytes,
                )
            )
            continue

        action = "keep" if item.path.strip("/").startswith(target) else "move"
        reason = "already_canonical" if action == "keep" else "normalize_to_canonical_folder"
        manifest_row = ManifestAction(
            source_path=item.path,
            target_path=target,
            category=category,
            action=action,
            reason=reason,
            checksum=item.checksum,
            size_bytes=item.size_bytes,
        )
        actions.append(manifest_row)
        if item.checksum:
            seen_by_fingerprint[fingerprint] = manifest_row

    by_action: dict[str, int] = {}
    by_category: dict[str, int] = {}
    for row in actions:
        by_action[row.action] = by_action.get(row.action, 0) + 1
        by_category[row.category] = by_category.get(row.category, 0) + 1

    return {
        "canonical_root": CANONICAL_ROOT,
        "canonical_folders": CANONICAL_FOLDERS,
        "summary": {
            "total_items": len(actions),
            "by_action": by_action,
            "by_category": by_category,
        },
        "actions": [asdict(row) for row in actions],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate a canonical STELL Google Drive normalization manifest from an inventory export."
    )
    parser.add_argument("--inventory", required=True, help="Path to inventory file (.jsonl or .csv)")
    parser.add_argument("--output", required=True, help="Path to output manifest JSON")
    args = parser.parse_args()

    inventory_path = Path(args.inventory)
    output_path = Path(args.output)

    if not inventory_path.exists():
        raise SystemExit(f"Inventory file not found: {inventory_path}")

    items = _load_inventory(inventory_path)
    manifest = build_manifest(items)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest, ensure_ascii=True, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "output": str(output_path),
                "total_items": manifest["summary"]["total_items"],
                "by_action": manifest["summary"]["by_action"],
            },
            ensure_ascii=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
