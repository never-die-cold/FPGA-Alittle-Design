"""按 (session_id, check_id) 读取与核对轮次产物（C04 §2.3 快照方案，待 NC 确认）。

产物布局（vision_live_service 写）：
  <root>/<session_id[:8]>/check-NNNNNN/capture.png     权威快照（本轮原帧副本）
  <root>/<session_id[:8]>/check-NNNNNN/capture.sha256  capture.png 字节哈希（侧车）
  <root>/<session_id[:8]>/check-NNNNNN/packet.json     v1.2 报文（原子落盘）
  <root>/<session_id[:8]>/check-NNNNNN/chkNNNNNN/      引擎产物（inspection_run，可选）

核对链：packet 白名单校验与 (session, check) 绑定 → capture.png 字节哈希 == capture.sha256
→ 若有引擎 result.json，其 provenance.source_sha256 与 capture 哈希一致。任一不符大声失败。
读取不修改任何文件；本核对只证明“产物未被改动”，不证明来源真实性（无签名）。
CLI：py src/pynq_host/round_artifacts.py <root> <session_id> <check_id>
"""
import hashlib
import json
from pathlib import Path

from vision_protocol import validate_packet


class SnapshotError(ValueError):
    pass


def round_dir(root, session_id, check_id):
    return Path(root) / session_id[:8] / f"check-{check_id:06d}"


def load_snapshot(root, session_id, check_id):
    """返回 {"capture", "packet", "sha256", "engine_result"}；校验失败抛 SnapshotError。"""
    path = round_dir(root, session_id, check_id)
    packet_path = path / "packet.json"
    capture_path = path / "capture.png"
    sha_path = path / "capture.sha256"
    for required in (packet_path, capture_path, sha_path):
        if not required.is_file():
            raise SnapshotError(f"missing artifact: {required}")
    try:
        packet = validate_packet(json.loads(packet_path.read_text(encoding="utf-8")))
    except ValueError as error:
        raise SnapshotError(f"packet invalid: {error}") from error
    if packet["session_id"] != session_id or packet["check_id"] != check_id:
        raise SnapshotError("packet does not match requested round")
    digest = hashlib.sha256(capture_path.read_bytes()).hexdigest()
    if digest != sha_path.read_text(encoding="ascii").strip():
        raise SnapshotError("capture hash mismatch")
    engine_result = None
    engine_path = path / f"chk{check_id:06d}" / "result.json"
    if engine_path.is_file():
        engine_result = json.loads(engine_path.read_text(encoding="utf-8"))
        source = engine_result.get("provenance", {}).get("source_sha256")
        if source != digest:
            raise SnapshotError("engine source hash mismatch")
    return {"capture": capture_path, "packet": packet, "sha256": digest,
            "engine_result": engine_result}


if __name__ == "__main__":
    import argparse
    import sys
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root")
    parser.add_argument("session_id")
    parser.add_argument("check_id", type=int)
    main_args = parser.parse_args()
    try:
        snapshot = load_snapshot(main_args.root, main_args.session_id, main_args.check_id)
    except SnapshotError as error:
        print(f"FAIL: {error}")
        sys.exit(1)
    print(f"PASS: snapshot verified {snapshot['capture']} sha256={snapshot['sha256']}")
