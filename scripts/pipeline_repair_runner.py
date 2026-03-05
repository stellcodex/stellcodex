#!/usr/bin/env python3
import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

from progress_checkpoint import write_checkpoint


WORKSPACE = Path("/root/workspace")
RUNS_DIR = WORKSPACE / "_runs" / "pipeline_doctor"
HANDOFF_DIR = WORKSPACE / "handoff"
HANDOFF_PATH = HANDOFF_DIR / "pipeline-repair-runner-status.md"
DEFAULT_PROJECT_ROOT = Path("/var/www/stellcodex")
APPROVED_DIR = Path("/root/stell/genois/02_approved")


def utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def compact_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def ensure_dirs() -> None:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    HANDOFF_DIR.mkdir(parents=True, exist_ok=True)


def load_json(path: Path) -> Dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_command(
    cmd: List[str],
    *,
    cwd: Path = WORKSPACE,
    timeout: int = 30,
    input_text: str = "",
    env: Dict[str, str] = None,
) -> Tuple[int, str, str]:
    def normalize(value: object) -> str:
        if value is None:
            return ""
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="replace")
        return str(value)

    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
            input=input_text or None,
            env=env,
        )
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as exc:
        return 124, normalize(exc.stdout), normalize(exc.stderr) or "timeout"
    except Exception as exc:
        return 1, "", str(exc)


def bundle_name(path: Path) -> str:
    return path.name.replace("_repair_bundle", "")


def unique_branch_name(source_project_root: Path, base: str) -> str:
    rc, stdout, _ = run_command(
        ["git", "-C", str(source_project_root), "show-ref", "--verify", "--quiet", "refs/heads/%s" % base],
        timeout=10,
    )
    if rc != 0:
        return base
    return "%s-%s" % (base, compact_stamp())


