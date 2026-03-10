from __future__ import annotations

from app.core.runtime.repo_language_audit import REPO_ROOT


FRONTEND_ROOT = REPO_ROOT / "frontend"
BACKEND_ROOT = REPO_ROOT / "backend"
PUBLIC_LAYOUT_PATH = FRONTEND_ROOT / "app" / "(public)" / "layout.tsx"
PUBLIC_STATUS_PATH = FRONTEND_ROOT / "app" / "(public)" / "status" / "page.tsx"
PUBLIC_COMMUNITY_PATH = FRONTEND_ROOT / "app" / "(public)" / "community" / "page.tsx"
PUBLIC_DOCS_PATH = FRONTEND_ROOT / "app" / "(public)" / "docs" / "page.tsx"
PUBLIC_FEATURES_PATH = FRONTEND_ROOT / "app" / "(public)" / "features" / "page.tsx"
PUBLIC_PRICING_PATH = FRONTEND_ROOT / "app" / "(public)" / "pricing" / "page.tsx"
POLICY_DOC_PATH = BACKEND_ROOT / "docs" / "reference" / "vercel_refresh_policy.md"


def test_public_layout_has_default_revalidate_interval() -> None:
    text = PUBLIC_LAYOUT_PATH.read_text(encoding="utf-8")

    assert "export const revalidate = 1800;" in text
    assert "refresh on a calm interval" in text


def test_public_high_change_pages_have_faster_intervals() -> None:
    status_text = PUBLIC_STATUS_PATH.read_text(encoding="utf-8")
    community_text = PUBLIC_COMMUNITY_PATH.read_text(encoding="utf-8")
    docs_text = PUBLIC_DOCS_PATH.read_text(encoding="utf-8")

    assert "export const revalidate = 300;" in status_text
    assert "export const revalidate = 900;" in community_text
    assert "export const revalidate = 1800;" in docs_text


def test_public_suite_copy_stays_aligned() -> None:
    features_text = PUBLIC_FEATURES_PATH.read_text(encoding="utf-8")
    pricing_text = PUBLIC_PRICING_PATH.read_text(encoding="utf-8")

    assert "One suite, focused applications" in features_text
    assert "Free" in pricing_text
    assert "Plus" in pricing_text
    assert "Pro" in pricing_text
    assert "Coming soon" not in pricing_text


def test_vercel_refresh_policy_document_exists() -> None:
    text = POLICY_DOC_PATH.read_text(encoding="utf-8")

    assert "default public interval: 1800 seconds" in text
    assert "faster public status interval: 300 seconds" in text
    assert "community feed interval: 900 seconds" in text
