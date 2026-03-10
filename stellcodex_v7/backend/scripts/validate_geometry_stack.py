from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
import textwrap
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.engineering import (  # noqa: E402
    MODE_BREP,
    MODE_MESH_APPROX,
    build_geometry_metrics_payload,
)


DEFAULT_PACKAGES: List[Tuple[str, str, bool]] = [
    ("cadquery", "cadquery", False),
    ("OCP", "OCP", False),
    ("trimesh", "trimesh", False),
    ("meshio", "meshio", False),
    ("shapely", "shapely", False),
    ("networkx", "networkx", False),
    ("pyvista", "pyvista", False),
    ("open3d", "open3d", True),
    ("pythonocc-core", "OCC", True),
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def run_command(
    cmd: List[str],
    *,
    cwd: Optional[Path] = None,
    timeout_seconds: Optional[int] = 30,
) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else (exc.stdout or b"").decode("utf-8", "ignore")
        stderr = exc.stderr if isinstance(exc.stderr, str) else (exc.stderr or b"").decode("utf-8", "ignore")
        message = stderr or stdout or ("command timed out after %ss" % timeout_seconds)
        return subprocess.CompletedProcess(cmd, 124, stdout, message)


def environment_discovery(python_exec: str) -> Dict[str, Any]:
    pip_version = run_command([python_exec, "-m", "pip", "--version"], timeout_seconds=30)
    return {
        "generated_at": now_iso(),
        "repo_root": str(ROOT),
        "cwd": os.getcwd(),
        "python_executable": python_exec,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "system": platform.system(),
        "active_virtual_env": os.environ.get("VIRTUAL_ENV"),
        "engineering_virtual_env_exists": str((ROOT / ".venv-engineering").exists()).lower(),
        "pip_version": (pip_version.stdout or pip_version.stderr).strip(),
    }


def pip_freeze(python_exec: str) -> str:
    result = run_command([python_exec, "-m", "pip", "freeze"], timeout_seconds=120)
    return result.stdout.strip()


def pip_show(python_exec: str, package_name: str) -> str:
    result = run_command([python_exec, "-m", "pip", "show", package_name], timeout_seconds=30)
    if result.returncode != 0:
        return "not_installed"
    return (result.stdout or "").strip()


def _decode_json(stdout: str) -> Dict[str, Any]:
    try:
        decoded = json.loads(stdout)
        return decoded if isinstance(decoded, dict) else {}
    except Exception:
        return {}


def probe_import(python_exec: str, dist_name: str, import_name: str) -> Dict[str, Any]:
    probe = textwrap.dedent(
        """
        import importlib
        import json
        import sys
        try:
            from importlib import metadata as importlib_metadata
        except Exception:
            import importlib_metadata  # type: ignore

        dist_name = sys.argv[1]
        import_name = sys.argv[2]

        try:
            module = importlib.import_module(import_name)
            version = None
            for candidate in (dist_name, import_name):
                try:
                    version = importlib_metadata.version(candidate)
                    break
                except Exception:
                    continue
            print(json.dumps({
                "import_ok": True,
                "version": version or getattr(module, "__version__", None),
                "notes": ""
            }, ensure_ascii=True))
        except Exception as exc:
            print(json.dumps({
                "import_ok": False,
                "error": exc.__class__.__name__,
                "notes": str(exc)[:500]
            }, ensure_ascii=True))
            raise SystemExit(1)
        """
    )
    result = run_command(
        [python_exec, "-c", probe, dist_name, import_name],
        cwd=ROOT,
        timeout_seconds=30,
    )
    payload = _decode_json((result.stdout or "").strip())
    if result.returncode == 0:
        payload.setdefault("import_ok", True)
        return payload

    if result.returncode == 124:
        return {
            "import_ok": False,
            "error": "ImportProbeTimeout",
            "notes": (result.stderr or "module import timed out").strip()[:500],
        }

    if result.returncode in (132, -4):
        return {
            "import_ok": False,
            "error": "IllegalInstruction",
            "notes": "module import terminated with illegal instruction",
        }

    if payload:
        payload.setdefault("import_ok", False)
        return payload

    return {
        "import_ok": False,
        "error": "ImportProbeFailed",
        "notes": (result.stderr or result.stdout or "").strip()[:500],
    }


def build_library_report(python_exec: str) -> Dict[str, Any]:
    packages = []
    conflicts = []
    for dist_name, import_name, optional in DEFAULT_PACKAGES:
        probe = probe_import(python_exec, dist_name, import_name)
        record = {
            "name": dist_name,
            "import_name": import_name,
            "import_ok": bool(probe.get("import_ok")),
            "version": probe.get("version"),
            "optional": optional,
            "notes": probe.get("notes", ""),
        }
        if probe.get("error"):
            record["error"] = probe["error"]
            if optional:
                conflicts.append(
                    "%s helper import failed at runtime: %s"
                    % (dist_name, probe["error"])
                )
        packages.append(record)

    cadquery_ok = any(item["name"] == "cadquery" and item["import_ok"] for item in packages)
    ocp_ok = any(item["name"] == "OCP" and item["import_ok"] for item in packages)
    pythonocc_ok = any(item["name"] == "pythonocc-core" and item["import_ok"] for item in packages)
    if pythonocc_ok:
        conflicts.append("pythonocc-core is present; keep it outside the default production baseline.")
    if cadquery_ok and not ocp_ok:
        conflicts.append("cadquery import succeeded without standalone OCP import proof.")

    required_failures = [item["name"] for item in packages if not item["optional"] and not item["import_ok"]]
    overall_status = "pass"
    if required_failures:
        overall_status = "fail"
    elif conflicts:
        overall_status = "partial"

    return {
        "generated_at": now_iso(),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "environment_path": python_exec,
        "packages": packages,
        "conflicts": conflicts,
        "overall_status": overall_status,
    }


def run_json_probe(python_exec: str, code: str) -> Dict[str, Any]:
    result = run_command([python_exec, "-c", code], cwd=ROOT, timeout_seconds=60)
    payload = _decode_json((result.stdout or "").strip())
    if result.returncode == 0 and payload:
        return payload
    if result.returncode == 124:
        return {
            "status": "fail",
            "errors": ["timeout"],
        }
    if result.returncode in (132, -4):
        return {
            "status": "fail",
            "errors": ["illegal_instruction"],
        }
    return {
        "status": "fail",
        "errors": [(result.stderr or result.stdout or "probe_failed").strip()[:500]],
    }


def brep_smoke(python_exec: str) -> Dict[str, Any]:
    code = textwrap.dedent(
        """
        import json
        import time
        started = time.monotonic()
        try:
            import cadquery as cq
            solid = cq.Workplane("XY").box(2, 3, 4).val()
            bb = solid.BoundingBox()
            payload = {
                "status": "pass",
                "mode": "BREP",
                "operations_tested": ["create_box", "bounding_box", "volume", "surface_area"],
                "metrics": {
                    "bbox": {
                        "min": [round(float(bb.xmin), 6), round(float(bb.ymin), 6), round(float(bb.zmin), 6)],
                        "max": [round(float(bb.xmax), 6), round(float(bb.ymax), 6), round(float(bb.zmax), 6)],
                        "size": [round(float(bb.xlen), 6), round(float(bb.ylen), 6), round(float(bb.zlen), 6)],
                    },
                    "volume": round(float(solid.Volume()), 6),
                    "surface_area": round(float(solid.Area()), 6),
                },
                "errors": [],
                "runtime_seconds": round(time.monotonic() - started, 6),
            }
        except Exception as exc:
            payload = {
                "status": "fail",
                "mode": "BREP",
                "operations_tested": ["create_box"],
                "metrics": {},
                "errors": [f"{exc.__class__.__name__}: {str(exc)[:240]}"],
                "runtime_seconds": round(time.monotonic() - started, 6),
            }
        print(json.dumps(payload, ensure_ascii=True))
        """
    )
    return run_json_probe(python_exec, code)


def mesh_smoke(python_exec: str) -> Dict[str, Any]:
    code = textwrap.dedent(
        """
        import json
        import time
        started = time.monotonic()
        try:
            import trimesh
            mesh = trimesh.creation.box(extents=(2, 3, 4))
            bounds = mesh.bounds.tolist()
            extents = mesh.extents.tolist()
            payload = {
                "status": "pass",
                "mode": "MESH_APPROX",
                "operations_tested": ["create_box", "bounding_box", "volume", "surface_area"],
                "metrics": {
                    "bbox": {
                        "min": [round(float(item), 6) for item in bounds[0]],
                        "max": [round(float(item), 6) for item in bounds[1]],
                        "size": [round(float(item), 6) for item in extents],
                    },
                    "volume": round(float(mesh.volume), 6) if mesh.is_volume else None,
                    "surface_area": round(float(mesh.area), 6),
                    "triangle_count": int(len(mesh.faces)),
                },
                "watertight": bool(mesh.is_watertight),
                "errors": [],
                "runtime_seconds": round(time.monotonic() - started, 6),
            }
        except Exception as exc:
            payload = {
                "status": "fail",
                "mode": "MESH_APPROX",
                "operations_tested": ["create_box"],
                "metrics": {},
                "watertight": False,
                "errors": [f"{exc.__class__.__name__}: {str(exc)[:240]}"],
                "runtime_seconds": round(time.monotonic() - started, 6),
            }
        print(json.dumps(payload, ensure_ascii=True))
        """
    )
    return run_json_probe(python_exec, code)


def geometry_contract_sample(brep_report: Dict[str, Any], mesh_report: Dict[str, Any]) -> Dict[str, Any]:
    if brep_report.get("status") == "pass":
        metrics = brep_report.get("metrics", {})
        bbox = metrics.get("bbox") if isinstance(metrics.get("bbox"), dict) else {}
        return build_geometry_metrics_payload(
            file_id="sample_or_test",
            mode=MODE_BREP,
            units="mm",
            bbox=bbox,
            volume=metrics.get("volume"),
            surface_area=metrics.get("surface_area"),
            part_count=1,
            triangle_count=None,
            source_type="brep_smoke",
            confidence=0.95,
        )

    metrics = mesh_report.get("metrics", {})
    bbox = metrics.get("bbox") if isinstance(metrics.get("bbox"), dict) else {}
    return build_geometry_metrics_payload(
        file_id="sample_or_test",
        mode=MODE_MESH_APPROX,
        units="mm",
        bbox=bbox,
        volume=metrics.get("volume"),
        surface_area=metrics.get("surface_area"),
        part_count=1,
        triangle_count=metrics.get("triangle_count"),
        source_type="mesh_smoke",
        confidence=0.78 if mesh_report.get("status") == "pass" else 0.2,
    )


def compatibility_decision(library_report: Dict[str, Any], brep_report: Dict[str, Any], mesh_report: Dict[str, Any]) -> Dict[str, Any]:
    package_state = {item["name"]: item for item in library_report.get("packages", [])}
    required_names = ["cadquery", "OCP", "trimesh", "meshio", "shapely", "networkx", "pyvista"]
    production_baseline = [name for name in required_names if package_state.get(name, {}).get("import_ok")]
    missing_required = [name for name in required_names if name not in production_baseline]
    optional_packages = [name for name in ("open3d",) if package_state.get(name, {}).get("import_ok")]
    rejected_packages = ["pythonocc-core"]
    known_conflicts = list(library_report.get("conflicts", []))
    if missing_required:
        known_conflicts.append("Missing required baseline imports: " + ", ".join(missing_required))

    final_recommendation = "PASS"
    if missing_required or brep_report.get("status") != "pass" or mesh_report.get("status") != "pass":
        final_recommendation = "PARTIAL" if mesh_report.get("status") == "pass" else "FAIL"

    return {
        "generated_at": now_iso(),
        "production_baseline_packages": production_baseline,
        "optional_packages": optional_packages,
        "rejected_packages": rejected_packages,
        "known_conflicts": known_conflicts,
        "why_cadquery_plus_ocp": "CadQuery + OCP remains the preferred B-Rep baseline for deterministic CAD metrics and future feature extraction.",
        "why_trimesh": "trimesh remains the mesh baseline for STL/OBJ primitives, watertight checks, and mesh_approx metrics.",
        "open3d_status": "approved_as_helper" if package_state.get("open3d", {}).get("import_ok") else "not_approved_in_runtime",
        "pythonocc_core_status": "rejected_from_default_baseline",
        "final_recommendation": final_recommendation,
    }


def summary_payload(
    discovery: Dict[str, Any],
    library_report: Dict[str, Any],
    brep_report: Dict[str, Any],
    mesh_report: Dict[str, Any],
    decision: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "generated_at": now_iso(),
        "environment": {
            "python_version": discovery.get("python_version"),
            "python_executable": discovery.get("python_executable"),
            "platform": discovery.get("platform"),
        },
        "imports_overall_status": library_report.get("overall_status"),
        "brep_status": brep_report.get("status"),
        "mesh_status": mesh_report.get("status"),
        "final_recommendation": decision.get("final_recommendation"),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate the STELLCODEX geometry stack.")
    parser.add_argument(
        "--output-dir",
        default=str(ROOT / "evidence" / ("geometry_stack_validation_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))),
        help="Directory where validation artifacts will be written.",
    )
    parser.add_argument(
        "--python",
        dest="python_exec",
        default=sys.executable,
        help="Python interpreter used for import and smoke validation.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    discovery = environment_discovery(args.python_exec)
    write_json(output_dir / "engineering_env_discovery.json", discovery)

    (output_dir / "engineering_pip_freeze.txt").write_text(pip_freeze(args.python_exec) + "\n", encoding="utf-8")
    installed_sections = []
    for dist_name, _import_name, _optional in DEFAULT_PACKAGES:
        installed_sections.append("## " + dist_name)
        installed_sections.append(pip_show(args.python_exec, dist_name))
        installed_sections.append("")
    (output_dir / "engineering_requirements_installed.txt").write_text("\n".join(installed_sections), encoding="utf-8")

    library_report = build_library_report(args.python_exec)
    write_json(output_dir / "engineering_library_report.json", library_report)

    brep_report = brep_smoke(args.python_exec)
    write_json(output_dir / "brep_smoke_report.json", brep_report)

    mesh_report = mesh_smoke(args.python_exec)
    write_json(output_dir / "mesh_smoke_report.json", mesh_report)

    sample = geometry_contract_sample(brep_report, mesh_report)
    write_json(output_dir / "geometry_metrics_sample.json", sample)

    decision = compatibility_decision(library_report, brep_report, mesh_report)
    write_json(output_dir / "geometry_stack_decision.json", decision)

    summary = summary_payload(discovery, library_report, brep_report, mesh_report, decision)
    write_json(output_dir / "engineering_stack_validation_summary.json", summary)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
