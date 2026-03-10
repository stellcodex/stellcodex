#!/usr/bin/env python3
"""Audit the full repository for unexpected mixed-language drift."""

from __future__ import annotations

import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.runtime.repo_language_audit import REPO_ROOT, iter_repo_language_findings


def main() -> int:
    findings = iter_repo_language_findings(repo_root=REPO_ROOT)
    payload = {
        "repo_root": str(REPO_ROOT),
        "finding_count": len(findings),
        "findings": findings,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
