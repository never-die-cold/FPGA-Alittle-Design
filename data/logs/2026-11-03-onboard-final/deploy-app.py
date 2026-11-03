"""Stage current board Python inputs in a new app directory, keeping older apps."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "sim/scripts"))
from board_ssh import connect, upload

stage = ROOT / "sim/build/onboard-final/app"
remote = "/home/xilinx/cop-app-final-20261103-62324fe"
files = sorted((ROOT / "src/pynq_host").glob("*.py"))
files += [ROOT / "sim/vision/localization_opencv.py",
          Path(__file__).with_name("start-service.sh")]
stage.mkdir(parents=True, exist_ok=False)
manifest = []
for source in files:
    relative = (Path("start-service.sh") if source.name == "start-service.sh"
                else source.relative_to(ROOT))
    target = stage / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    raw = source.read_bytes()
    target.write_bytes(raw)
    manifest.append({"path": relative.as_posix(), "sha256": hashlib.sha256(raw).hexdigest()})
(stage / "sources.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
client = connect()
try:
    sftp = client.open_sftp()
    try:
        sftp.stat(remote)
    except FileNotFoundError:
        pass
    else:
        raise RuntimeError("choose a new app path; existing app preserved")
    upload(client, stage, remote)
    for row in manifest:
        with sftp.open(remote + "/" + row["path"], "rb") as stream:
            assert hashlib.sha256(stream.read()).hexdigest() == row["sha256"]
    sftp.close()
    print(f"DEPLOYED new_app={remote} verified_files={len(manifest)}")
finally:
    client.close()
