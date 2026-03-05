#!/usr/bin/env python3
import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple
from urllib.parse import urlparse

from progress_checkpoint import write_checkpoint


WORKSPACE = Path("/root/workspace")
RUNS_DIR = WORKSPACE / "_runs" / "pipeline_doctor"
HANDOFF_DIR = WORKSPACE / "handoff"
HANDOFF_PATH = HANDOFF_DIR / "pipeline-doctor-status.md"

DEFAULT_PROJECT_ROOT = Path("/var/www/stellcodex")


def utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def compact_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def ensure_dirs() -> None:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    HANDOFF_DIR.mkdir(parents=True, exist_ok=True)


def slugify(value: str, limit: int = 48) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return (cleaned or "repair")[:limit].strip("-") or "repair"


def analyze_failure(output: str) -> str:
    text = output.lower()
    if "no health endpoint returned http 200" in text:
        return "Health endpoint discovery failed; backend or proxy path is unavailable."
    if "openapi reachable" in text and "fail" in text:
        return "OpenAPI endpoint check failed; backend routing or app boot may be broken."
    if "forbidden token leak detected" in text:
        return "Public contract or schema files contain forbidden storage tokens."
    if "contract leak scan failed to execute" in text:
        return "Forbidden token scan did not complete; inspect rg availability or target paths."
    if "curl:" in text:
        return "HTTP probe failed; inspect base URL reachability and service health."
    if "permission denied" in text:
        return "Command permissions blocked execution."
    if "not found" in text:
        return "A required executable or script path is missing."
    return "No heuristic root cause matched; inspect captured stdout/stderr."


def run_step(name: str, cmd: List[str], env: Dict[str, str], cwd: str) -> Dict[str, object]:
    started = time.time()
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env, cwd=cwd)
    duration = round(time.time() - started, 2)
    combined = "\n".join(part for part in (proc.stdout.strip(), proc.stderr.strip()) if part).strip()
    status = "PASS" if proc.returncode == 0 else "FAIL"
    return {
        "name": name,
        "command": cmd,
        "status": status,
        "exit_code": proc.returncode,
        "duration_seconds": duration,
        "started_at": utc_iso(),
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "root_cause_hint": "" if status == "PASS" else analyze_failure(combined),
    }


def run_text_command(cmd: List[str], cwd: str = str(DEFAULT_PROJECT_ROOT), timeout: int = 10) -> Tuple[int, str, str]:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, timeout=timeout)
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except Exception as exc:
        return 1, "", str(exc)


def probe_base_url(base_url: str) -> Dict[str, object]:
    target = base_url.rstrip("/") + "/"
    rc, stdout, stderr = run_text_command(
        [
            "curl",
            "-sS",
            "-o",
            "/dev/null",
            "-w",
            "%{http_code}",
            "--max-time",
            "5",
            target,
        ],
        timeout=10,
    )
    http_code = stdout.strip() if stdout.strip() else "000"
    return {
        "target": target,
        "curl_return_code": rc,
        "http_code": http_code,
        "reachable": http_code != "000",
        "stderr": stderr,
    }


def build_failure_analysis(report: Dict[str, object]) -> Dict[str, object]:
    failed = [step for step in report["steps"] if step["status"] != "PASS"]
    hints = [str(step.get("root_cause_hint", "")) for step in failed]
    hint_text = " ".join(hints).lower()
    base_probe = probe_base_url(str(report.get("base_url", "http://127.0.0.1:8000")))
    parsed = urlparse(str(report.get("base_url", "")))

    analysis = {
        "classification": "code_actionable",
        "execution_policy": "provider_patch_allowed",
        "reason": "At least one failing step may be repairable by changing repository code or scripts.",
        "base_probe": base_probe,
        "recommended_actions": [
            "Run the isolated repair runner against the generated bundle.",
            "Verify smoke and contract checks after the patch.",
        ],
    }

    if failed and all("health endpoint discovery failed" in hint.lower() for hint in hints):
        if not bool(base_probe["reachable"]):
            analysis = {
                "classification": "env_only",
                "execution_policy": "skip_provider_patch",
                "reason": "The configured base URL is not reachable, so a repo patch is unlikely to fix the failure.",
                "base_probe": base_probe,
                "recommended_actions": [
                    "Verify BASE_URL/BACKEND_BASE_URL and target port for the failing environment.",
                    "Check runtime health before generating a code patch.",
                    "Rerun Pipeline Doctor with a reachable base URL after service recovery.",
                ],
            }
        else:
            analysis["reason"] = "The runtime is reachable but health discovery failed; investigate health route and smoke script behavior."
            analysis["recommended_actions"] = [
                "Inspect health route wiring and smoke path candidates.",
                "Run the isolated repair runner because a code or script fix may be needed.",
            ]
    elif "forbidden token leak detected" in hint_text:
        analysis["reason"] = "Public contract assets contain forbidden token patterns and require a repository patch."
        analysis["recommended_actions"] = [
            "Patch public docs/schema files to remove forbidden token patterns.",
            "Rerun the leak scan and contract matrix after the patch.",
        ]
    elif "openapi endpoint check failed" in hint_text:
        if not bool(base_probe["reachable"]):
            analysis = {
                "classification": "env_only",
                "execution_policy": "skip_provider_patch",
                "reason": "OpenAPI probe failed because the configured runtime is not reachable.",
                "base_probe": base_probe,
                "recommended_actions": [
                    "Restore runtime reachability for the configured base URL.",
                    "Rerun Pipeline Doctor before attempting a repo patch.",
                ],
            }
        else:
            analysis["reason"] = "Runtime is reachable but OpenAPI is failing; backend routing or app boot may require a repo patch."
            analysis["recommended_actions"] = [
                "Inspect API router and app bootstrap paths.",
                "Run the isolated repair runner because a code patch is likely needed.",
            ]

    if parsed.scheme and parsed.hostname:
        analysis["base_url_host"] = parsed.hostname
        analysis["base_url_port"] = parsed.port
    return analysis


