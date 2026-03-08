from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MAX_PARSE_BYTES = 2_000_000
WORKSPACE_ROOT = Path("/root/workspace").resolve()

_SECRET_PATTERNS = (
    re.compile(r"(?i)(password|passwd|secret|token|api[_-]?key)\s*[:=]\s*([^\s,;]+)"),
    re.compile(r"(?i)(authorization\s*:\s*bearer\s+)([a-z0-9._-]+)"),
    re.compile(r"\bsk-[a-zA-Z0-9]{10,}\b"),
)


@dataclass(frozen=True)
class ParseResult:
    title: str
    text: str
    metadata: dict[str, Any]
    tags: list[str]
    time_start: str | None
    time_end: str | None


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def mask_secrets(text: str) -> str:
    out = str(text or "")
    for pattern in _SECRET_PATTERNS:
        out = pattern.sub(lambda m: f"{m.group(1)}=[REDACTED]" if m.lastindex and m.lastindex >= 2 else "[REDACTED]", out)
    return out


def _validate_local_path(raw_path: str) -> Path:
    candidate = Path(raw_path)
    if not candidate.is_absolute():
        candidate = (WORKSPACE_ROOT / candidate).resolve()
    else:
        candidate = candidate.resolve()
    try:
        candidate.relative_to(WORKSPACE_ROOT)
    except Exception as exc:
        raise ValueError("source_uri outside allowed workspace root") from exc
    if not candidate.exists() or not candidate.is_file():
        raise FileNotFoundError(f"source_uri not found: {candidate}")
    return candidate


def _read_bounded(path: Path, max_bytes: int = MAX_PARSE_BYTES) -> str:
    data = path.read_bytes()[: max(1024, int(max_bytes))]
    return data.decode("utf-8", errors="ignore")


def _parse_md_or_txt(*, source_uri: str, raw_text: str) -> ParseResult:
    lines = raw_text.splitlines()
    title = Path(source_uri).name
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            title = stripped.lstrip("#").strip() or title
            break
    text = mask_secrets(raw_text)
    return ParseResult(
        title=title,
        text=text,
        metadata={"source_type": "text", "parser": "markdown_parser", "ingestion_version": "v1"},
        tags=["text", "markdown" if source_uri.endswith(".md") else "plain_text"],
        time_start=None,
        time_end=None,
    )


def _parse_json(*, source_uri: str, raw_text: str) -> ParseResult:
    payload = json.loads(raw_text) if raw_text.strip() else {}
    if not isinstance(payload, (dict, list)):
        payload = {"value": payload}
    text = mask_secrets(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2))
    return ParseResult(
        title=Path(source_uri).name,
        text=text,
        metadata={"source_type": "json", "parser": "json_parser", "ingestion_version": "v1"},
        tags=["json"],
        time_start=None,
        time_end=None,
    )


def _parse_log(*, source_uri: str, raw_text: str) -> ParseResult:
    lines = [mask_secrets(line.rstrip()) for line in raw_text.splitlines() if line.strip()]
    time_start = None
    time_end = None
    if lines:
        time_start = lines[0][:32]
        time_end = lines[-1][:32]
    return ParseResult(
        title=Path(source_uri).name,
        text="\n".join(lines),
        metadata={"source_type": "log", "parser": "log_parser", "ingestion_version": "v1"},
        tags=["log"],
        time_start=time_start,
        time_end=time_end,
    )


def _parse_csv(*, source_uri: str, raw_text: str) -> ParseResult:
    lines = [line for line in raw_text.splitlines() if line.strip()]
    header = lines[0] if lines else ""
    sample = lines[1:21]
    text = mask_secrets("\n".join([header, *sample]))
    return ParseResult(
        title=Path(source_uri).name,
        text=text,
        metadata={"source_type": "csv", "parser": "csv_parser", "ingestion_version": "v1"},
        tags=["csv"],
        time_start=None,
        time_end=None,
    )


def parse_source(
    *,
    source_uri: str,
    source_type: str,
    max_bytes: int = MAX_PARSE_BYTES,
    inline_text: str | None = None,
) -> ParseResult:
    _ = source_type
    uri = str(source_uri or "").strip()
    if not uri:
        raise ValueError("source_uri is required")

    if uri.startswith("inline://"):
        text = mask_secrets(str(inline_text or ""))
        if not text.strip():
            raise ValueError("inline source is empty")
        return ParseResult(
            title=uri.replace("inline://", "", 1) or "inline_source",
            text=text,
            metadata={"source_type": "inline", "parser": "inline_parser", "ingestion_version": "v1"},
            tags=["inline"],
            time_start=_now_iso(),
            time_end=_now_iso(),
        )

    path = _validate_local_path(uri)
    lower = path.name.lower()
    raw_text = _read_bounded(path, max_bytes=max_bytes)
    if lower.endswith(".md") or lower.endswith(".txt"):
        return _parse_md_or_txt(source_uri=str(path), raw_text=raw_text)
    if lower.endswith(".json"):
        return _parse_json(source_uri=str(path), raw_text=raw_text)
    if lower.endswith(".log"):
        return _parse_log(source_uri=str(path), raw_text=raw_text)
    if lower.endswith(".csv"):
        return _parse_csv(source_uri=str(path), raw_text=raw_text)
    if lower.endswith(".pdf"):
        # Optional path; safe fallback with no OCR.
        text = mask_secrets(raw_text)
        return ParseResult(
            title=path.name,
            text=text,
            metadata={"source_type": "pdf", "parser": "pdf_text_fallback", "ingestion_version": "v1"},
            tags=["pdf"],
            time_start=None,
            time_end=None,
        )
    raise ValueError(f"unsupported input extension: {path.suffix}")
