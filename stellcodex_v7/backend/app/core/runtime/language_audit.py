"""Language consistency audit helpers.

The backend implementation stays English-first, while a small allowlist of
files may intentionally include multilingual keyword hints for request routing.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable


BACKEND_ROOT = Path(__file__).resolve().parents[3]
SCAN_ROOTS = ("app", "docs", "tests", "scripts", "alembic", "../infrastructure")
ALLOWED_MULTILINGUAL_FILES = {
    "app/core/runtime/message_mode.py": "multilingual message classification keywords",
    "app/core/runtime/repo_language_audit.py": "repo language audit keyword patterns",
    "app/stellai/agents.py": "multilingual tool inference keywords",
    "app/stellai/channel_runtime.py": "multilingual async routing keywords",
}
TURKISH_CHAR_PATTERN = re.compile("[\u00c7\u00d6\u00dc\u011e\u0130\u015e\u00e7\u00f6\u00fc\u011f\u0131\u015f]")


def iter_language_findings(*, backend_root: Path | None = None, scan_roots: Iterable[str] | None = None) -> list[dict[str, str | int]]:
    root = backend_root or BACKEND_ROOT
    roots = tuple(scan_roots or SCAN_ROOTS)
    findings: list[dict[str, str | int]] = []

    for relative_root in roots:
        scan_root = root / relative_root
        if not scan_root.exists():
            continue
        for path in sorted(scan_root.rglob("*")):
            if not path.is_file():
                continue
            rel_path = path.relative_to(root).as_posix()
            if rel_path in ALLOWED_MULTILINGUAL_FILES:
                continue
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except UnicodeDecodeError:
                continue
            for index, line in enumerate(lines, start=1):
                if TURKISH_CHAR_PATTERN.search(line):
                    findings.append(
                        {
                            "path": rel_path,
                            "line": index,
                            "text": line.strip(),
                        }
                    )
    return findings
