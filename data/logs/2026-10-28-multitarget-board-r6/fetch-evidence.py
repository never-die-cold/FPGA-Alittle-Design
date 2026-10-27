"""Read-only export of the completed board runs and the final LIVE round."""
import hashlib
import json
from pathlib import Path
import stat
import sys

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]
sys.path.insert(0, str(ROOT / "sim/scripts"))
from board_ssh import connect

output = RUN / "board-evidence"
output.mkdir(exist_ok=False)
client = connect()
sftp = client.open_sftp()
files = []


def fetch(remote, local):
    local.mkdir(parents=True, exist_ok=True)
    for item in sftp.listdir_attr(remote):
        if Path(item.filename).name != item.filename or item.filename in (".", ".."):
            raise ValueError("unsafe remote filename")
        source, target = remote+"/"+item.filename, local/item.filename
        if stat.S_ISDIR(item.st_mode):
            fetch(source, target)
        elif stat.S_ISREG(item.st_mode):
            sftp.get(source, str(target))
            files.append({"source": source, "path": target.relative_to(RUN).as_posix(),
                          "bytes": target.stat().st_size,
                          "sha256": hashlib.sha256(target.read_bytes()).hexdigest()})


try:
    for remote, name in (("cop-board-r6-20261028", "attempt-0"),
                         ("cop-board-r6-20261028-r1", "attempt-1"),
                         ("cop-board-r6-20261028-r2", "numeric-pass"),
                         ("cop-live-r6-20261028", "live")):
        fetch("/home/xilinx/"+remote, output/name)
    (output/"manifest.json").write_text(json.dumps({"files": files}, indent=2)+"\n", encoding="utf-8")
    print(f"BOARD_EVIDENCE_FETCHED files={len(files)} bytes={sum(f['bytes'] for f in files)}")
finally:
    sftp.close()
    client.close()
