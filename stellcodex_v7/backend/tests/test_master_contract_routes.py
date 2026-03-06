from __future__ import annotations

import unittest

from app.api.v1.router import api_router
from app.api.v1.routes.share import MIN_SHARE_TOKEN_LENGTH, _generate_share_token


class MasterContractRouteTests(unittest.TestCase):
    def test_required_contract_routes_exist(self) -> None:
        route_methods: dict[str, set[str]] = {}
        for route in api_router.routes:
            methods = {m for m in (route.methods or set()) if m not in {"HEAD", "OPTIONS"}}
            route_methods.setdefault(route.path, set()).update(methods)

        required = [
            ("GET", "/files/{file_id}/versions"),
            ("POST", "/jobs"),
            ("GET", "/status/{file_id}"),
            ("POST", "/orchestrator/start"),
            ("POST", "/orchestrator/input"),
            ("POST", "/orchestrator/advance"),
            ("GET", "/orchestrator/session"),
            ("POST", "/dfm/run"),
            ("GET", "/dfm/report"),
            ("POST", "/shares"),
        ]

        for method, path in required:
            self.assertIn(path, route_methods, f"missing path: {path}")
            self.assertIn(method, route_methods[path], f"missing method {method} for path: {path}")

    def test_share_token_length_policy(self) -> None:
        token = _generate_share_token()
        self.assertGreaterEqual(len(token), MIN_SHARE_TOKEN_LENGTH)


if __name__ == "__main__":
    unittest.main()