def collect_git_context(project_root: Path) -> Dict[str, object]:
    branch_rc, branch_out, branch_err = run_text_command(
        ["git", "-C", str(project_root), "rev-parse", "--abbrev-ref", "HEAD"]
    )
    head_rc, head_out, head_err = run_text_command(
        ["git", "-C", str(project_root), "rev-parse", "--short", "HEAD"]
    )
    status_rc, status_out, status_err = run_text_command(
        ["git", "-C", str(project_root), "status", "--short", "--branch"]
    )
    return {
        "project_root": str(project_root),
        "branch": branch_out if branch_rc == 0 else "",
        "head": head_out if head_rc == 0 else "",
        "status": status_out if status_rc == 0 else "",
        "errors": [item for item in (branch_err, head_err, status_err) if item],
    }


def infer_candidate_files(step: Dict[str, object]) -> List[str]:
    combined = "%s\n%s" % (step.get("stdout", ""), step.get("stderr", ""))
    text = combined.lower()
    files: List[str] = []

    if step["name"] == "smoke_test":
        files.extend(
            [
                "scripts/smoke_test.sh",
                "backend/app/api/v1/routes/health.py",
                "infrastructure/deploy/docker-compose.yml",
            ]
        )
    if step["name"] == "contract_matrix":
        files.extend(
            [
                "ci/contract_matrix.sh",
                "scripts/smoke_test.sh",
                "scripts/release_gate.sh",
            ]
        )
    if "openapi" in text:
        files.extend(["backend/app/main.py", "backend/app/api/v1/api.py"])
    if "no such file or directory" in text:
        files.extend(["ci/contract_matrix.sh", "scripts/smoke_test.sh"])
    if "forbidden token" in text:
        files.extend(["docs/contracts/", "schemas/", "scripts/leak_scan_repo.sh"])

    ordered = []
    seen = set()
    for item in files:
        if item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


def build_repair_metadata(
    report: Dict[str, object], git_context: Dict[str, object], failure_analysis: Dict[str, object]
) -> Dict[str, object]:
    failed = [step for step in report["steps"] if step["status"] != "PASS"]
    first = failed[0] if failed else None
    problem = first["root_cause_hint"] if first else "pipeline checks"
    branch_slug = slugify("%s-%s" % (first["name"] if first else "pipeline", problem))
    suggested_branch = "doctor/%s-%s" % (compact_stamp(), branch_slug)
    is_code_actionable = failure_analysis.get("execution_policy") == "provider_patch_allowed"
    pr_title = (
        "fix: repair %s failure" % (first["name"] if first else "pipeline")
        if is_code_actionable
        else "chore: record %s pipeline incident" % (first["name"] if first else "pipeline")
    )
    pr_body = [
        "## Summary",
        "- %s" % (
            "Repair failing Pipeline Doctor step."
            if is_code_actionable
            else "Record env/runtime incident; no automatic repo patch should be attempted."
        ),
        "- Preserve passing checks and avoid unrelated mutations.",
        "",
        "## Failure",
        report["summary"],
        "",
        "## Failure Analysis",
        "- Classification: %s" % failure_analysis["classification"],
        "- Execution policy: %s" % failure_analysis["execution_policy"],
        "- Reason: %s" % failure_analysis["reason"],
        "",
        "## Evidence",
        "- Report: %s" % report["report_path"],
        "- Base branch: %s" % (git_context.get("branch") or "unknown"),
        "- Base commit: %s" % (git_context.get("head") or "unknown"),
    ]
    if failure_analysis.get("recommended_actions"):
        pr_body.extend(["", "## Recommended Actions"])
        for action in failure_analysis["recommended_actions"]:
            pr_body.append("- %s" % action)
    return {
        "suggested_branch": suggested_branch,
        "commit_message": pr_title,
        "pr_title": pr_title,
        "pr_body": "\n".join(pr_body),
        "candidate_files": infer_candidate_files(first) if first and is_code_actionable else [],
        "classification": failure_analysis["classification"],
        "execution_policy": failure_analysis["execution_policy"],
        "recommended_actions": failure_analysis["recommended_actions"],
    }