def shell_escape(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def git_remote_url(project_root: Path, name: str = "origin") -> str:
    rc, stdout, _ = run_command(["git", "-C", str(project_root), "remote", "get-url", name], timeout=10)
    return stdout if rc == 0 else ""


def gh_auth_ready() -> bool:
    rc, _, _ = run_command(["gh", "auth", "status"], timeout=10)
    return rc == 0


def write_handoff(status: str, summary: str, run_dir: Path) -> None:
    lines = [
        "## Gorev",
        "Pipeline Repair Runner",
        "",
        "## Durum",
        status,
        "",
        "## Sonuc Ozeti",
        summary,
        "",
        "## Timestamp",
        utc_iso(),
        "",
        "## Run Dir",
        str(run_dir),
        "",
    ]
    HANDOFF_PATH.write_text("\n".join(lines), encoding="utf-8")
    normalized_status = status.lower()
    next_step = "Inspect delivery package and remote push/PR outputs."
    if normalized_status in {"fail", "failed"}:
        next_step = "Inspect run_dir artifacts and decide whether to rerun with adjusted provider or approval flags."
    write_checkpoint(
        agent="pipeline-repair-runner",
        task="Pipeline Repair Runner",
        status=normalized_status,
        summary=summary,
        next_step=next_step,
        files=[str(Path(__file__))],
        artifacts=[str(run_dir), str(HANDOFF_PATH)],
    )


def translate_command_for_worktree(cmd: List[str], source_project_root: Path, worktree_dir: Path) -> List[str]:
    translated: List[str] = []
    for item in cmd:
        if item.startswith(str(source_project_root)):
            rel = Path(item).relative_to(source_project_root)
            translated.append(str(worktree_dir / rel))
        else:
            translated.append(item)
    return translated


def prepare_worktree(source_project_root: Path, run_dir: Path, branch_name: str) -> Path:
    worktree_dir = run_dir / "worktree"
    rc, _, stderr = run_command(
        [
            "git",
            "-C",
            str(source_project_root),
            "worktree",
            "add",
            "-b",
            branch_name,
            str(worktree_dir),
            "HEAD",
        ],
        timeout=60,
    )
    if rc != 0:
        raise RuntimeError("git worktree add failed: %s" % stderr.strip())
    return worktree_dir


def collect_git_artifacts(worktree_dir: Path, run_dir: Path) -> Dict[str, str]:
    status_rc, status_out, status_err = run_command(
        ["git", "-C", str(worktree_dir), "status", "--short", "--branch"],
        timeout=20,
    )
    diff_stat_rc, diff_stat_out, diff_stat_err = run_command(
        ["git", "-C", str(worktree_dir), "diff", "--stat"],
        timeout=20,
    )
    diff_rc, diff_out, diff_err = run_command(
        ["git", "-C", str(worktree_dir), "diff", "--binary"],
        timeout=30,
    )
    untracked_rc, untracked_out, untracked_err = run_command(
        ["git", "-C", str(worktree_dir), "ls-files", "--others", "--exclude-standard"],
        timeout=20,
    )
    untracked_files = [line.strip() for line in untracked_out.splitlines() if line.strip()] if untracked_rc == 0 else []

    untracked_patch_parts = []
    for rel_path in untracked_files:
        file_path = worktree_dir / rel_path
        rc, stdout, stderr = run_command(
            ["git", "-C", str(worktree_dir), "diff", "--no-index", "--binary", "--", "/dev/null", str(file_path)],
            timeout=20,
        )
        if rc in (0, 1):
            untracked_patch_parts.append(stdout)
        elif stderr:
            untracked_patch_parts.append(stderr)

    status_path = run_dir / "git_status.txt"
    status_path.write_text(status_out if status_rc == 0 else status_err, encoding="utf-8")

    diff_stat_path = run_dir / "git_diff_stat.txt"
    diff_stat_text = diff_stat_out if diff_stat_rc == 0 else diff_stat_err
    if untracked_files:
        diff_stat_text = (diff_stat_text + "\n" if diff_stat_text else "") + "\n".join(
            "untracked: %s" % item for item in untracked_files
        )
    diff_stat_path.write_text(diff_stat_text, encoding="utf-8")

    diff_path = run_dir / "proposed.patch"
    combined_patch = diff_out if diff_rc == 0 else diff_err
    if untracked_patch_parts:
        combined_patch = (combined_patch + "\n" if combined_patch else "") + "\n".join(untracked_patch_parts)
    diff_path.write_text(combined_patch, encoding="utf-8")

    untracked_path = run_dir / "untracked_files.txt"
    untracked_path.write_text("\n".join(untracked_files), encoding="utf-8")

    return {
        "status_path": str(status_path),
        "diff_stat_path": str(diff_stat_path),
        "diff_path": str(diff_path),
        "untracked_path": str(untracked_path),
        "has_diff": "yes" if bool((diff_out or "").strip()) or bool(untracked_files) else "no",
    }


def verify_steps(report: Dict[str, object], source_project_root: Path, worktree_dir: Path, run_dir: Path) -> Dict[str, object]:
    env = os.environ.copy()
    env["BASE_URL"] = str(report.get("base_url", "http://127.0.0.1:8000"))
    if report.get("sample_file"):
        env["SAMPLE_FILE"] = str(report["sample_file"])

    results = []
    for step in report.get("steps", []):
        translated = translate_command_for_worktree(step["command"], source_project_root, worktree_dir)
        rc, stdout, stderr = run_command(translated, cwd=worktree_dir, timeout=120, env=env)
        results.append(
            {
                "name": step["name"],
                "command": translated,
                "return_code": rc,
                "status": "PASS" if rc == 0 else "FAIL",
                "stdout": stdout,
                "stderr": stderr,
            }
        )

    verify_path = run_dir / "verify_results.json"
    payload = {
        "generated_at": utc_iso(),
        "base_url": report.get("base_url"),
        "results": results,
        "status": "PASS" if all(item["status"] == "PASS" for item in results) else "FAIL",
    }
    verify_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "verify_path": str(verify_path),
        "status": payload["status"],
    }


