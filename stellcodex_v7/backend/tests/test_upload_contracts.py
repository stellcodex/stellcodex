from __future__ import annotations

import unittest

from app.api.v1.routes.files import router as files_router
from app.api.v1.routes.product import router as product_router


class UploadContractsTests(unittest.TestCase):
    def test_canonical_upload_route_exists(self) -> None:
        paths = {route.path for route in files_router.routes}
        self.assertIn("/upload", paths)

    def test_legacy_upload_alias_exists(self) -> None:
        paths = {route.path for route in product_router.routes}
        self.assertIn("/upload", paths)


if __name__ == "__main__":
    unittest.main()
