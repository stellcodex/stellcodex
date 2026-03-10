from __future__ import annotations

from app.core.runtime.repo_language_audit import REPO_ROOT


FRONTEND_ROOT = REPO_ROOT / "frontend"
LAYOUT_PATH = FRONTEND_ROOT / "app" / "layout.tsx"
LOGIN_PATH = FRONTEND_ROOT / "app" / "(public)" / "login" / "page.tsx"
REGISTER_PATH = FRONTEND_ROOT / "app" / "(public)" / "register" / "page.tsx"
FORGOT_PATH = FRONTEND_ROOT / "app" / "(public)" / "forgot" / "page.tsx"
RESET_PATH = FRONTEND_ROOT / "app" / "(public)" / "reset" / "page.tsx"
CONSOLE_PATH = FRONTEND_ROOT / "app" / "console" / "page.tsx"
PLATFORM_LAYOUT_PATH = FRONTEND_ROOT / "components" / "platform" / "PlatformLayout.tsx"
VISUAL_DOC_PATH = REPO_ROOT / "backend" / "docs" / "reference" / "suite_visual_language.md"
DEPLOY_BRIDGE_DOC_PATH = REPO_ROOT / "backend" / "docs" / "reference" / "frontend_deploy_bridge.md"


def test_root_layout_forces_light_theme() -> None:
    text = LAYOUT_PATH.read_text(encoding="utf-8")

    assert 'const resolvedTheme = "light";' in text
    assert "d.dataset.theme='light'" in text
    assert "d.dataset.themeResolved='light'" in text


def test_auth_pages_use_shared_shell_and_drop_console_branding() -> None:
    for path in [LOGIN_PATH, REGISTER_PATH, FORGOT_PATH, RESET_PATH]:
        text = path.read_text(encoding="utf-8")
        assert "AuthShell" in text
        assert "STELLCONSOLE" not in text
        assert "bg-[#1a1a1a]" not in text


def test_login_no_longer_redirects_into_legacy_console() -> None:
    text = LOGIN_PATH.read_text(encoding="utf-8")
    assert 'router.push("/")' in text
    assert "/console" not in text


def test_console_route_redirects_back_into_workspace() -> None:
    text = CONSOLE_PATH.read_text(encoding="utf-8")
    assert "WorkspaceRedirect" in text
    assert "STELLCONSOLE" not in text


def test_platform_layout_has_one_settings_entry_in_user_menu() -> None:
    text = PLATFORM_LAYOUT_PATH.read_text(encoding="utf-8")
    assert text.count('resolveWorkspaceHref(workspaceId, "/settings")') == 1
    assert "Plan access" in text
    assert ">Plans<" not in text


def test_visual_language_and_deploy_bridge_docs_exist() -> None:
    visual_text = VISUAL_DOC_PATH.read_text(encoding="utf-8")
    bridge_text = DEPLOY_BRIDGE_DOC_PATH.read_text(encoding="utf-8")

    assert "Locked baseline" in visual_text
    assert "teal (`#0f766e`)" in visual_text
    assert "/var/www/stellcodex/frontend/src" in bridge_text
    assert "pm2" in bridge_text
