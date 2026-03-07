from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "security" / "rbac.policy.json"
OUT_DIR = ROOT / "backend" / "app" / "security"
REQUIRED_ROLES = {"admin", "support", "moderator", "user"}


def _ensure_roles_ready(policy: dict) -> None:
    roles = {
        r.get("name"): r.get("permissions", [])
        for r in policy.get("roles", [])
        if isinstance(r, dict)
    }
    missing = [r for r in REQUIRED_ROLES if r not in roles]
    if missing:
        print(f"RBAC generation blocked: missing roles {', '.join(missing)}")
        sys.exit(1)
    empty = [r for r in REQUIRED_ROLES if not roles.get(r)]
    if empty:
        print(
            "RBAC generation blocked: empty role permissions for "
            + ", ".join(empty)
            + ". Fill docs/security/role-permission-template.md"
        )
        sys.exit(1)


def main() -> None:
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    _ensure_roles_ready(policy)
    api = policy.get("api_endpoint_permissions", [])
    critical = [
        {"method": e["method"], "path": e["path"], "perm": e["perm"]}
        for e in api
        if e.get("approval_required") is True
    ]

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    (OUT_DIR / "api-perms.generated.json").write_text(
        json.dumps(api, indent=2),
        encoding="utf-8",
    )
    (OUT_DIR / "critical-endpoints.generated.json").write_text(
        json.dumps(critical, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
