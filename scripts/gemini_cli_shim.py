#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Tuple
from urllib import error as urllib_error
from urllib import request as urllib_request


ENV_PATHS = (
    Path("/root/stell/webhook/.env"),
    Path("/var/www/stellcodex/backend/.env"),
)
DEFAULT_MODEL = os.getenv("STELL_JUDGE_GEMINI_CLI_MODEL", "gemini-2.5-flash")
SHIM_VERSION = "gemini-cli-shim 0.1.0"


def load_env_key(key: str) -> str:
    for env_path in ENV_PATHS:
        if not env_path.exists():
            continue
        try:
            for raw_line in env_path.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                current_key, value = line.split("=", 1)
                if current_key.strip() != key:
                    continue
                cleaned = value.strip().strip("'").strip('"')
                if cleaned:
                    return cleaned
        except Exception:
            continue
    return ""


def api_key() -> str:
    return (
        os.getenv("GEMINI_API_KEY")
        or os.getenv("GOOGLE_API_KEY")
        or load_env_key("GEMINI_API_KEY")
        or load_env_key("GOOGLE_API_KEY")
    )


def parse_args(argv: list[str]) -> Tuple[str, str, str]:
    prompt = ""
    model = DEFAULT_MODEL
    output_format = "text"
    idx = 0
    while idx < len(argv):
        arg = argv[idx]
        if arg == "--version":
            return "version", "", output_format
        if arg in ("-p", "--prompt"):
            idx += 1
            if idx >= len(argv):
                raise ValueError("prompt degeri eksik")
            prompt = argv[idx]
        elif arg == "--model":
            idx += 1
            if idx >= len(argv):
                raise ValueError("model degeri eksik")
            model = argv[idx].strip() or DEFAULT_MODEL
        elif arg == "--output-format":
            idx += 1
            if idx >= len(argv):
                raise ValueError("output format degeri eksik")
            output_format = argv[idx].strip() or "text"
        elif arg in ("--approval-mode", "--sandbox", "--telemetry-target"):
            idx += 1
            if idx >= len(argv):
                raise ValueError(f"{arg} icin deger eksik")
        elif arg in ("--help", "-h"):
            return "help", "", output_format
        idx += 1
    return model, prompt, output_format


def normalize_model(model: str) -> str:
    cleaned = (model or DEFAULT_MODEL).strip()
    if cleaned.startswith("models/"):
        return cleaned[len("models/") :]
    return cleaned


def render_help() -> str:
    return "\n".join(
        [
            SHIM_VERSION,
            "",
            "Supported subset:",
            "  --version",
            "  -p/--prompt <text>",
            "  --model <model>",
            "  --output-format text|json",
        ]
    )


def generate(prompt: str, model: str, key: str) -> str:
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": "You are a CLI-compatible Gemini shim. Return only the answer."},
                    {"text": prompt},
                ]
            }
        ]
    }
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{normalize_model(model)}:generateContent?key={key}"
    )
    body = json.dumps(payload).encode("utf-8")
    request = urllib_request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib_request.urlopen(request, timeout=30) as response:
        raw = response.read().decode("utf-8")
    data = json.loads(raw)
    return data["candidates"][0]["content"]["parts"][0]["text"]


def main(argv: list[str]) -> int:
    try:
        mode, prompt, output_format = parse_args(argv)
    except ValueError as exc:
        print(f"gemini-cli-shim arg error: {exc}", file=sys.stderr)
        return 2

    if mode == "version":
        print(SHIM_VERSION)
        return 0
    if mode == "help":
        print(render_help())
        return 0

    if not prompt.strip():
        print("gemini-cli-shim prompt eksik", file=sys.stderr)
        return 2

    key = api_key()
    if not key:
        print("gemini-cli-shim API key bulunamadi", file=sys.stderr)
        return 1

    try:
        text = generate(prompt, mode, key).strip()
    except urllib_error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        print(f"gemini-cli-shim HTTP error: {detail}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"gemini-cli-shim error: {exc}", file=sys.stderr)
        return 1

    if output_format == "json":
        print(json.dumps({"text": text}, ensure_ascii=False))
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
