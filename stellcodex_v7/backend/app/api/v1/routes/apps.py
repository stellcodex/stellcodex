from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.security.deps import Principal, get_current_principal

router = APIRouter(prefix="/apps", tags=["apps"])


class AppCatalogItemOut(BaseModel):
    id: str
    slug: str
    name: str
    category: str
    tier: str
    enabled_by_default: bool
    enabled: bool
    routes: list[str]
    required_capabilities: list[str]
    supported_formats: list[str]


class AppManifestOut(BaseModel):
    slug: str
    manifest: dict[str, Any]


def _backend_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _repo_root_candidates() -> list[Path]:
    backend_root = _backend_root()
    return [backend_root, backend_root.parent]


def _catalog_candidates() -> list[Path]:
    paths: list[Path] = []
    for root in _repo_root_candidates():
        paths.append(root / "marketplace" / "catalog.json")
    return paths


def _manifest_candidates(slug: str) -> list[Path]:
    paths: list[Path] = []
    for root in _repo_root_candidates():
        paths.append(root / "apps" / slug / "app.manifest.json")
    return paths


def _read_json_file(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"invalid json at {path}: {exc}")


def _load_catalog_raw() -> list[dict[str, Any]]:
    for path in _catalog_candidates():
        if not path.exists():
            continue
        payload = _read_json_file(path)
        if not isinstance(payload, list):
            raise HTTPException(status_code=500, detail="marketplace catalog must be a JSON array")
        return [row for row in payload if isinstance(row, dict)]
    raise HTTPException(status_code=500, detail="marketplace/catalog.json not found")


def _disabled_slugs() -> set[str]:
    raw = os.getenv("APPS_DISABLED", "").strip()
    if not raw:
        return set()
    return {item.strip().lower() for item in raw.split(",") if item.strip()}


def _flag_override(slug: str) -> bool | None:
    key = f"APP_{slug.upper().replace('-', '_')}"
    value = os.getenv(key)
    if value is None:
        return None
    token = value.strip().lower()
    if token in {"1", "true", "yes", "on", "enabled"}:
        return True
    if token in {"0", "false", "no", "off", "disabled"}:
        return False
    return None


def _is_enabled(entry: dict[str, Any]) -> bool:
    slug = str(entry.get("slug") or "").strip().lower()
    default_enabled = bool(entry.get("enabled_by_default", False))

    if not slug:
        return False
    if slug in _disabled_slugs():
        return False

    override = _flag_override(slug)
    if override is not None:
        return override
    return default_enabled


def _normalize_catalog_entry(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(entry.get("id") or ""),
        "slug": str(entry.get("slug") or ""),
        "name": str(entry.get("name") or ""),
        "category": str(entry.get("category") or "general"),
        "tier": str(entry.get("tier") or "pro"),
        "enabled_by_default": bool(entry.get("enabled_by_default", False)),
        "enabled": _is_enabled(entry),
        "routes": [str(item) for item in (entry.get("routes") or []) if isinstance(item, str)],
        "required_capabilities": [
            str(item) for item in (entry.get("required_capabilities") or []) if isinstance(item, str)
        ],
        "supported_formats": [str(item) for item in (entry.get("supported_formats") or []) if isinstance(item, str)],
    }


def _manifest_for_slug(slug: str) -> dict[str, Any]:
    for path in _manifest_candidates(slug):
        if not path.exists():
            continue
        payload = _read_json_file(path)
        if not isinstance(payload, dict):
            raise HTTPException(status_code=500, detail=f"manifest for {slug} must be a JSON object")
        return payload
    raise HTTPException(status_code=404, detail=f"manifest not found for slug: {slug}")


@router.get("/catalog", response_model=List[AppCatalogItemOut])
def list_apps_catalog(
    include_disabled: bool = Query(default=False),
    _principal: Principal = Depends(get_current_principal),
):
    rows = [_normalize_catalog_entry(row) for row in _load_catalog_raw()]
    if include_disabled:
        return [AppCatalogItemOut(**row) for row in rows]
    return [AppCatalogItemOut(**row) for row in rows if row["enabled"]]


@router.get("/{slug}/manifest", response_model=AppManifestOut)
def get_app_manifest(
    slug: str,
    _principal: Principal = Depends(get_current_principal),
):
    slug = slug.strip().lower()
    catalog = [_normalize_catalog_entry(row) for row in _load_catalog_raw()]
    row = next((item for item in catalog if item["slug"] == slug), None)
    if row is None:
        raise HTTPException(status_code=404, detail="app not found")
    if not row["enabled"]:
        raise HTTPException(status_code=404, detail="app is disabled by feature flag")

    manifest = _manifest_for_slug(slug)
    return AppManifestOut(slug=slug, manifest=manifest)
