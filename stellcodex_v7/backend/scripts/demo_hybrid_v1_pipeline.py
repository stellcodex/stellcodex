#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from typing import Any
import sys
from pathlib import Path


def _bootstrap_backend_on_path() -> None:
    backend_dir = Path(__file__).resolve().parents[1]
    backend_dir_str = str(backend_dir)
    if backend_dir_str not in sys.path:
        sys.path.insert(0, backend_dir_str)


_bootstrap_backend_on_path()

from app.core.hybrid_v1_rules import run_hybrid_v1_step_pipeline


DEFAULT_STEP_PATH = Path("/var/stellcodex/work/samples/parca.STEP")

def _load_demo_provided_inputs() -> dict[str, Any]:
    """Demo-only explicit inputs. Override via env HYBRID_V1_PROVIDED_JSON."""
    raw = os.environ.get("HYBRID_V1_PROVIDED_JSON", "").strip()
    if raw:
        try:
            obj = json.loads(raw)
            if isinstance(obj, dict):
                return obj
        except Exception:
            pass
    return {
        "wall_mm_min": 1.8,
        "draft_deg_min": 1.0,
        "has_undercut": False,
        "complexity_risk": "medium",
    }



def _resolve_step_path(argv: list[str]) -> Path | None:
    if len(argv) > 1:
        return Path(argv[1])
    if DEFAULT_STEP_PATH.exists():
        return DEFAULT_STEP_PATH
    return None


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run HYBRID V1 demo pipeline on a STEP file. "
            "If STEP_PATH is omitted, default sample path is used when present."
        ),
    )
    parser.add_argument(
        "step_path",
        nargs="?",
        help=f"Path to STEP file (default: {DEFAULT_STEP_PATH})",
    )
    return parser.parse_args(argv[1:])


def main(argv: list[str] | None = None) -> int:
    args = argv or sys.argv
    parsed = _parse_args(args)

    if parsed.step_path:
        step_path = Path(parsed.step_path)
    else:
        step_path = _resolve_step_path(args)

    if step_path is None:
        print(f"SKIP: default STEP not found at {DEFAULT_STEP_PATH}")
        return 0
    provided_inputs = _load_demo_provided_inputs()
    os.environ.setdefault('HYBRID_V1_OVERRIDE_PROVIDED', '1')
    result = run_hybrid_v1_step_pipeline(step_path, provided_inputs=provided_inputs)
    print(json.dumps(result["dfm_findings"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
