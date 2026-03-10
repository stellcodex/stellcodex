"""Repository-wide language audit helpers.

The implementation layer stays English-first. A very small allowlist may
contain multilingual keyword matching or dedicated localized content pages.
"""

from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
SCAN_ROOTS = ("backend", "frontend", "infrastructure")
SKIP_PARTS = {
    ".git",
    ".next",
    "node_modules",
    ".venv",
    ".venv-engineering",
    "__pycache__",
}
ALLOWED_MULTILINGUAL_FILES = {
    "backend/app/core/runtime/message_mode.py": "multilingual message classification keywords",
    "backend/app/core/runtime/repo_language_audit.py": "repo language audit keyword patterns",
    "backend/app/stellai/agents.py": "multilingual tool inference keywords",
    "backend/app/stellai/channel_runtime.py": "multilingual async routing keywords",
    "frontend/components/ChatShell.tsx": "bilingual quick-start intent matching",
    "frontend/components/viewer/DxfViewer.tsx": "legacy Turkish pending-state compatibility detection",
    "frontend/app/(viewer)/view/[scx_id]/page.tsx": "legacy Turkish transport error compatibility detection",
    "frontend/content/privacy.tr.md": "dedicated Turkish privacy content",
    "frontend/content/terms.tr.md": "dedicated Turkish terms content",
}
TURKISH_CHAR_PATTERN = re.compile(r"[\u00c7\u00d6\u00dc\u011e\u0130\u015e\u00e7\u00f6\u00fc\u011f\u0131\u015f]")
ASCII_TURKISH_PATTERN = re.compile(
    r"\b(?:"
    r"yukleme|yuklen(?:emedi|iyor|mis|en)?|"
    r"olustur(?:uldu|uluyor|ulamad[ıi])?|"
    r"hazir(?:landi|laniyor|lanmadi)|"
    r"basarisiz|"
    r"dosya|"
    r"proje|"
    r"kayit(?:lar)?|"
    r"guncellen(?:iyor|di)|"
    r"kopyala|"
    r"kapat|"
    r"gizlilik|"
    r"kosullari|"
    r"calisma|"
    r"erisim|"
    r"kutuphane|"
    r"paylas|"
    r"yuzey|"
    r"ozellik"
    r")\b",
    re.IGNORECASE,
)


def _should_skip(path: Path) -> bool:
    return any(part in SKIP_PARTS for part in path.parts)


def iter_repo_language_findings(*, repo_root: Path | None = None) -> list[dict[str, str | int]]:
    root = repo_root or REPO_ROOT
    findings: list[dict[str, str | int]] = []

    for relative_root in SCAN_ROOTS:
        scan_root = root / relative_root
        if not scan_root.exists():
            continue
        for path in sorted(scan_root.rglob("*")):
            if _should_skip(path) or not path.is_file():
                continue
            rel_path = path.relative_to(root).as_posix()
            if rel_path in ALLOWED_MULTILINGUAL_FILES:
                continue
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except UnicodeDecodeError:
                continue
            for index, line in enumerate(lines, start=1):
                if TURKISH_CHAR_PATTERN.search(line) or ASCII_TURKISH_PATTERN.search(line):
                    findings.append(
                        {
                            "path": rel_path,
                            "line": index,
                            "text": line.strip(),
                        }
                    )
    return findings
