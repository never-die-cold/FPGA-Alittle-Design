"""Fetch exact trace/capture evidence for a host-recorded LIVE round batch."""
import argparse
import hashlib
import json
from pathlib import Path

from board_ssh import connect


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rounds", type=Path, required=True)
    parser.add_argument("--remote-root", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[2]
    if repo not in args.output.resolve().parents:
        parser.error("output must stay inside this repository")
    packets = [json.loads(p.read_text()) for p in sorted(args.rounds.glob("round-*.json"))]
    packets = [p for p in packets if "check_id" in p]
    if not packets:
        parser.error("no recorded packet to fetch")
    args.output.mkdir(parents=True, exist_ok=False)
    client = connect()
    manifest = []
    try:
        sftp = client.open_sftp()
        for index, packet in enumerate(packets):
            remote = args.remote_root.rstrip("/") + "/" + packet["session_id"][:8]
            remote += f"/check-{packet['check_id']:06d}"
            names = ["cop_trace.json", "capture-dma.json", "packet.json"]
            if index in (0, len(packets)-1):
                names += ["capture.png", "capture.sha256"]
            local = args.output / f"check-{packet['check_id']:06d}"
            local.mkdir()
            for name in names:
                with sftp.open(remote + "/" + name, "rb") as stream:
                    raw = stream.read()
                (local / name).write_bytes(raw)
                manifest.append({"source":remote+"/"+name,
                                 "path":str((local/name).relative_to(args.output)),
                                 "sha256":hashlib.sha256(raw).hexdigest()})
            assert json.loads((local / "packet.json").read_bytes()) == packet
            if (local / "capture.png").is_file():
                assert hashlib.sha256((local / "capture.png").read_bytes()).hexdigest() == \
                    (local / "capture.sha256").read_text().strip()
        sftp.close()
        (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2)+"\n", encoding="utf-8")
        print(f"PASS: {len(packets)} exact packets/traces and representative snapshots fetched")
    finally:
        client.close()


if __name__ == "__main__":
    main()
