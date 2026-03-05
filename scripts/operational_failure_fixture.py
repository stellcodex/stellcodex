#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List


WORKSPACE = Path("/root/workspace")
RUNS_DIR = WORKSPACE / "_runs" / "pipeline_doctor"
DEFAULT_SOURCE_REPO = Path("/var/www/stellcodex")
DEFAULT_FIXTURE_ROOT = Path("/tmp/stellcodex-operational-fixture")
DEFAULT_ENV_PATH = Path("/tmp/stellcodex-operational-fixture.env")
BROKEN_CONTAINER = "stellcodex-op-fixture"
FIXED_CONTAINER = "stellcodex-op-fixture-fixed"
DEFAULT_PORT = 18080
REQUIRED_ENV_KEYS = [
    "DATABASE_URL",
    "REDIS_URL",
    "JWT_ALG",
    "JWT_SECRET",
    "REFRESH_TOKEN_DAYS",
    "ACCESS_TOKEN_MINUTES",
    "RATE_LIMIT_PER_HOUR",
    "MAX_UPLOAD_BYTES",
    "FEATURE_FILES",
    "ALLOWED_CONTENT_TYPES",
    "CONVERSION_TIMEOUT_SECONDS",
    "BLENDER_TIMEOUT_SECONDS",
    "STELLCODEX_S3_ENDPOINT_URL",
    "STELLCODEX_S3_REGION",
    "STELLCODEX_S3_BUCKET",
    "STELLCODEX_S3_ACCESS_KEY_ID",
    "STELLCODEX_S3_SECRET_ACCESS_KEY",
    "PUBLIC_S3_BASE_URL",
    "WORKDIR",
    "ADMIN_TOKEN",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def compact_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def run(
    cmd: List[str],
    *,
    cwd: Path | None = None,
    env: Dict[str, str] | None = None,
    timeout: int = 300,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd or WORKSPACE),
        env=env,
        text=True,
        capture_output=True,
        timeout=timeout,
    )
    if check and proc.returncode != 0:
        raise RuntimeError(
            "command failed rc=%s\ncmd=%s\nstdout=%s\nstderr=%s"
            % (proc.returncode, " ".join(cmd), proc.stdout, proc.stderr)
        )
    return proc


def write_json(path: Path, payload: Dict[str, object]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def docker_rm(name: str) -> None:
    run(["docker", "rm", "-f", name], check=False, timeout=60)


def docker_logs(name: str) -> str:
    proc = run(["docker", "logs", name, "--tail", "80"], check=False, timeout=30)
    return (proc.stdout or "") + (proc.stderr or "")


def curl_code(url: str, timeout_seconds: int = 5) -> str:
    proc = run(
        ["curl", "-sS", "-o", "/dev/null", "-w", "%{http_code}", "--max-time", str(timeout_seconds), url],
        check=False,
        timeout=timeout_seconds + 5,
    )
    return (proc.stdout or "").strip() or "000"


def wait_http_code(url: str, expected: Iterable[str], timeout_seconds: int = 30) -> str:
    expected_set = set(expected)
    deadline = time.time() + timeout_seconds
    last_code = "000"
    while time.time() < deadline:
        last_code = curl_code(url)
        if last_code in expected_set:
            return last_code
        time.sleep(1)
    raise RuntimeError("timeout waiting for %s to return one of %s; last_code=%s" % (url, sorted(expected_set), last_code))


def copy_tree(src_repo: Path, fixture_root: Path) -> None:
    if fixture_root.exists():
        shutil.rmtree(fixture_root)
    (fixture_root / "backend").mkdir(parents=True, exist_ok=True)
    (fixture_root / "scripts").mkdir(parents=True, exist_ok=True)
    (fixture_root / "ci").mkdir(parents=True, exist_ok=True)
    (fixture_root / "docs" / "contracts").mkdir(parents=True, exist_ok=True)
    (fixture_root / "schemas").mkdir(parents=True, exist_ok=True)
    shutil.copytree(src_repo / "backend" / "app", fixture_root / "backend" / "app")
    shutil.copy2(src_repo / "scripts" / "smoke_test.sh", fixture_root / "scripts" / "smoke_test.sh")
    shutil.copy2(src_repo / "ci" / "contract_matrix.sh", fixture_root / "ci" / "contract_matrix.sh")


def init_git_repo(fixture_root: Path) -> None:
    run(["git", "init", str(fixture_root)], timeout=30)
    run(["git", "-C", str(fixture_root), "config", "user.email", "fixture@example.com"], timeout=30)
    run(["git", "-C", str(fixture_root), "config", "user.name", "Fixture Bot"], timeout=30)


def break_health_route(path: Path) -> None:
    original = path.read_text(encoding="utf-8")
    updated = original.replace("from fastapi import APIRouter\n", "from fastapi import APIRouter, HTTPException\n")
    updated = updated.replace('    return {"status": "ok"}\n', '    raise HTTPException(status_code=503, detail="operational fixture health failure")\n')
    if updated == original:
        raise RuntimeError("health route patch did not apply to %s" % path)
    path.write_text(updated, encoding="utf-8")


def collect_backend_env(env_path: Path) -> None:
    proc = run(["docker", "exec", "stellcodex-backend", "env"], timeout=30)
    values: Dict[str, str] = {}
    for line in proc.stdout.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key] = value
    missing = [key for key in REQUIRED_ENV_KEYS if key not in values]
    if missing:
        raise RuntimeError("missing required env keys from backend container: %s" % ", ".join(missing))
    env_path.write_text(
        "\n".join("%s=%s" % (key, values[key]) for key in REQUIRED_ENV_KEYS) + "\n",
        encoding="utf-8",
    )


