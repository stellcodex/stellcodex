from __future__ import annotations

import json
from datetime import datetime, timezone
from types import SimpleNamespace
import unittest

from app.api.v1.routes.files import _serialize_file_out
from app.api.v1.routes.share import _serialize_share_resolve


BANNED_SUBSTRINGS = [
    "storage_key",
    "revision_id",
    "s3://",
    "r2://",
    "\"bucket\"",
    "'bucket'",
]


def _assert_no_banned_content(payload: dict) -> None:
    text = json.dumps(payload, ensure_ascii=True, default=str).lower()
    for banned in BANNED_SUBSTRINGS:
        if banned in text:
            raise AssertionError(f"public payload leaked banned token: {banned}")


class PublicContractLeakTests(unittest.TestCase):
    def test_file_out_does_not_leak_storage_key_or_bucket(self) -> None:
        file_row = SimpleNamespace(
            file_id="scx_file_11111111-1111-1111-1111-111111111111",
            original_filename="demo.step",
            content_type="application/step",
            size_bytes=12345,
            created_at=datetime.now(timezone.utc),
            status="ready",
            visibility="private",
            gltf_key="models/x/lod0.glb",
            thumbnail_key="thumb/x/thumb.png",
            meta={
                "kind": "3d",
                "mode": "brep",
                "assembly_meta_key": "metadata/x/assembly_meta.json",
                "preview_jpg_keys": ["previews/x/preview_1.jpg", "previews/x/preview_2.jpg", "previews/x/preview_3.jpg"],
                "decision_json": {"state_code": "S6"},
            },
        )
        payload = _serialize_file_out(file_row).model_dump()
        _assert_no_banned_content(payload)

    def test_share_resolve_does_not_leak_storage_key_or_bucket(self) -> None:
        file_row = SimpleNamespace(
            file_id="scx_file_22222222-2222-2222-2222-222222222222",
            status="ready",
            content_type="application/pdf",
            original_filename="doc.pdf",
            size_bytes=256,
            gltf_key=None,
        )
        share = SimpleNamespace(permission="download", expires_at=datetime.now(timezone.utc))
        payload = _serialize_share_resolve("token-abc", share, file_row).model_dump()
        _assert_no_banned_content(payload)


if __name__ == "__main__":
    unittest.main()
