"""批次记录存储（EXE 侧，M3 起步）——决策单 D8–D10。

规则：
- D8 只有手动触发的轮次是记录候选；自动间隔轮次永不落记录
  （结构性满足 M3"重复帧不增加批次计数"）。
- D9 记录键 = (session_id, check_id)，同键重复写入被拒（一次确认的检查只记一条）。
- D10 存储 = records.jsonl（一行一条）+ screenshots/ 逐条截图；MOCK 模式截图带
  `mock_` 前缀且记录含 mode 字段——不得用作板上识别证据（plan.md §3.4）。

截图写入通过注入的 save_image(path, frame) 回调完成；缺省惰性导入 cv2（EXE 内可用），
离线测试传桩函数以保持纯 stdlib。
"""
import json
import time
from datetime import datetime
from pathlib import Path

SCHEMA_VERSION = 1


class BatchRecords:
    """记录目录内的追加式批次存储；进程内按键去重。"""

    def __init__(self, directory, save_image=None):
        if save_image is None:
            import cv2
            save_image = lambda path, frame: bool(cv2.imwrite(str(path), frame))
        self.dir = Path(directory)
        self.shots = self.dir / "screenshots"
        self.shots.mkdir(parents=True, exist_ok=True)
        self.save_image = save_image
        self.keys = set()
        self.count = 0

    def accept(self, packet):
        return (packet["session_id"], packet["check_id"]) not in self.keys

    def write(self, packet, frame):
        """落一条记录（jsonl 行 + 截图）；重复键返回 None，不抛异常。"""
        key = (packet["session_id"], packet["check_id"])
        if key in self.keys:
            return None
        prefix = "mock_" if packet["mode"] == "MOCK" else ""
        name = f"{prefix}{packet['session_id'][:8]}_{packet['check_id']:06d}.png"
        shot = self.shots / name
        if not self.save_image(shot, frame):
            raise RuntimeError(f"screenshot write failed: {shot}")
        row = {
            "schema_version": SCHEMA_VERSION,
            "mode": packet["mode"],
            "session_id": packet["session_id"],
            "check_id": packet["check_id"],
            "config_id": packet["config_id"],
            "frame_id": packet["frame_id"],
            "recorded_at": datetime.now().isoformat(timespec="seconds"),
            "result_age_s": round(time.time() - packet["created_at"], 3),
            "target_count": len(packet["targets"]),
            "targets": packet["targets"],
            "verdict": packet.get("verdict"),  # M3 工单判定预留
            "screenshot": f"screenshots/{name}",
        }
        with (self.dir / "records.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        self.keys.add(key)
        self.count += 1
        return shot
