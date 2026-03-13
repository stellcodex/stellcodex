from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path("/root/workspace")


class ReleaseGateContractTests(unittest.TestCase):
    def test_root_smoke_wrapper_execs_infra_smoke_script(self) -> None:
        payload = (ROOT / "scripts" / "smoke_test.sh").read_text(encoding="utf-8")
        self.assertIn("exec /root/workspace/stellcodex_v7/infrastructure/deploy/scripts/smoke_test.sh", payload)

    def test_root_restore_wrapper_execs_infra_restore_script(self) -> None:
        payload = (ROOT / "scripts" / "restore.sh").read_text(encoding="utf-8")
        self.assertIn("exec /root/workspace/stellcodex_v7/infrastructure/deploy/scripts/restore.sh", payload)

    def test_release_gate_keeps_smoke_and_restore_release_blocking(self) -> None:
        payload = (
            ROOT / "stellcodex_v7" / "infrastructure" / "deploy" / "scripts" / "release_gate_v7.sh"
        ).read_text(encoding="utf-8")
        self.assertIn('"${SCRIPT_DIR}/smoke_test.sh"', payload)
        self.assertIn('"${SCRIPT_DIR}/restore.sh"', payload)
        self.assertIn('"${SCRIPT_DIR}/drive_export.sh"', payload)
        self.assertIn('echo "[gate] PASS"', payload)

    def test_smoke_script_pins_share_and_approval_contracts(self) -> None:
        payload = (
            ROOT / "stellcodex_v7" / "infrastructure" / "deploy" / "scripts" / "smoke_v7.sh"
        ).read_text(encoding="utf-8")
        self.assertIn('share_expire_http', payload)
        self.assertIn('share_rate_limit_http', payload)
        self.assertIn('share_revoke_http', payload)
        self.assertIn('.state=="S7" and .approval_required==false', payload)
        self.assertIn('.state=="S4"', payload)

    def test_drive_export_script_generates_manifest_and_cleans_large_local_artifacts(self) -> None:
        payload = (
            ROOT / "stellcodex_v7" / "infrastructure" / "deploy" / "scripts" / "drive_export.sh"
        ).read_text(encoding="utf-8")
        self.assertIn('drive_export_manifest.json', payload)
        self.assertIn('drive_export_status.txt', payload)
        self.assertIn('rm -f "${DB_DUMP_PATH}"', payload)
        self.assertIn('rm -rf "${STORAGE_DIR}"', payload)


if __name__ == "__main__":
    unittest.main()