def load_approval_record(token: str) -> Dict[str, object]:
    path = APPROVED_DIR / ("%s.json" % token)
    if not path.exists():
        raise RuntimeError("Approval token not found in approved store: %s" % token)
    record = load_json(path)
    if record.get("status") != "approved":
        raise RuntimeError("Approval token is not approved: %s" % token)
    return record


def commit_changes(
    worktree_dir: Path,
    run_dir: Path,
    commit_message: str,
    approval_token: str,
) -> Dict[str, object]:
    record = load_approval_record(approval_token)
    add_rc, add_out, add_err = run_command(["git", "-C", str(worktree_dir), "add", "-A"], timeout=30)
    commit_cmd = [
        "git",
        "-C",
        str(worktree_dir),
        "commit",
        "-m",
        commit_message,
    ]
    commit_rc, commit_out, commit_err = run_command(commit_cmd, timeout=60)
    payload = {
        "approval_token": approval_token,
        "approval_record": record,
        "add_return_code": add_rc,
        "add_stdout": add_out,
        "add_stderr": add_err,
        "commit_return_code": commit_rc,
        "commit_stdout": commit_out,
        "commit_stderr": commit_err,
        "status": "PASS" if add_rc == 0 and commit_rc == 0 else "FAIL",
    }
    commit_path = run_dir / "commit_result.json"
    commit_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    payload["commit_path"] = str(commit_path)
    return payload


def ensure_remote(worktree_dir: Path, remote_name: str, remote_url: str) -> str:
    if not remote_url:
        rc, stdout, stderr = run_command(
            ["git", "-C", str(worktree_dir), "remote", "get-url", remote_name],
            timeout=10,
        )
        if rc != 0:
            raise RuntimeError("Push remote not found: %s (%s)" % (remote_name, stderr.strip()))
        return stdout.strip()

    existing_rc, _, _ = run_command(
        ["git", "-C", str(worktree_dir), "remote", "get-url", remote_name],
        timeout=10,
    )
    if existing_rc == 0:
        set_rc, _, set_err = run_command(
            ["git", "-C", str(worktree_dir), "remote", "set-url", remote_name, remote_url],
            timeout=10,
        )
        if set_rc != 0:
            raise RuntimeError("Push remote set-url failed: %s" % set_err.strip())
    else:
        add_rc, _, add_err = run_command(
            ["git", "-C", str(worktree_dir), "remote", "add", remote_name, remote_url],
            timeout=10,
        )
        if add_rc != 0:
            raise RuntimeError("Push remote add failed: %s" % add_err.strip())
    return remote_url


def push_branch(
    worktree_dir: Path,
    run_dir: Path,
    branch_name: str,
    approval_token: str,
    remote_name: str,
    remote_url: str,
) -> Dict[str, object]:
    record = load_approval_record(approval_token)
    resolved_remote_url = ensure_remote(worktree_dir, remote_name, remote_url)
    push_rc, push_out, push_err = run_command(
        ["git", "-C", str(worktree_dir), "push", "-u", remote_name, branch_name],
        timeout=120,
    )
    payload = {
        "approval_token": approval_token,
        "approval_record": record,
        "remote_name": remote_name,
        "remote_url": resolved_remote_url,
        "push_return_code": push_rc,
        "push_stdout": push_out,
        "push_stderr": push_err,
        "status": "PASS" if push_rc == 0 else "FAIL",
    }
    push_path = run_dir / "push_result.json"
    push_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    payload["push_path"] = str(push_path)
    return payload


