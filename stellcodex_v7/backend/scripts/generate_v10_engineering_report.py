#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from app.core.autonomous_engineering.stability_report import write_v10_engineering_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate STELLCODEX V10 engineering stability report.")
    parser.add_argument("--output", required=True, help="Primary JSON output path.")
    parser.add_argument("--mirror", action="append", default=[], help="Additional output paths.")
    parser.add_argument("--system-health", default="ok")
    parser.add_argument("--tests-passed", type=int, default=0)
    parser.add_argument("--tests-total", type=int, default=0)
    parser.add_argument("--gate-status", default="pending")
    parser.add_argument("--evidence-artifact", action="append", default=[])
    parser.add_argument("--degraded-feature", action="append", default=[])
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = write_v10_engineering_report(
        output_path=args.output,
        system_health=args.system_health,
        tests_passed=args.tests_passed,
        tests_total=args.tests_total,
        gate_status=args.gate_status,
        evidence_artifacts=args.evidence_artifact,
        degraded_features=args.degraded_feature,
    )
    for mirror in args.mirror:
        write_v10_engineering_report(
            output_path=mirror,
            system_health=args.system_health,
            tests_passed=args.tests_passed,
            tests_total=args.tests_total,
            gate_status=args.gate_status,
            evidence_artifacts=args.evidence_artifact,
            degraded_features=args.degraded_feature,
        )
    print(Path(args.output))
    return 0 if payload["test_coverage"]["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
