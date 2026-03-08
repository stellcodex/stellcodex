from __future__ import annotations

import re
from typing import Any

from app.knowledge.hash_utils import make_chunk_hash, make_id
from app.knowledge.schemas import ChunkRecord, MemoryRecord


TOKEN_RE = re.compile(r"[a-zA-Z0-9_]+")
DEFAULT_TARGET_TOKENS = 800
DEFAULT_OVERLAP_TOKENS = 100
DEFAULT_MAX_CHARS = 6000


def estimate_tokens(text: str) -> int:
    return len(TOKEN_RE.findall(str(text or "")))


def _split_markdown_sections(text: str) -> list[str]:
    lines = text.splitlines()
    out: list[str] = []
    current: list[str] = []
    for line in lines:
        if line.lstrip().startswith("#") and current:
            out.append("\n".join(current).strip())
            current = [line]
        else:
            current.append(line)
    if current:
        out.append("\n".join(current).strip())
    return [item for item in out if item.strip()]


def _split_json_blocks(text: str) -> list[str]:
    compact = str(text or "").strip()
    if not compact:
        return []
    lines = [line for line in compact.splitlines() if line.strip()]
    blocks: list[str] = []
    current: list[str] = []
    depth = 0
    for line in lines:
        current.append(line)
        depth += line.count("{") + line.count("[")
        depth -= line.count("}") + line.count("]")
        if depth <= 0 and current:
            blocks.append("\n".join(current).strip())
            current = []
            depth = 0
    if current:
        blocks.append("\n".join(current).strip())
    return [item for item in blocks if item]


def _split_log_blocks(text: str, lines_per_block: int = 40) -> list[str]:
    lines = [line for line in text.splitlines() if line.strip()]
    out: list[str] = []
    for i in range(0, len(lines), max(1, int(lines_per_block))):
        block = "\n".join(lines[i : i + lines_per_block]).strip()
        if block:
            out.append(block)
    return out


def _token_window_chunks(
    text: str,
    *,
    target_tokens: int,
    overlap_tokens: int,
    hard_max_chars: int,
) -> list[str]:
    tokens = TOKEN_RE.findall(str(text or ""))
    if not tokens:
        return []
    if len(tokens) <= target_tokens:
        compact = str(text or "").strip()
        return [compact[:hard_max_chars]] if compact else []

    overlap = min(max(0, overlap_tokens), max(0, target_tokens - 1))
    step = max(1, target_tokens - overlap)
    chunks: list[str] = []
    for start in range(0, len(tokens), step):
        window = tokens[start : start + target_tokens]
        if not window:
            continue
        chunk = " ".join(window).strip()
        if not chunk:
            continue
        chunks.append(chunk[:hard_max_chars])
        if start + target_tokens >= len(tokens):
            break
    return chunks


def chunk_memory_record(
    record: MemoryRecord,
    *,
    chunk_strategy: str,
    target_chunk_size: int = DEFAULT_TARGET_TOKENS,
    overlap: int = DEFAULT_OVERLAP_TOKENS,
    hard_max_chars: int = DEFAULT_MAX_CHARS,
    min_token_threshold: int = 8,
) -> list[ChunkRecord]:
    record.validate()
    strategy = str(chunk_strategy or "default").strip().lower()
    text = str(record.text or "").strip()
    if not text:
        return []

    if strategy == "heading_aware":
        blocks = _split_markdown_sections(text)
    elif strategy == "json_block":
        blocks = _split_json_blocks(text)
    elif strategy == "log_block":
        blocks = _split_log_blocks(text)
    else:
        blocks = [text]
    if not blocks:
        blocks = [text]

    chunk_payloads: list[str] = []
    for block in blocks:
        chunk_payloads.extend(
            _token_window_chunks(
                block,
                target_tokens=max(64, int(target_chunk_size)),
                overlap_tokens=max(0, int(overlap)),
                hard_max_chars=max(800, int(hard_max_chars)),
            )
        )

    dedupe_hashes: set[str] = set()
    out: list[ChunkRecord] = []
    for idx, chunk_text in enumerate(chunk_payloads):
        token_est = estimate_tokens(chunk_text)
        if token_est < max(1, int(min_token_threshold)):
            continue
        chunk_hash = make_chunk_hash(record.record_id, idx, chunk_text)
        if chunk_hash in dedupe_hashes:
            continue
        dedupe_hashes.add(chunk_hash)
        chunk_id = make_id("ch", record.record_id, idx, chunk_hash, size=40)
        chunk = ChunkRecord(
            chunk_id=chunk_id,
            record_id=record.record_id,
            chunk_index=len(out),
            text=chunk_text,
            token_estimate=token_est,
            metadata={
                "chunk_hash": chunk_hash,
                "chunk_policy": {
                    "strategy": strategy,
                    "target_chunk_size": int(target_chunk_size),
                    "overlap": int(overlap),
                    "hard_max_chars": int(hard_max_chars),
                },
                "record_type": record.record_type,
                "source_uri": record.source_uri,
            },
        )
        chunk.validate()
        out.append(chunk)
    return out


def chunk_order_is_valid(chunks: list[ChunkRecord]) -> bool:
    for idx, chunk in enumerate(chunks):
        if int(chunk.chunk_index) != idx:
            return False
    return True
