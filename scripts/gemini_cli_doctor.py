#!/usr/bin/env python3
import json
import os
import shutil
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from progress_checkpoint import write_checkpoint


WORKSPACE = Path("/root/workspace")
RUNS_DIR = WORKSPACE / "_runs" / "gemini_cli_doctor"
HANDOFF_DIR = WORKSPACE / "handoff"
HANDOFF_PATH = HANDOFF_DIR / "gemini-cli-doctor-status.md"
TMP_ROOT = Path("/tmp")
GEMINI_ENTRY = Path("/usr/lib/node_modules/@google/gemini-cli/dist/index.js")
GEMINI_CORE = Path("/usr/lib/node_modules/@google/gemini-cli/node_modules/@google/gemini-cli-core/dist/src")
ENV_PATHS = [
    Path("/root/stell/webhook/.env"),
    Path("/var/www/stellcodex/backend/.env"),
]

IMPORT_SNIPPET = (
    "import(process.argv[1]).then(() => { console.log('IMPORT_OK'); process.exit(0); })"
    ".catch(err => { console.error(err); process.exit(1); })"
)


def utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def compact_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def ensure_dirs() -> None:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    HANDOFF_DIR.mkdir(parents=True, exist_ok=True)


def trim_text(text: str, limit: int = 1800) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 14].rstrip() + "\n...[truncated]"


def load_env_key(paths: List[Path], key: str) -> str:
    for env_path in paths:
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


def run_step(
    name: str,
    cmd: List[str],
    cwd: str = "/tmp",
    timeout: int = 10,
    env: Optional[Dict[str, str]] = None,
) -> Dict[str, object]:
    started = time.time()
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            env=run_env,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        duration = round(time.time() - started, 2)
        return {
            "name": name,
            "command": cmd,
            "cwd": cwd,
            "timeout_seconds": timeout,
            "exit_code": proc.returncode,
            "status": "PASS" if proc.returncode == 0 else "FAIL",
            "duration_seconds": duration,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }
    except subprocess.TimeoutExpired as exc:
        duration = round(time.time() - started, 2)
        return {
            "name": name,
            "command": cmd,
            "cwd": cwd,
            "timeout_seconds": timeout,
            "exit_code": 124,
            "status": "TIMEOUT",
            "duration_seconds": duration,
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
        }
    except Exception as exc:
        duration = round(time.time() - started, 2)
        return {
            "name": name,
            "command": cmd,
            "cwd": cwd,
            "timeout_seconds": timeout,
            "exit_code": 1,
            "status": "ERROR",
            "duration_seconds": duration,
            "stdout": "",
            "stderr": str(exc),
        }


def summarize(report: Dict[str, object]) -> str:
    steps = report["steps"]
    version_step = next(step for step in steps if step["name"] == "gemini_version_isolated")
    prompt_step = next(step for step in steps if step["name"] == "gemini_prompt_isolated")
    heavy = [
        step["name"]
        for step in steps
        if step["name"].startswith("import_")
        and step["status"] == "TIMEOUT"
        and step["name"] != "import_paths_control"
    ]
    controls = [
        step["name"]
        for step in steps
        if step["name"] in ("import_paths_control", "import_extensions_control")
        and step["status"] == "PASS"
    ]
    lines = [
        "Gemini CLI doctor",
        "",
        "Binary: %s" % report["environment"]["gemini_binary"],
        "API key present: %s" % ("yes" if report["environment"]["gemini_api_key_present"] else "no"),
        "Isolated home: %s" % report["environment"]["gemini_cli_home"],
        "",
        "gemini --version: %s (%ss)" % (version_step["status"], version_step["duration_seconds"]),
        "gemini -p smoke: %s (%ss)" % (prompt_step["status"], prompt_step["duration_seconds"]),
        "Control imports passing: %s" % (", ".join(controls) or "none"),
        "Heavy imports timing out: %s" % (", ".join(heavy) or "none"),
    ]
    if heavy and controls:
        lines.append("Conclusion: startup hang is localized to a subset of Gemini core imports, not all module loading.")
    return "\n".join(lines)


