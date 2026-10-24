"""按 (session_id, check_id) 读取与核对轮次产物（C04 §2.3 快照方案，待 NC 确认）。

产物布局（vision_live_service 写）：
  <root>/<session_id[:8]>/check-NNNNNN/capture.png     权威快照（本轮原帧副本）
  <root>/<session_id[:8]>/check-NNNNNN/capture.sha256  capture.png 字节哈希（侧车）
  <root>/<session_id[:8]>/check-NNNNNN/packet.json     v1.2 报文（原子落盘）
  <root>/<session_id[:8]>/check-NNNNNN/chkNNNNNN/      引擎产物（inspection_run，可选）
  <root>/<session_id[:8]>/check-NNNNNN/cop_trace.json  MMIO 引擎证据（可选，含 ROI 哈希链）

核对链：packet 白名单校验与 (session, check) 绑定 → capture.png 字节哈希 == capture.sha256
→ 若有 cop_trace.json，解码像素哈希、decision 绑定和每个 ROI 的字节哈希均一致
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
        _verify_rois(engine_path.parent, engine_result)
    cop_trace = None
    trace_path = path / "cop_trace.json"
    if trace_path.is_file():
        try:
            cop_trace = json.loads(trace_path.read_text(encoding="utf-8"))
        except ValueError as error:
            raise SnapshotError(f"cop trace invalid: {error}") from error
        _verify_cop_trace(path, cop_trace, packet)
    return {"capture": capture_path, "packet": packet, "sha256": digest,
            "engine_result": engine_result, "cop_trace": cop_trace}


def _pixels_sha256(capture_path):
    import cv2
    import numpy as np
    raw = Path(capture_path).read_bytes()
    pixels = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
    if pixels is None:
        raise SnapshotError("capture is not a decodable color image")
    return hashlib.sha256(pixels.tobytes()).hexdigest()


def _verify_cop_trace(root, trace, packet):
    """MMIO trace chain: capture pixels -> ROI bytes -> packet decision."""
    if not isinstance(trace, dict):
        raise SnapshotError("cop trace is not an object")
    frame = trace.get("frame")
    if not isinstance(frame, dict) or (frame.get("width"), frame.get("height")) != \
            (packet["width"], packet["height"]):
        raise SnapshotError("cop trace frame metadata mismatch")
    expected_pixels = _pixels_sha256(root / "capture.png")
    if frame.get("pixel_sha256") != expected_pixels:
        raise SnapshotError("cop trace pixel hash mismatch")
    kind = trace.get("kind")
    if kind == "cop_job":
        if trace.get("decision") != packet.get("decision"):
            raise SnapshotError("cop trace decision differs from packet")
        if len(trace.get("rois") or []) != len(packet["targets"]):
            raise SnapshotError("cop trace ROI count differs from packet")
        _verify_roi_files(root, trace["rois"])
    elif kind == "cop_failure":
        _verify_roi_files(root, trace.get("rois") or [])
    elif kind == "target_limit":
        if packet["status"] != "RECHECK" or "target_limit" not in \
                (packet.get("decision") or {}).get("reasons", []):
            raise SnapshotError("target_limit trace does not match packet")
    elif kind == "empty_scene_ps_gate":
        if packet["status"] != "CHECK_FAIL" or packet["targets"]:
            raise SnapshotError("empty-scene trace does not match packet")
    else:
        raise SnapshotError(f"unknown cop trace kind {kind!r}")


def _verify_roi_files(root, rois):
    resolved = Path(root).resolve()
    for item in rois:
        relative, expected = item.get("path"), item.get("bytes_sha256")
        if not relative or not expected:
            raise SnapshotError("cop ROI entry lacks path/hash")
        path = (Path(root) / relative).resolve()
        if not path.is_relative_to(resolved):
            raise SnapshotError("cop ROI path escapes the round directory")
        if not path.is_file():
            raise SnapshotError("missing cop ROI artifact")
        data = path.read_bytes()
        if len(data) != 4096 or hashlib.sha256(data).hexdigest() != expected:
            raise SnapshotError("cop ROI hash mismatch")


def _verify_rois(engine_dir, engine_result):
    """逐目标 ROI 像素哈希链（NC 10-14 Q3 细则）：文件在引擎目录内、解码像素哈希一致。"""
    root = engine_dir.resolve()
    for target in engine_result.get("targets", []):
        relative = target.get("roi_path")
        expected = target.get("roi_pixels_sha256")
        if not relative or not expected:
            raise SnapshotError("engine target lacks ROI artifact reference")
        roi_path = (engine_dir / relative).resolve()
        if not roi_path.is_relative_to(root):
            raise SnapshotError("ROI path escapes engine artifacts")
        if not roi_path.is_file():
            raise SnapshotError("missing ROI artifact")
        import cv2
        import numpy as np
        pixels = cv2.imdecode(np.frombuffer(roi_path.read_bytes(), np.uint8),
                              cv2.IMREAD_UNCHANGED)
        if pixels is None or hashlib.sha256(pixels.tobytes()).hexdigest() != expected:
            raise SnapshotError("ROI hash mismatch")


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
