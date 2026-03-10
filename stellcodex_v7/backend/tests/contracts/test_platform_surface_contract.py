from __future__ import annotations

import re

from app.core.runtime.repo_language_audit import REPO_ROOT


FRONTEND_ROOT = REPO_ROOT / "frontend"
CATALOG_PATH = FRONTEND_ROOT / "data" / "platformCatalog.ts"
CLIENT_PATH = FRONTEND_ROOT / "components" / "platform" / "PlatformClient.tsx"
SURFACE_DOC_PATH = REPO_ROOT / "backend" / "docs" / "reference" / "app_surface_modes.md"


def test_platform_catalog_assigns_one_surface_per_app() -> None:
    text = CATALOG_PATH.read_text(encoding="utf-8")
    ids = re.findall(r'id:\s*"([^"]+)"', text)
    surfaces = re.findall(r'surface:\s*"([^"]+)"', text)

    expected = {
        "viewer3d": "viewer3d",
        "viewer2d": "viewer2d",
        "docviewer": "docviewer",
        "convert": "job",
        "mesh2d3d": "job",
        "moldcodes": "configurator",
        "library": "route",
        "drive": "route",
        "projects": "route",
        "accounting": "records",
        "socialmanager": "records",
        "feedpublisher": "records",
        "webbuilder": "records",
        "cms": "records",
        "admin": "route",
        "status": "route",
    }

    assert ids
    assert len(ids) == len(surfaces) == len(expected)
    assert dict(zip(ids, surfaces)) == expected


def test_platform_client_renders_surface_specific_flows() -> None:
    text = CLIENT_PATH.read_text(encoding="utf-8")

    assert "const surface = app.surface;" in text
    assert "function renderViewerSurface()" in text
    assert "function renderJobSurface()" in text
    assert "function renderConfiguratorSurface()" in text
    assert "function renderRecordSurface()" in text
    assert "function renderRouteSurface()" in text
    assert "RUNNER_TABS" not in text


def test_surface_reference_document_exists() -> None:
    text = SURFACE_DOC_PATH.read_text(encoding="utf-8")

    assert "App Surface Modes" in text
    assert "Do not reuse one generic tab runner" in text
    assert "viewer3d" in text