def create_pull_request(
    run_dir: Path,
    pr_metadata: Dict[str, object],
    branch_name: str,
    approval_token: str,
    base_branch: str,
) -> Dict[str, object]:
    record = load_approval_record(approval_token)
    if not gh_auth_ready():
        payload = {
            "approval_token": approval_token,
            "approval_record": record,
            "base_branch": base_branch,
            "status": "SKIP",
            "reason": "gh_auth_not_ready",
        }
    else:
        delivery_dir = run_dir / "delivery_package"
        pr_body_path = delivery_dir / "pr_body.md"
        if not pr_body_path.exists():
            delivery_dir.mkdir(parents=True, exist_ok=True)
            pr_body_path.write_text(str(pr_metadata["pr_body"]) + "\n", encoding="utf-8")
        pr_rc, pr_out, pr_err = run_command(
            [
                "gh",
                "pr",
                "create",
                "--base",
                base_branch,
                "--head",
                branch_name,
                "--title",
                str(pr_metadata["pr_title"]),
                "--body-file",
                str(pr_body_path),
            ],
            timeout=120,
        )
        payload = {
            "approval_token": approval_token,
            "approval_record": record,
            "base_branch": base_branch,
            "pr_return_code": pr_rc,
            "pr_stdout": pr_out,
            "pr_stderr": pr_err,
            "status": "PASS" if pr_rc == 0 else "FAIL",
        }
    pr_path = run_dir / "pr_result.json"
    pr_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    payload["pr_path"] = str(pr_path)
    return payload


def export_delivery_package(
    run_dir: Path,
    pr_metadata: Dict[str, object],
    branch_name: str,
    commit_result: Dict[str, object],
    remote_name: str,
    remote_url: str,
    base_branch: str,
    source_project_root: Path,
) -> Dict[str, object]:
    delivery_dir = run_dir / "delivery_package"
    delivery_dir.mkdir(parents=True, exist_ok=True)

    pr_body_path = delivery_dir / "pr_body.md"
    pr_body_path.write_text(str(pr_metadata["pr_body"]) + "\n", encoding="utf-8")

    push_script_path = delivery_dir / "push_branch.sh"
    push_lines = ["#!/usr/bin/env bash", "set -euo pipefail"]
    if remote_url:
        push_lines.append(
            "if git remote get-url %s >/dev/null 2>&1; then git remote set-url %s %s; else git remote add %s %s; fi"
            % (
                shell_escape(remote_name),
                shell_escape(remote_name),
                shell_escape(remote_url),
                shell_escape(remote_name),
                shell_escape(remote_url),
            )
        )
    push_lines.append("git push -u %s %s" % (shell_escape(remote_name), shell_escape(branch_name)))
    push_script = "\n".join(push_lines) + "\n"
    push_script_path.write_text(push_script, encoding="utf-8")

    gh_script_path = delivery_dir / "create_pr.sh"
    gh_script = (
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "gh pr create "
        "--base %s "
        "--head %s "
        "--title %s "
        "--body-file %s\n"
    ) % (
        shell_escape(base_branch),
        shell_escape(branch_name),
        shell_escape(str(pr_metadata["pr_title"])),
        shell_escape(str(pr_body_path)),
    )
    gh_script_path.write_text(gh_script, encoding="utf-8")

    payload = {
        "generated_at": utc_iso(),
        "branch_name": branch_name,
        "remote_name": remote_name,
        "remote_url": (remote_url or git_remote_url(source_project_root, remote_name).strip()),
        "base_branch": base_branch,
        "gh_auth_ready": gh_auth_ready(),
        "commit_result_status": commit_result.get("status", ""),
        "push_script_path": str(push_script_path),
        "create_pr_script_path": str(gh_script_path),
        "pr_body_path": str(pr_body_path),
        "pr_title": pr_metadata["pr_title"],
    }
    manifest_path = delivery_dir / "delivery_manifest.json"
    manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "delivery_dir": str(delivery_dir),
        "manifest_path": str(manifest_path),
        "gh_auth_ready": payload["gh_auth_ready"],
    }


