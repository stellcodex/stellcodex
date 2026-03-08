from __future__ import annotations

import unittest

from app.api.v1.router import api_router
from app.api.v1.routes.share import MIN_SHARE_TOKEN_LENGTH, _generate_share_token
from app.main import app


class MasterContractRouteTests(unittest.TestCase):
    def test_required_contract_routes_exist(self) -> None:
        route_methods: dict[str, set[str]] = {}
        for route in api_router.routes:
            methods = {m for m in (route.methods or set()) if m not in {"HEAD", "OPTIONS"}}
            route_methods.setdefault(route.path, set()).update(methods)

        required = [
            ("GET", "/files/{file_id}/versions"),
            ("GET", "/files/{file_id}/decision_json"),
            ("POST", "/jobs"),
            ("GET", "/status/{file_id}"),
            ("POST", "/orchestrator/start"),
            ("POST", "/orchestrator/input"),
            ("POST", "/orchestrator/advance"),
            ("GET", "/orchestrator/session"),
            ("GET", "/orchestrator/decision"),
            ("POST", "/dfm/run"),
            ("GET", "/dfm/report"),
            ("POST", "/shares"),
            ("POST", "/approvals/{session_id}/approve"),
            ("POST", "/approvals/{session_id}/reject"),
        ]

        for method, path in required:
            self.assertIn(path, route_methods, f"missing path: {path}")
            self.assertIn(method, route_methods[path], f"missing method {method} for path: {path}")

    def test_share_token_length_policy(self) -> None:
        token = _generate_share_token()
        self.assertGreaterEqual(len(token), MIN_SHARE_TOKEN_LENGTH)

    def test_share_expiry_is_required_in_openapi(self) -> None:
        schema = app.openapi()
        paths = schema.get("paths", {})
        post_op = None
        for path, entry in paths.items():
            if not str(path).endswith("/shares"):
                continue
            if isinstance(entry, dict) and "post" in entry:
                post_op = entry["post"]
                break
        self.assertIsNotNone(post_op, "POST /shares operation not found in OpenAPI")

        body_schema = (
            (post_op or {})
            .get("requestBody", {})
            .get("content", {})
            .get("application/json", {})
            .get("schema", {})
        )
        if "$ref" in body_schema:
            ref = str(body_schema["$ref"]).split("/")[-1]
            body_schema = schema.get("components", {}).get("schemas", {}).get(ref, {})
        required = set(body_schema.get("required") or [])
        self.assertIn("expires_in_seconds", required)


if __name__ == "__main__":
    unittest.main()
