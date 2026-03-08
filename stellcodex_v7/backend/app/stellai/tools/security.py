from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from app.stellai.types import RuntimeContext


@dataclass(frozen=True)
class PathValidationResult:
    allowed: bool
    path: Path | None
    tenant_root: Path
    reason: str | None = None


class ToolSecurityPolicy:
    def __init__(
        self,
        *,
        base_root: str | Path | None = None,
        denied_roots: Iterable[str | Path] | None = None,
    ) -> None:
        configured_root = base_root or os.getenv("STELLAI_TOOL_FS_ROOT") or "/root/workspace/evidence/stellai/tenant_fs"
        self.base_root = Path(configured_root).resolve()
        default_denied = (
            "/etc",
            "/proc",
            "/sys",
            "/dev",
            "/boot",
            "/usr",
            "/bin",
            "/sbin",
            "/lib",
            "/lib64",
            "/root/.ssh",
            "/var/lib",
        )
        denied = denied_roots or default_denied
        self.denied_roots = tuple(Path(item).resolve() for item in denied)

    def tenant_root(self, context: RuntimeContext) -> Path:
        tenant_id = str(context.tenant_id or "").strip()
        if not tenant_id:
            tenant_id = "0"
        root = self.base_root / f"tenant_{tenant_id}"
        root.mkdir(parents=True, exist_ok=True)
        return root.resolve()

    def allowed_roots(self, context: RuntimeContext) -> tuple[str, ...]:
        tenant_root = self.tenant_root(context)
        return (str(tenant_root),)

    def validate_path(
        self,
        *,
        context: RuntimeContext,
        raw_path: str,
        for_write: bool = False,
        expect_directory: bool = False,
        must_exist: bool = True,
    ) -> PathValidationResult:
        tenant_root = self.tenant_root(context)
        candidate = str(raw_path or "").strip()
        if not candidate:
            return PathValidationResult(allowed=False, path=None, tenant_root=tenant_root, reason="missing_path")

        candidate_path = Path(candidate)
        resolved = (candidate_path if candidate_path.is_absolute() else tenant_root / candidate_path).resolve()

        for denied in self.denied_roots:
            if resolved == denied or denied in resolved.parents:
                return PathValidationResult(
                    allowed=False,
                    path=resolved,
                    tenant_root=tenant_root,
                    reason="forbidden_path",
                )

        if not _is_relative_to(resolved, tenant_root):
            return PathValidationResult(
                allowed=False,
                path=resolved,
                tenant_root=tenant_root,
                reason="path_outside_tenant_root",
            )

        if must_exist and not resolved.exists():
            return PathValidationResult(
                allowed=False,
                path=resolved,
                tenant_root=tenant_root,
                reason="path_not_found",
            )

        if expect_directory and resolved.exists() and not resolved.is_dir():
            return PathValidationResult(
                allowed=False,
                path=resolved,
                tenant_root=tenant_root,
                reason="not_a_directory",
            )

        if not expect_directory and resolved.exists() and resolved.is_dir() and not for_write:
            return PathValidationResult(
                allowed=False,
                path=resolved,
                tenant_root=tenant_root,
                reason="not_a_file",
            )

        if for_write:
            parent = resolved if expect_directory else resolved.parent
            parent.mkdir(parents=True, exist_ok=True)

        return PathValidationResult(allowed=True, path=resolved, tenant_root=tenant_root)



def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False