def start_fixture_container(name: str, source_app_dir: Path, env_path: Path, port: int) -> str:
    docker_rm(name)
    proc = run(
        [
            "docker",
            "run",
            "-d",
            "--name",
            name,
            "--network",
            "deploy_default",
            "-p",
            "127.0.0.1:%s:8000" % port,
            "--env-file",
            str(env_path),
            "-v",
            "%s:/app/app:ro" % source_app_dir,
            "deploy_backend",
        ],
        timeout=60,
    )
    return proc.stdout.strip()


def run_pipeline_doctor(project_root: Path, base_url: str) -> Path:
    env = os.environ.copy()
    env["BACKEND_BASE_URL"] = base_url
    proc = run(
        [
            "python3",
            "/root/workspace/scripts/pipeline_doctor.py",
            "--project-root",
            str(project_root),
            "--base-url",
            base_url,
        ],
        env=env,
        timeout=120,
        check=False,
    )
    if not proc.stdout:
        raise RuntimeError("pipeline_doctor produced no stdout")
    report_path = None
    for line in proc.stdout.splitlines():
        if "report=" in line:
            report_path = line.split("report=", 1)[1].strip()
            break
    if not report_path:
        raise RuntimeError("could not locate report path in pipeline_doctor output:\n%s" % proc.stdout)
    return Path(report_path)


def run_repair_runner(bundle_dir: Path, fixture_root: Path, timeout_seconds: int) -> Path:
    proc = run(
        [
            "python3",
            "/root/workspace/scripts/pipeline_repair_runner.py",
            "--bundle",
            str(bundle_dir),
            "--source-project-root",
            str(fixture_root),
            "--provider",
            "codex",
            "--execute",
            "--unsafe-bypass-codex-sandbox",
            "--timeout",
            str(timeout_seconds),
        ],
        timeout=timeout_seconds + 120,
    )
    run_dir = None
    for line in proc.stdout.splitlines():
        if line.startswith("Pipeline Repair Runner | run_dir="):
            run_dir = line.split("run_dir=", 1)[1].strip()
            break
    if not run_dir:
        raise RuntimeError("could not locate repair runner run_dir in stdout:\n%s" % proc.stdout)
    return Path(run_dir)