def execute_codex(
    source_project_root: Path,
    worktree_dir: Path,
    prompt_path: Path,
    run_dir: Path,
    timeout: int,
    unsafe_bypass: bool,
) -> Dict[str, object]:
    prompt = prompt_path.read_text(encoding="utf-8")
    prompt = prompt.replace(str(source_project_root), str(worktree_dir))
    cmd = [
        "codex",
        "exec",
        "-C",
        str(worktree_dir),
        "--json",
        "--output-last-message",
        str(run_dir / "codex_final_message.txt"),
        "-",
    ]
    if unsafe_bypass:
        cmd.insert(2, "--dangerously-bypass-approvals-and-sandbox")
    else:
        cmd.insert(2, "--sandbox")
        cmd.insert(3, "workspace-write")
    rc, stdout, stderr = run_command(cmd, cwd=WORKSPACE, timeout=timeout, input_text=prompt)
    events_path = run_dir / "codex_events.jsonl"
    events_path.write_text(stdout, encoding="utf-8")
    stderr_path = run_dir / "codex_stderr.txt"
    stderr_path.write_text(stderr, encoding="utf-8")
    return {
        "return_code": rc,
        "events_path": str(events_path),
        "stderr_path": str(stderr_path),
        "final_message_path": str(run_dir / "codex_final_message.txt"),
    }


