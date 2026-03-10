from __future__ import annotations

from app.core.runtime.language_audit import BACKEND_ROOT, iter_language_findings


def test_backend_language_baseline_stays_english_first() -> None:
    findings = iter_language_findings(backend_root=BACKEND_ROOT)

    assert findings == []