def build_repair_prompt(
    report: Dict[str, object], repair: Dict[str, object], git_context: Dict[str, object], failure_analysis: Dict[str, object]
) -> str:
    failed = [step for step in report["steps"] if step["status"] != "PASS"]
    lines = [
        "# Pipeline Doctor Repair Prompt",
        "",
        "You are repairing a failing CI preflight in %s." % git_context.get("project_root", str(DEFAULT_PROJECT_ROOT)),
        "",
        "Constraints:",
        "- Change only files necessary to fix the failing checks.",
        "- Do not touch unrelated user changes.",
        "- After the fix, rerun smoke and contract-matrix checks.",
        "",
        "Current git context:",
        "- Branch: %s" % (git_context.get("branch") or "unknown"),
        "- HEAD: %s" % (git_context.get("head") or "unknown"),
        "",
        "Failure summary:",
        report["summary"],
        "",
        "Failure analysis:",
        "- Classification: %s" % failure_analysis["classification"],
        "- Execution policy: %s" % failure_analysis["execution_policy"],
        "- Reason: %s" % failure_analysis["reason"],
        "",
        "Candidate files:",
    ]
    for item in repair["candidate_files"]:
        lines.append("- %s" % item)
    if not repair["candidate_files"]:
        lines.append("- Inspect the failing step output directly.")
    lines.extend(["", "Step evidence:"])
    for step in failed:
        lines.extend(
            [
                "",
                "## %s" % step["name"],
                "Root cause hint: %s" % step["root_cause_hint"],
                "Command: %s" % " ".join(step["command"]),
                "Stdout:",
                "```text",
                (step["stdout"] or "").strip(),
                "```",
                "Stderr:",
                "```text",
                (step["stderr"] or "").strip(),
                "```",
            ]
        )
    if failure_analysis.get("execution_policy") != "provider_patch_allowed":
        lines.extend(
            [
                "",
                "## Stop Condition",
                "This bundle is classified as env-only. Do not create a repo patch.",
                "Return operational remediation notes instead of code changes.",
            ]
        )
    return "\n".join(lines).strip() + "\n"


def write_repair_bundle(report: Dict[str, object], project_root: Path) -> Dict[str, object]:
    git_context = collect_git_context(project_root)
    failure_analysis = dict(report.get("failure_analysis", {}))
    repair = build_repair_metadata(report, git_context, failure_analysis)
    bundle_dir = RUNS_DIR / ("%s_repair_bundle" % compact_stamp())
    bundle_dir.mkdir(parents=True, exist_ok=True)

    copied_report = bundle_dir / "report.json"
    copied_report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    git_path = bundle_dir / "git_context.json"
    git_path.write_text(json.dumps(git_context, ensure_ascii=False, indent=2), encoding="utf-8")

    pr_path = bundle_dir / "pr_metadata.json"
    pr_path.write_text(json.dumps(repair, ensure_ascii=False, indent=2), encoding="utf-8")

    prompt_path = bundle_dir / "repair_prompt.md"
    prompt_path.write_text(build_repair_prompt(report, repair, git_context, failure_analysis), encoding="utf-8")

    remediation_path = bundle_dir / "remediation_plan.md"
    remediation_lines = [
        "# Pipeline Doctor Remediation Plan",
        "",
        "Classification: %s" % failure_analysis.get("classification", "unknown"),
        "Execution policy: %s" % failure_analysis.get("execution_policy", "unknown"),
        "Reason: %s" % failure_analysis.get("reason", "No reason recorded."),
        "",
        "Recommended actions:",
    ]
    for action in failure_analysis.get("recommended_actions", []):
        remediation_lines.append("- %s" % action)
    base_probe = failure_analysis.get("base_probe") or {}
    if base_probe:
        remediation_lines.extend(
            [
                "",
                "Base probe:",
                "- Target: %s" % base_probe.get("target", ""),
                "- Reachable: %s" % base_probe.get("reachable", ""),
                "- HTTP code: %s" % base_probe.get("http_code", ""),
                "- curl rc: %s" % base_probe.get("curl_return_code", ""),
                "- stderr: %s" % base_probe.get("stderr", ""),
            ]
        )
    remediation_path.write_text("\n".join(remediation_lines) + "\n", encoding="utf-8")

    readme_lines = [
        "# Pipeline Doctor Repair Bundle",
        "",
        "Status: %s" % report["status"],
        "Generated: %s" % report["generated_at"],
        "",
        "Summary:",
        report["summary"],
        "",
        "Artifacts:",
        "- report.json",
        "- git_context.json",
        "- pr_metadata.json",
        "- repair_prompt.md",
        "- remediation_plan.md",
        "",
        "Suggested branch: %s" % repair["suggested_branch"],
        "Suggested commit: %s" % repair["commit_message"],
        "Execution policy: %s" % repair["execution_policy"],
    ]
    (bundle_dir / "README.md").write_text("\n".join(readme_lines) + "\n", encoding="utf-8")

    return {
        "bundle_dir": str(bundle_dir),
        "git_context": git_context,
        "pr_metadata": repair,
        "failure_analysis": failure_analysis,
    }