def load_repair_runner_module() -> Any:
    module_path = WORKSPACE / "scripts" / "pipeline_repair_runner.py"
    spec = importlib.util.spec_from_file_location("pipeline_repair_runner_module", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load pipeline_repair_runner module from %s" % module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_smoke(script_root: Path, base_url: str) -> str:
    env = os.environ.copy()
    env["BASE_URL"] = base_url
    env["BACKEND_BASE_URL"] = base_url
    proc = run(["bash", "scripts/smoke_test.sh"], cwd=script_root, env=env, timeout=120)
    return proc.stdout


def run_contract(script_root: Path, base_url: str) -> str:
    env = os.environ.copy()
    env["BASE_URL"] = base_url
    env["BACKEND_BASE_URL"] = base_url
    proc = run(["bash", "ci/contract_matrix.sh"], cwd=script_root, env=env, timeout=120)
    return proc.stdout


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a scripted real operational-failure repair proof.")
    parser.add_argument("--source-repo", default=str(DEFAULT_SOURCE_REPO))
    parser.add_argument("--fixture-root", default=str(DEFAULT_FIXTURE_ROOT))
    parser.add_argument("--env-path", default=str(DEFAULT_ENV_PATH))
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--repair-timeout", type=int, default=180)
    parser.add_argument("--commit-with-approval-token", default="")
    parser.add_argument("--export-delivery-package", action="store_true")
    parser.add_argument("--push-with-approval-token", default="")
    parser.add_argument("--push-remote", default="origin")
    parser.add_argument("--push-remote-url", default="")
    parser.add_argument("--create-pr-with-approval-token", default="")
    parser.add_argument("--pr-base", default="main")
    args = parser.parse_args()

    source_repo = Path(args.source_repo).resolve()
    fixture_root = Path(args.fixture_root).resolve()
    env_path = Path(args.env_path).resolve()
    port = int(args.port)
    base_url = "http://127.0.0.1:%s" % port

    proof_dir = RUNS_DIR / ("%s_operational_failure_proof" % compact_stamp())
    proof_dir.mkdir(parents=True, exist_ok=True)

    result: Dict[str, object] = {
        "generated_at": utc_now(),
        "source_repo": str(source_repo),
        "fixture_root": str(fixture_root),
        "base_url": base_url,
        "steps": {},
    }
    delivery_requested = any(
        [
            bool(args.commit_with_approval_token),
            bool(args.export_delivery_package),
            bool(args.push_with_approval_token),
            bool(args.create_pr_with_approval_token),
        ]
    )
    delivery_failed = False

    try:
        copy_tree(source_repo, fixture_root)
        init_git_repo(fixture_root)
        break_health_route(fixture_root / "backend" / "app" / "api" / "v1" / "routes" / "health.py")
        run(["git", "-C", str(fixture_root), "add", "-A"], timeout=60)
        run(["git", "-C", str(fixture_root), "commit", "-m", "fixture: broken health runtime"], timeout=60)
        collect_backend_env(env_path)
        start_fixture_container(BROKEN_CONTAINER, fixture_root / "backend" / "app", env_path, port)
        wait_http_code(base_url + "/openapi.json", ["200"], timeout_seconds=30)
        health_code = wait_http_code(base_url + "/api/v1/health", ["503"], timeout_seconds=30)
        result["steps"]["broken_runtime"] = {
            "openapi_code": "200",
            "health_code": health_code,
            "container_logs": docker_logs(BROKEN_CONTAINER),
        }

        fail_report = run_pipeline_doctor(fixture_root, base_url)
        fail_payload = json.loads(fail_report.read_text(encoding="utf-8"))
        if fail_payload.get("status") != "FAIL":
            raise RuntimeError("expected failing pipeline_doctor report, got %s" % fail_payload.get("status"))
        result["steps"]["doctor_fail"] = {
            "report_path": str(fail_report),
            "repair_bundle": str(fail_payload["repair_bundle"]["bundle_dir"]),
            "classification": fail_payload["failure_analysis"]["classification"],
        }

        repair_run_dir = run_repair_runner(Path(fail_payload["repair_bundle"]["bundle_dir"]), fixture_root, args.repair_timeout)
        manifest = json.loads((repair_run_dir / "execution_manifest.json").read_text(encoding="utf-8"))
        if manifest["git_artifacts"]["has_diff"] != "yes":
            raise RuntimeError("repair runner did not produce a diff")
        worktree_dir = Path(manifest["worktree_dir"])
        result["steps"]["repair_runner"] = {
            "run_dir": str(repair_run_dir),
            "worktree_dir": str(worktree_dir),
            "manifest_path": str(repair_run_dir / "execution_manifest.json"),
        }

        docker_rm(BROKEN_CONTAINER)
        start_fixture_container(FIXED_CONTAINER, worktree_dir / "backend" / "app", env_path, port)
        wait_http_code(base_url + "/openapi.json", ["200"], timeout_seconds=30)
        fixed_health = wait_http_code(base_url + "/api/v1/health", ["200"], timeout_seconds=30)
        smoke_output = run_smoke(worktree_dir, base_url)
        contract_output = run_contract(worktree_dir, base_url)
        pass_report = run_pipeline_doctor(worktree_dir, base_url)
        pass_payload = json.loads(pass_report.read_text(encoding="utf-8"))
        if pass_payload.get("status") != "PASS":
            raise RuntimeError("expected passing pipeline_doctor report, got %s" % pass_payload.get("status"))
        result["steps"]["doctor_pass"] = {
            "report_path": str(pass_report),
            "health_code": fixed_health,
            "smoke_output": smoke_output,
            "contract_output": contract_output,
        }

        if delivery_requested:
            bundle_dir = Path(fail_payload["repair_bundle"]["bundle_dir"])
            pr_metadata = json.loads((bundle_dir / "pr_metadata.json").read_text(encoding="utf-8"))
            branch_name = str(manifest["branch_name"])
            delivery_step: Dict[str, object] = {
                "branch_name": branch_name,
                "requested": {
                    "commit": bool(args.commit_with_approval_token),
                    "export_delivery_package": bool(args.export_delivery_package),
                    "push": bool(args.push_with_approval_token),
                    "pr": bool(args.create_pr_with_approval_token),
                },
            }
            try:
                repair_runner = load_repair_runner_module()
                commit_result: Dict[str, object] = {}
                delivery_package: Dict[str, object] = {}
                push_result: Dict[str, object] = {}
                pr_result: Dict[str, object] = {}

                if args.commit_with_approval_token:
                    commit_result = repair_runner.commit_changes(
                        worktree_dir,
                        repair_run_dir,
                        str(pr_metadata["commit_message"]),
                        args.commit_with_approval_token,
                    )
                elif any([args.export_delivery_package, args.push_with_approval_token, args.create_pr_with_approval_token]):
                    commit_result = {
                        "status": "SKIP",
                        "reason": "commit_approval_token_missing",
                    }

                if args.export_delivery_package:
                    if commit_result.get("status") == "PASS":
                        delivery_package = repair_runner.export_delivery_package(
                            repair_run_dir,
                            pr_metadata,
                            branch_name,
                            commit_result,
                            args.push_remote,
                            args.push_remote_url,
                            args.pr_base,
                            worktree_dir,
                        )
                    else:
                        delivery_package = {
                            "status": "SKIP",
                            "reason": "commit_not_ready",
                        }

                if args.push_with_approval_token:
                    if commit_result.get("status") == "PASS":
                        push_result = repair_runner.push_branch(
                            worktree_dir,
                            repair_run_dir,
                            branch_name,
                            args.push_with_approval_token,
                            args.push_remote,
                            args.push_remote_url,
                        )
                    else:
                        push_result = {
                            "status": "SKIP",
                            "reason": "commit_not_ready",
                        }

                if args.create_pr_with_approval_token:
                    if push_result.get("status") == "PASS":
                        pr_result = repair_runner.create_pull_request(
                            repair_run_dir,
                            pr_metadata,
                            branch_name,
                            args.create_pr_with_approval_token,
                            args.pr_base,
                        )
                    else:
                        pr_result = {
                            "status": "SKIP",
                            "reason": "push_not_ready",
                        }

                delivery_step["commit_result"] = commit_result
                delivery_step["delivery_package"] = delivery_package
                delivery_step["push_result"] = push_result
                delivery_step["pr_result"] = pr_result
                delivery_step["status"] = "PASS"
                if commit_result.get("status") == "FAIL" or push_result.get("status") == "FAIL" or pr_result.get("status") == "FAIL":
                    delivery_step["status"] = "FAIL"
                    delivery_failed = True
            except Exception as exc:
                delivery_step["status"] = "FAIL"
                delivery_step["error"] = str(exc)
                delivery_failed = True
            result["steps"]["delivery"] = delivery_step

        result["status"] = "FAIL" if delivery_failed else "PASS"
        result["summary"] = "FAIL -> code_actionable bundle -> codex patch -> smoke PASS -> contract PASS -> doctor PASS"
        if delivery_requested:
            result["summary"] += " -> delivery readiness recorded"
        if delivery_failed:
            print("Operational failure proof FAIL: delivery step failed", file=sys.stderr)
        else:
            print("Operational failure proof PASS")
        print("Fail report: %s" % fail_report)
        print("Repair run: %s" % repair_run_dir)
        print("Pass report: %s" % pass_report)
        return_code = 1 if delivery_failed else 0
    except Exception as exc:
        result["status"] = "FAIL"
        result["error"] = str(exc)
        result["broken_logs"] = docker_logs(BROKEN_CONTAINER)
        result["fixed_logs"] = docker_logs(FIXED_CONTAINER)
        print("Operational failure proof FAIL: %s" % exc, file=sys.stderr)
        return_code = 1
    finally:
        write_json(proof_dir / "result.json", result)
        docker_rm(BROKEN_CONTAINER)
        docker_rm(FIXED_CONTAINER)

    return return_code


if __name__ == "__main__":
    sys.exit(main())
