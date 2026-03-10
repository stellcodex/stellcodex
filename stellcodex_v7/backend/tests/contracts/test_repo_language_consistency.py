from __future__ import annotations

from app.core.runtime.repo_language_audit import REPO_ROOT, iter_repo_language_findings


def test_repository_language_baseline_stays_english_first() -> None:
    findings = iter_repo_language_findings(repo_root=REPO_ROOT)

    assert findings == []