def write_handoff(report: Dict[str, object]) -> None:
    lines = [
        "## Gorev",
        "Pipeline Doctor self-healing preflight",
        "",
        "## Durum",
        report["status"],
        "",
        "## Sonuc Ozeti",
        report["summary"],
        "",
        "## Timestamp",
        report["generated_at"],
        "",
        "## Rapor",
        str(report["report_path"]),
        "",
    ]
    HANDOFF_PATH.write_text("\n".join(lines), encoding="utf-8")
    artifacts = [str(report["report_path"]), str(HANDOFF_PATH)]
    if report.get("repair_bundle"):
        artifacts.append(str(report["repair_bundle"]["bundle_dir"]))
    next_step = "No immediate action required."
    if report["status"] != "PASS":
        next_step = "Review repair bundle and run pipeline_repair_runner if code-actionable."
    write_checkpoint(
        agent="pipeline-doctor",
        task="Pipeline Doctor self-healing preflight",
        status=str(report["status"]).lower(),
        summary=str(report["summary"]),
        next_step=next_step,
        files=[str(Path(__file__))],
        artifacts=artifacts,
    )


def build_summary(steps: List[Dict[str, object]]) -> str:
    failed = [step for step in steps if step["status"] != "PASS"]
    if not failed:
        return "Smoke and contract matrix checks passed. No immediate CI healing action required."
    parts = []
    for step in failed:
        parts.append("%s failed: %s" % (step["name"], step["root_cause_hint"]))
    return " | ".join(parts)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run STELLCODEX Pipeline Doctor checks.")
    parser.add_argument("--base-url", default=os.getenv("BASE_URL", "http://127.0.0.1:8000"))
    parser.add_argument("--sample-file", default=os.getenv("SAMPLE_FILE", ""))
    parser.add_argument("--project-root", default=str(DEFAULT_PROJECT_ROOT))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ensure_dirs()
    project_root = Path(args.project_root).resolve()
    smoke_script = project_root / "scripts" / "smoke_test.sh"
    contract_script = project_root / "ci" / "contract_matrix.sh"

    env = os.environ.copy()
    env["BASE_URL"] = args.base_url
    if args.sample_file:
        env["SAMPLE_FILE"] = args.sample_file

    steps = [
        run_step("smoke_test", ["bash", str(smoke_script)], env, str(project_root)),
        run_step("contract_matrix", ["bash", str(contract_script)], env, str(project_root)),
    ]
    status = "PASS" if all(step["status"] == "PASS" for step in steps) else "FAIL"
    stamp = compact_stamp()
    report_path = RUNS_DIR / ("%s_pipeline_doctor.json" % stamp)
    report = {
        "generated_at": utc_iso(),
        "status": status,
        "base_url": args.base_url,
        "sample_file": args.sample_file,
        "project_root": str(project_root),
        "steps": steps,
        "summary": build_summary(steps),
        "report_path": str(report_path),
    }
    if status != "PASS":
        report["failure_analysis"] = build_failure_analysis(report)
        report["repair_bundle"] = write_repair_bundle(report, project_root)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    write_handoff(report)

    print("Pipeline Doctor | status=%s | report=%s" % (status, report_path))
    if report.get("repair_bundle"):
        print("Repair bundle: %s" % report["repair_bundle"]["bundle_dir"])
    for step in steps:
        print(
            "- %s: %s (exit=%s, %.2fs)"
            % (step["name"], step["status"], step["exit_code"], step["duration_seconds"])
        )
        if step["status"] != "PASS":
            print("  root_cause_hint=%s" % step["root_cause_hint"])
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