def write_handoff(summary: str, report_path: Path) -> None:
    HANDOFF_PATH.write_text(
        "\n".join(
            [
                "## Gorev",
                "Gemini CLI startup hang diagnozu",
                "",
                "## Durum",
                "completed",
                "",
                "## Sonuc Ozeti",
                trim_text(summary, 1400),
                "",
                "## Report",
                str(report_path),
                "",
                "## Timestamp",
                utc_iso(),
                "",
            ]
        ),
        encoding="utf-8",
    )
    write_checkpoint(
        agent="gemini-cli-doctor",
        task="Gemini CLI startup hang diagnozu",
        status="completed",
        summary=trim_text(summary, 1400),
        next_step="Native import zinciri tekrar duzeltilecekse doctor raporundaki timeout modullerinden devam et.",
        files=[str(Path(__file__))],
        artifacts=[str(report_path), str(HANDOFF_PATH)],
    )


def main() -> int:
    ensure_dirs()
    stamp = compact_stamp()
    report_path = RUNS_DIR / f"{stamp}_gemini_cli_doctor.json"

    gemini_binary = shutil.which("gemini") or ""
    node_binary = shutil.which("node") or ""
    api_key = (
        os.getenv("GEMINI_API_KEY")
        or os.getenv("GOOGLE_API_KEY")
        or load_env_key(ENV_PATHS, "GEMINI_API_KEY")
        or load_env_key(ENV_PATHS, "GOOGLE_API_KEY")
    )
    gemini_home = tempfile.mkdtemp(prefix="gemini-home.", dir=str(TMP_ROOT))
    base_env = {
        "GEMINI_CLI_HOME": gemini_home,
        "SANDBOX": "local",
        "NO_COLOR": "1",
        "CI": "1",
    }
    if api_key:
        base_env["GEMINI_API_KEY"] = api_key

    steps: List[Dict[str, object]] = []
    steps.append(run_step("node_version", ["node", "--version"], timeout=6))
    steps.append(run_step("gemini_version_isolated", ["gemini", "--version"], timeout=15, env=base_env))
    steps.append(
        run_step(
            "gemini_prompt_isolated",
            [
                "gemini",
                "-p",
                "Reply with exactly READY.",
                "--output-format",
                "text",
                "--model",
                "gemini-2.5-flash",
            ],
            timeout=20,
            env=base_env,
        )
    )
    steps.append(
        run_step(
            "import_paths_control",
            ["node", "-e", IMPORT_SNIPPET, str(GEMINI_CORE / "utils/paths.js")],
            timeout=6,
        )
    )
    steps.append(
        run_step(
            "import_extensions_control",
            ["node", "-e", IMPORT_SNIPPET, str(GEMINI_CORE / "commands/extensions.js")],
            timeout=8,
        )
    )
    for name, module_path, timeout in (
        ("import_core_index", GEMINI_ENTRY, 12),
        ("import_config_config", GEMINI_CORE / "config/config.js", 8),
        ("import_telemetry_index", GEMINI_CORE / "telemetry/index.js", 8),
        ("import_code_assist", GEMINI_CORE / "code_assist/codeAssist.js", 8),
        ("import_hooks_index", GEMINI_CORE / "hooks/index.js", 8),
    ):
        steps.append(
            run_step(
                name,
                ["node", "-e", IMPORT_SNIPPET, str(module_path)],
                timeout=timeout,
            )
        )

    report = {
        "generated_at": utc_iso(),
        "environment": {
            "gemini_binary": gemini_binary,
            "node_binary": node_binary,
            "gemini_entry": str(GEMINI_ENTRY),
            "gemini_core_root": str(GEMINI_CORE),
            "gemini_cli_home": gemini_home,
            "gemini_api_key_present": bool(api_key),
            "env_paths_checked": [str(path) for path in ENV_PATHS],
        },
        "steps": steps,
    }
    report["summary"] = summarize(report)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    write_handoff(str(report["summary"]), report_path)
    print(json.dumps({"report_path": str(report_path), "summary": report["summary"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
