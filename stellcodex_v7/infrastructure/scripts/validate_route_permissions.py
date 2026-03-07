from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "security" / "rbac.policy.json"
ROUTE_MAP_PATH = ROOT / "frontend" / "src" / "security" / "route-permissions.json"
BLOCKING = "BLOCKING_PERM_KEY_REQUIRED"


def fail(msg: str) -> None:
    print(f"RBAC ROUTE VALIDATION FAILED: {msg}")
    sys.exit(1)


def main() -> None:
    if not POLICY_PATH.exists():
        fail(f"policy file not found: {POLICY_PATH}")
    if not ROUTE_MAP_PATH.exists():
        fail(f"route permissions map not found: {ROUTE_MAP_PATH}")

    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    perm_defs = policy.get("permission_definitions", [])
    perm_keys = [p.get("key") for p in perm_defs if isinstance(p, dict)]
    if any(k is None for k in perm_keys):
        fail("permission_definitions contains entries without key")

    perm_set = set(perm_keys)

    route_map = json.loads(ROUTE_MAP_PATH.read_text(encoding="utf-8"))
    if not isinstance(route_map, dict):
        fail("route-permissions.json must be an object map of route -> permission")

    missing = [route for route, perm in route_map.items() if perm == BLOCKING]
    if missing:
        missing_sorted = ", ".join(sorted(missing))
        fail(
            "missing permission keys for routes: "
            + missing_sorted
            + ". Update frontend/src/security/route-permissions.json"
        )

    unknown = sorted({perm for perm in route_map.values() if perm not in perm_set and perm != "*"})
    if unknown:
        fail("undefined permissions referenced in route map: " + ", ".join(unknown))

    print("RBAC route permissions ok")


if __name__ == "__main__":
    main()