def build_summary(executed: bool, exec_result: Dict[str, object], git_artifacts: Dict[str, str]) -> str:
    if exec_result.get("status") == "SKIP":
        return "Provider yurutmesi politika geregi atlandi."
    if not executed:
        return "Worktree hazirlandi; provider calistirilmadi."
    if int(exec_result["return_code"]) != 0:
        return "Provider calisti fakat basarisiz oldu. stderr artefaktini inceleyin."
    if git_artifacts["has_diff"] == "yes":
        return "Provider tamamlandi ve patch diff olustu."
    return "Provider tamamlandi ancak diff olusmadi."


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a provider against a Pipeline Doctor repair bundle.")
    parser.add_argument("--bundle", required=True, help="Path to *_repair_bundle directory")
    parser.add_argument("--provider", default="codex", choices=["codex"])
    parser.add_argument("--execute", action="store_true", help="Actually invoke the provider after preparing the worktree.")
    parser.add_argument("--verify", action="store_true", help="Rerun report steps inside the isolated worktree.")
    parser.add_argument(
        "--commit-with-approval-token",
        default="",
        help="Create a git commit in the isolated worktree only if this approved D-SAC token is present.",
    )
    parser.add_argument("--timeout", type=int, default=180, help="Provider timeout in seconds")
    parser.add_argument(
        "--unsafe-bypass-codex-sandbox",
        action="store_true",
        help="Run codex with --dangerously-bypass-approvals-and-sandbox inside the isolated worktree.",
    )
    parser.add_argument(
        "--export-delivery-package",
        action="store_true",
        help="Export push and PR command artifacts after a successful isolated commit.",
    )
    parser.add_argument(
        "--push-with-approval-token",
        default="",
        help="Push the isolated branch only if this approved D-SAC token is present.",
    )
    parser.add_argument("--push-remote", default="origin", help="Remote name to use for push/export operations.")
    parser.add_argument(
        "--push-remote-url",
        default="",
        help="Optional remote URL to configure inside the isolated worktree before push.",
    )
    parser.add_argument(
        "--source-project-root",
        default="",
        help="Optional repository root to use instead of the bundle's project_root.",
    )
    parser.add_argument(
        "--create-pr-with-approval-token",
        default="",
        help="Create a PR with gh only if this approved D-SAC token is present.",
    )
    parser.add_argument("--pr-base", default="main", help="Base branch to target when creating a PR.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ensure_dirs()

    bundle_dir = Path(args.bundle).resolve()
    if not bundle_dir.exists():
        raise SystemExit("Bundle not found: %s" % bundle_dir)

    report = load_json(bundle_dir / "report.json")
    pr_metadata = load_json(bundle_dir / "pr_metadata.json")
    git_context = load_json(bundle_dir / "git_context.json")
    run_dir = RUNS_DIR / ("%s_repair_exec" % compact_stamp())
    run_dir.mkdir(parents=True, exist_ok=True)
    execution_policy = str(pr_metadata.get("execution_policy", "provider_patch_allowed"))
    source_project_root = Path(
        args.source_project_root
        or str(report.get("project_root") or git_context.get("project_root") or DEFAULT_PROJECT_ROOT)
    ).resolve()

    branch_name = unique_branch_name(source_project_root, str(pr_metadata["suggested_branch"]))
    worktree_dir = prepare_worktree(source_project_root, run_dir, branch_name)

    shutil.copy2(bundle_dir / "repair_prompt.md", run_dir / "repair_prompt.md")
    shutil.copy2(bundle_dir / "pr_metadata.json", run_dir / "pr_metadata.json")
    shutil.copy2(bundle_dir / "report.json", run_dir / "report.json")

    execution: Dict[str, object] = {"return_code": None}
    provider_policy_blocked = args.execute and execution_policy != "provider_patch_allowed"
    if provider_policy_blocked:
        execution = {
            "status": "SKIP",
            "reason": execution_policy,
            "return_code": None,
            "recommended_actions": pr_metadata.get("recommended_actions", []),
        }
    elif args.execute:
        execution = execute_codex(
            source_project_root,
            worktree_dir,
            bundle_dir / "repair_prompt.md",
            run_dir,
            args.timeout,
            args.unsafe_bypass_codex_sandbox,
        )

    git_artifacts = collect_git_artifacts(worktree_dir, run_dir)
    verification: Dict[str, object] = {}
    if args.verify and provider_policy_blocked:
        verification = {
            "status": "SKIP",
            "reason": execution_policy,
        }
    elif args.verify:
        verification = verify_steps(report, source_project_root, worktree_dir, run_dir)

    commit_result: Dict[str, object] = {}
    if args.commit_with_approval_token:
        approval_record: Dict[str, object] = {}
        try:
            approval_record = load_approval_record(args.commit_with_approval_token)
        except Exception as exc:
            commit_result = {
                "status": "FAIL",
                "reason": "approval_invalid",
                "approval_token": args.commit_with_approval_token,
                "error": str(exc),
            }
        if not commit_result and git_artifacts["has_diff"] != "yes":
            commit_result = {
                "status": "SKIP",
                "reason": "no_diff",
                "approval_token": args.commit_with_approval_token,
                "approval_record": approval_record,
            }
        elif not commit_result and verification and verification.get("status") != "PASS":
            commit_result = {
                "status": "SKIP",
                "reason": "verify_failed",
                "approval_token": args.commit_with_approval_token,
                "approval_record": approval_record,
            }
        elif not commit_result:
            commit_result = commit_changes(
                worktree_dir,
                run_dir,
                str(pr_metadata["commit_message"]),
                args.commit_with_approval_token,
            )
        if commit_result and approval_record and "approval_record" not in commit_result:
            commit_result["approval_record"] = approval_record

    delivery_package: Dict[str, object] = {}
    if args.export_delivery_package and commit_result.get("status") == "PASS":
        delivery_package = export_delivery_package(
            run_dir,
            pr_metadata,
            branch_name,
            commit_result,
            args.push_remote,
            args.push_remote_url,
            args.pr_base,
            source_project_root,
        )

    push_result: Dict[str, object] = {}
    if args.push_with_approval_token:
        approval_record: Dict[str, object] = {}
        try:
            approval_record = load_approval_record(args.push_with_approval_token)
        except Exception as exc:
            push_result = {
                "status": "FAIL",
                "reason": "approval_invalid",
                "approval_token": args.push_with_approval_token,
                "error": str(exc),
            }
        if not push_result and commit_result.get("status") != "PASS":
            push_result = {
                "status": "SKIP",
                "reason": "commit_not_ready",
                "approval_token": args.push_with_approval_token,
                "approval_record": approval_record,
            }
        elif not push_result:
            push_result = push_branch(
                worktree_dir,
                run_dir,
                branch_name,
                args.push_with_approval_token,
                args.push_remote,
                args.push_remote_url,
            )
        if push_result and approval_record and "approval_record" not in push_result:
            push_result["approval_record"] = approval_record

    pr_result: Dict[str, object] = {}
    if args.create_pr_with_approval_token:
        approval_record = {}
        try:
            approval_record = load_approval_record(args.create_pr_with_approval_token)
        except Exception as exc:
            pr_result = {
                "status": "FAIL",
                "reason": "approval_invalid",
                "approval_token": args.create_pr_with_approval_token,
                "error": str(exc),
            }
        if not pr_result and push_result.get("status") != "PASS":
            pr_result = {
                "status": "SKIP",
                "reason": "push_not_ready",
                "approval_token": args.create_pr_with_approval_token,
                "approval_record": approval_record,
            }
        elif not pr_result:
            pr_result = create_pull_request(
                run_dir,
                pr_metadata,
                branch_name,
                args.create_pr_with_approval_token,
                args.pr_base,
            )
        if pr_result and approval_record and "approval_record" not in pr_result:
            pr_result["approval_record"] = approval_record

    manifest = {
        "generated_at": utc_iso(),
        "source_bundle": str(bundle_dir),
        "source_report_status": report["status"],
        "provider": args.provider,
        "executed": args.execute,
        "execution_policy": execution_policy,
        "unsafe_bypass_codex_sandbox": args.unsafe_bypass_codex_sandbox,
        "source_project_root": str(source_project_root),
        "worktree_dir": str(worktree_dir),
        "branch_name": branch_name,
        "execution": execution,
        "git_artifacts": git_artifacts,
        "verification": verification,
        "commit_result": commit_result,
        "delivery_package": delivery_package,
        "push_result": push_result,
        "pr_result": pr_result,
    }
    manifest_path = run_dir / "execution_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    summary = build_summary(args.execute, execution, git_artifacts)
    write_handoff("PASS" if (not args.execute or int(execution.get("return_code") or 0) == 0) else "FAIL", summary, run_dir)

    print("Pipeline Repair Runner | run_dir=%s" % run_dir)
    print("Worktree: %s" % worktree_dir)
    print("Branch: %s" % branch_name)
    print("Executed: %s" % ("yes" if args.execute else "no"))
    if args.execute:
        if execution.get("status") == "SKIP":
            print("Provider: SKIP (%s)" % execution.get("reason", "policy"))
        else:
            print("Provider rc: %s" % execution["return_code"])
    if args.verify:
        print("Verify: %s" % verification.get("status", "unknown"))
    if args.commit_with_approval_token:
        print("Commit: %s" % commit_result.get("status", "unknown"))
    if args.export_delivery_package:
        print("Delivery package: %s" % (delivery_package.get("delivery_dir") or "not-created"))
    if args.push_with_approval_token:
        print("Push: %s" % push_result.get("status", "unknown"))
    if args.create_pr_with_approval_token:
        print("PR: %s" % pr_result.get("status", "unknown"))
    print("Diff generated: %s" % git_artifacts["has_diff"])
    print("Manifest: %s" % manifest_path)
    failure = args.execute and execution.get("status") != "SKIP" and int(execution.get("return_code") or 0) != 0
    if verification and verification.get("status") == "FAIL":
        failure = True
    if commit_result and commit_result.get("status") == "FAIL":
        failure = True
    if push_result and push_result.get("status") == "FAIL":
        failure = True
    if pr_result and pr_result.get("status") == "FAIL":
        failure = True
    return 0 if not failure else 1


if __name__ == "__main__":
    sys.exit(main())
