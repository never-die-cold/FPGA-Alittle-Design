"""Offline SSH trust configuration and safe loading of the current r6 checkpoint."""
from pathlib import Path
import runpy
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
ssh = runpy.run_path(str(ROOT / "sim/scripts/board_ssh.py"))
with patch("paramiko.SSHClient") as client, patch.dict("os.environ", {"BOARD_KNOWN_HOSTS": "pinned-hosts"}):
    ssh["connect"]()
    obj = client.return_value
    obj.load_system_host_keys.assert_called_once()
    obj.load_host_keys.assert_called_once_with("pinned-hosts")
    assert type(obj.set_missing_host_key_policy.call_args.args[0]).__name__ == "RejectPolicy"
    obj.connect.assert_called_once()
export = runpy.run_path(str(ROOT / "sim/scripts/export_trained_payload.py"))
model, meta = export["load_weights"](ROOT / "data/evidence/2026-10-28-cnn-r6/fp32.pt")
assert tuple(meta["classes"]) == ("bolt", "nut", "washer")
assert not model.training
print("PASS: SSH verifies known hosts; current r6 checkpoint loads with weights_only=True")
