from __future__ import annotations

from app.core.runtime.repo_language_audit import REPO_ROOT


FRONTEND_ROOT = REPO_ROOT / "frontend"
ROOT_PAGE_PATH = FRONTEND_ROOT / "app" / "page.tsx"
APPS_PAGE_PATH = FRONTEND_ROOT / "app" / "apps" / "page.tsx"
APP_RUNNER_PAGE_PATH = FRONTEND_ROOT / "app" / "app" / "[appId]" / "page.tsx"
WORKSPACE_ROUTE_PATH = FRONTEND_ROOT / "app" / "workspace" / "[workspaceId]" / "[[...slug]]" / "page.tsx"
PUBLIC_HOME_PATH = FRONTEND_ROOT / "app" / "(public)" / "home" / "page.tsx"
CLIENT_PATH = FRONTEND_ROOT / "components" / "platform" / "PlatformClient.tsx"


def _function_block(text: str, function_name: str, next_function_name: str) -> str:
    start = text.index(f"function {function_name}(")
    end = text.index(f"function {next_function_name}(", start)
    return text[start:end]


def test_root_entry_is_canonical_workspace_redirect() -> None:
    root_text = ROOT_PAGE_PATH.read_text(encoding="utf-8")
    apps_text = APPS_PAGE_PATH.read_text(encoding="utf-8")
    app_runner_text = APP_RUNNER_PAGE_PATH.read_text(encoding="utf-8")

    assert "WorkspaceRedirect" in root_text
    assert "WorkspaceRedirect" in apps_text
    assert 'suffix="/apps"' in apps_text
    assert "WorkspaceRedirect" in app_runner_text
    assert "preserveSearch" in app_runner_text


def test_workspace_route_dispatch_stays_small_and_canonical() -> None:
    route_text = WORKSPACE_ROUTE_PATH.read_text(encoding="utf-8")

    assert 'if (!section) return <PlatformClient view="home" />;' in route_text
    assert 'if (section === "apps") return <PlatformClient view="apps" />;' in route_text
    assert 'if (section === "files") return <PlatformClient view="files" />;' in route_text
    assert 'if (section === "library") return <PlatformClient view="library" />;' in route_text
    assert 'if (section === "settings") return <PlatformClient view="settings" />;' in route_text
    assert 'if (section === "admin") return <PlatformClient view="admin" />;' in route_text
    assert 'if (section === "open" && resourceId)' in route_text


def test_public_home_does_not_duplicate_suite_entry_copy() -> None:
    public_text = PUBLIC_HOME_PATH.read_text(encoding="utf-8")

    assert "STELLCODEX Suite" not in public_text
    assert "Simple in front. Specialized underneath." not in public_text
    assert "Upload once. Open the right app automatically." not in public_text


def test_home_surface_primary_actions_are_unique() -> None:
    client_text = CLIENT_PATH.read_text(encoding="utf-8")
    home_block = _function_block(client_text, "HomeScreen", "AppsCatalogScreen")

    assert home_block.count("Select file") == 1
    assert home_block.count("Open Files and Share") == 1
    assert home_block.count("Browse all applications") == 1
    assert home_block.count("No cloned entry pages") == 1


def test_suite_home_keeps_no_chat_wall_or_send_button() -> None:
    client_text = CLIENT_PATH.read_text(encoding="utf-8")
    home_block = _function_block(client_text, "HomeScreen", "AppsCatalogScreen")

    assert "Send" not in home_block
    assert "textarea" not in home_block
    assert "What can STELLCODEX help build today?" not in home_block
    assert "appendSessionMessage" not in home_block
