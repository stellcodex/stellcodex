from __future__ import annotations

import argparse
import json
import os
from uuid import uuid4

os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test_stellcodex")
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-unit-tests-only-32chars!!")

from app.stellai.service import get_stellai_runtime
from app.stellai.types import RuntimeContext, RuntimeRequest


def main() -> int:
    parser = argparse.ArgumentParser(description="STELL-AI runtime smoke runner")
    parser.add_argument("--message", default="show runtime status")
    parser.add_argument("--tenant-id", default="1")
    parser.add_argument("--project-id", default="default")
    parser.add_argument("--session-id", default=f"smoke_{uuid4().hex[:12]}")
    parser.add_argument("--trace-id", default=str(uuid4()))
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    context = RuntimeContext(
        tenant_id=str(args.tenant_id),
        project_id=str(args.project_id),
        principal_type="smoke",
        principal_id="smoke-runner",
        session_id=str(args.session_id),
        trace_id=str(args.trace_id),
        allowed_tools=frozenset({"runtime.echo"}),
    )
    request = RuntimeRequest(
        message=str(args.message),
        context=context,
        top_k=max(1, args.top_k),
        tool_requests=[{"name": "runtime.echo", "params": {"message": "smoke"}}],
        metadata_filters={"project_id": str(args.project_id)},
    )
    result = get_stellai_runtime().run(request=request, db=None)
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
