from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "security" / "rbac.policy.json"

REQUIRED_ROLES = {"admin", "support", "moderator", "member"}


def fail(msg: str) -> None:
    print(f"RBAC VALIDATION FAILED: {msg}")
    sys.exit(1)


def main() -> None:
    if not POLICY_PATH.exists():
        fail(f"policy file not found: {POLICY_PATH}")

    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))

    perm_defs = policy.get("permission_definitions", [])
    perm_keys = [p.get("key") for p in perm_defs if isinstance(p, dict)]
    if any(k is None for k in perm_keys):
        fail("permission_definitions contains entries without key")

    # duplicate permission keys
    seen: set[str] = set()
    dupes: set[str] = set()
    for k in perm_keys:
        if k in seen:
            dupes.add(k)
        else:
            seen.add(k)
    if dupes:
        fail(f"duplicate permission keys: {', '.join(dupes)}")

    perm_set = set(perm_keys)

    roles = {
        r.get("name"): r.get("permissions", [])
        for r in policy.get("roles", [])
        if isinstance(r, dict)
    }

    missing_roles = [r for r in REQUIRED_ROLES if r not in roles]
    if missing_roles:
        fail(f"missing required roles: {', '.join(missing_roles)}")

    for role in sorted(REQUIRED_ROLES):
        perms = roles.get(role)
        if not isinstance(perms, list) or len(perms) == 0:
            fail(
                f"role '{role}' has empty permissions; fill docs/security/role-permission-template.md"
            )

        unknown = sorted({p for p in perms if p != "*" and p not in perm_set})
        if unknown:
            fail(
                f"role '{role}' references undefined permissions: {', '.join(unknown)}"
            )

    print("RBAC validation ok")


if __name__ == "__main__":
    main()
