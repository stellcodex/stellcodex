# Engineering Stack Validation

This document locks the geometry-analysis foundation used by STELLCODEX.

## Scope

The production baseline is layered:

- Primary B-Rep/CAD baseline: `cadquery` + `OCP`
- Primary mesh baseline: `trimesh` + `meshio`
- Support libraries: `shapely`, `networkx`, `pyvista`
- Optional helper: `open3d`

`pythonocc-core` is not part of the default production baseline. It may be evaluated only after a concrete missing-capability proof.

## Product Context

This stack supports the core platform layer shared by:

- StellView
- StellShare
- StellDoc
- StellMesh
- MoldCodes
- STELL-AI

The geometry foundation exists to unlock:

- geometry metrics
- feature extraction
- deterministic manufacturing analysis
- DFM reporting

It does not replace the V7 deterministic decision boundary.

## Validation Flow

Run the validation script from the backend root:

```bash
python3 scripts/validate_geometry_stack.py --output-dir /root/workspace/evidence/geometry_stack_validation_manual
```

The script generates:

- `engineering_env_discovery.json`
- `engineering_requirements_installed.txt`
- `engineering_pip_freeze.txt`
- `engineering_library_report.json`
- `brep_smoke_report.json`
- `mesh_smoke_report.json`
- `geometry_metrics_sample.json`
- `geometry_stack_decision.json`
- `engineering_stack_validation_summary.json`

## Expected Decisions

- `cadquery + OCP` remains the preferred B-Rep baseline.
- `trimesh` remains the preferred mesh baseline.
- `open3d` stays helper-only unless runtime proof says otherwise.
- `pythonocc-core` stays outside the default baseline.
