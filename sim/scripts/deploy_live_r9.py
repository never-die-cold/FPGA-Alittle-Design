"""Stage the reviewed r9 development candidate without touching older packages."""
import hashlib
import json
from pathlib import Path
import sys
from board_ssh import connect, upload

ROOT = Path(__file__).resolve().parents[2]
stage = ROOT / "sim/build/r9-app-stage"
stage.mkdir(parents=True, exist_ok=False)
files = list((ROOT / "src/pynq_host").glob("*.py")) + [ROOT / "sim/vision/localization_opencv.py"]
rows = []
for source in files:
    path = source.relative_to(ROOT)
    target = stage / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(source.read_bytes())
    rows.append({"path":path.as_posix(),"sha256":hashlib.sha256(target.read_bytes()).hexdigest()})
(stage / "sources.json").write_text(json.dumps(rows,indent=2),encoding="utf-8")
client = connect()
try:
    sftp = client.open_sftp()
    for local,remote in [(stage,"/home/xilinx/cop-app-r9-20261103"),
                          (ROOT / "sim/build/cnn-r9-board-package","/home/xilinx/cop-pkg-r9-20261103")]:
        try:
            sftp.stat(remote)
        except FileNotFoundError:
            pass
        else:
            raise RuntimeError("existing target preserved: " + remote)
        upload(client,local,remote)
        for path in local.rglob("*"):
            if path.is_file():
                with sftp.open(remote+"/"+path.relative_to(local).as_posix(),"rb") as stream:
                    assert hashlib.sha256(stream.read()).digest() == hashlib.sha256(path.read_bytes()).digest()
    sftp.close()
    print("PASS: isolated r9 app/package uploaded and every file hash checked")
finally:
    client.close()
