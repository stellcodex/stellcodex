from __future__ import annotations

import json

from app.core.runtime.repo_language_audit import REPO_ROOT


FRONTEND_ROOT = REPO_ROOT / "frontend"
BACKEND_ROOT = REPO_ROOT / "backend"
MARKETPLACE_PATH = REPO_ROOT / "marketplace" / "catalog.json"
WORKSPACE_ROUTE_PATH = FRONTEND_ROOT / "app" / "workspace" / "[workspaceId]" / "[[...slug]]" / "page.tsx"
APPS_PAGE_PATH = FRONTEND_ROOT / "app" / "apps" / "page.tsx"
APP_MODULE_PAGE_PATH = FRONTEND_ROOT / "app" / "apps" / "[slug]" / "page.tsx"
PLATFORM_MARKETPLACE_PATH = FRONTEND_ROOT / "data" / "platformMarketplace.ts"
INVENTORY_DOC_PATH = BACKEND_ROOT / "docs" / "reference" / "platform_app_inventory.md"
APPS_ROUTE_PATH = BACKEND_ROOT / "app" / "api" / "v1" / "routes" / "apps.py"


def test_marketplace_catalog_has_expected_inventory_shape() -> None:
    rows = json.loads(MARKETPLACE_PATH.read_text(encoding="utf-8"))

    assert isinstance(rows, list)
    assert len(rows) == 45

    slugs = [row["slug"] for row in rows]
    assert len(slugs) == len(set(slugs))

    for slug in slugs:
        manifest_path = BACKEND_ROOT / "apps" / slug / "app.manifest.json"
        assert manifest_path.exists(), f"missing manifest for {slug}"


def test_workspace_shell_handles_applications_catalog_route() -> None:
    text = WORKSPACE_ROUTE_PATH.read_text(encoding="utf-8")

    assert 'if (section === "apps") return <PlatformClient view="apps" />;' in text


def test_root_apps_routes_redirect_into_workspace_shell() -> None:
    apps_page = APPS_PAGE_PATH.read_text(encoding="utf-8")
    app_module_page = APP_MODULE_PAGE_PATH.read_text(encoding="utf-8")

    assert "WorkspaceRedirect" in apps_page
    assert 'suffix="/apps"' in apps_page
    assert "WorkspaceRedirect" in app_module_page
    assert "suffix={`/app/${slug}`}" in app_module_page


def test_marketplace_integration_rules_and_docs_exist() -> None:
    helper = PLATFORM_MARKETPLACE_PATH.read_text(encoding="utf-8")
    doc = INVENTORY_DOC_PATH.read_text(encoding="utf-8")
    route = APPS_ROUTE_PATH.read_text(encoding="utf-8")

    assert "const CORE_APP_ALIASES" in helper
    assert "stellview" in helper
    assert "stellai" in doc
    assert "45 application modules" in doc
    assert "include_disabled: bool = Query(default=False)" in route
