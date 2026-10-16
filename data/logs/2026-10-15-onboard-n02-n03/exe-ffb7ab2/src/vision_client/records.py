"""批次记录存储（EXE 侧，M3 起步）——决策单 D8–D10；W07 起 schema v2。

规则：
- D8 只有手动触发的轮次是记录候选；自动间隔轮次永不落记录
  （结构性满足 M3"重复帧不增加批次计数"）。
- D9 记录键 = (session_id, check_id)，同键重复写入被拒（一次确认的检查只记一条）。
- D10 存储 = records.jsonl（一行一条）+ screenshots/ 逐条截图。截图前缀标来源
  （C04 §3.2/Q2）：MOCK=`mock_`；LIVE+prototype=`proto_`（离线产物代实时结果）；
  真实 LIVE 无前缀——三者不得互换使用（plan.md §3.4）。
- v2 新增（W07，C04 §5）：status（报文 status 原文）、decision（工单判定原样，
  含 expected/actual/delta/missing/extra/reasons——当轮工单即 decision.expected）、
  prototype（来源标识）、protocol_version（报文契约版本）；替代 v1 的 verdict
  预留字段（该字段误读顶层 verdict，对 v1.2 报文恒为 None）。
  result_age_s 按 EXE 接收时基传入（age_s），created_at 保留原始服务端时间戳供诊断。
- 重启安全（2026-10-13，NC 点名）：BatchRecords 启动时从既有 records.jsonl 重建去重键与计数；
  AnomalyLog 按既有行数续编截图序号（防 anomaly_*.png 覆盖）；损坏记录行大声失败——
  静默跳过会让去重失效、重复证据被写入。

截图写入通过注入的 save_image(path, frame) 回调完成；缺省惰性导入 cv2（EXE 内可用），
离线测试传桩函数以保持纯 stdlib。
"""
import json
import time
from datetime import datetime
from pathlib import Path

SCHEMA_VERSION = 2


def source_prefix(mode, prototype=False):
    """截图前缀 = 来源标识：MOCK → mock_；LIVE+prototype → proto_；真实 LIVE → 空。"""
    if mode == "MOCK":
        return "mock_"
    return "proto_" if prototype else ""


class BatchRecords:
    """记录目录内的追加式批次存储；去重键跨进程有效（启动时从 records.jsonl 重建）。"""

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
        self._rebuild()

    def _rebuild(self):
        """重启恢复：从既有 records.jsonl 重建去重键与计数（D9 键跨进程仍有效）。"""
        path = self.dir / "records.jsonl"
        if not path.exists():
            return
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
                self.keys.add((row["session_id"], row["check_id"]))
            except (ValueError, KeyError, TypeError) as error:
                raise ValueError(f"corrupt records line {lineno}: {error}") from error
            self.count += 1

    def accept(self, packet):
        return (packet["session_id"], packet["check_id"]) not in self.keys

    def write(self, packet, frame, age_s=None):
        """落一条记录（jsonl 行 + 截图）；重复键返回 None，不抛异常。

        age_s 为 EXE 接收时基的结果年龄（调用方传入）；缺省回退 created_at 差值。
        """
        key = (packet["session_id"], packet["check_id"])
        if key in self.keys:
            return None
        prefix = source_prefix(packet["mode"], bool(packet.get("prototype", False)))
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
            "result_age_s": round(age_s if age_s is not None else time.time() - packet["created_at"], 3),
            "created_at": packet["created_at"],
            "protocol_version": packet["version"],
            "target_count": len(packet["targets"]),
            "targets": packet["targets"],
            "status": packet["status"],
            "decision": packet.get("decision"),
            "prototype": bool(packet.get("prototype", False)),
            "screenshot": f"screenshots/{name}",
        }
        with (self.dir / "records.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        self.keys.add(key)
        self.count += 1
        return shot


class AnomalyLog:
    """异常事件追加日志（D11）：anomalies.jsonl 一行一事件 + screenshots/anomaly_*.png。

    事件种类来自 rounds.RemoteRounds.drain_events()：overlay_*（状态迁移，含恢复的
    overlay_ok）/ session_changed / rehandshake_failed。与批次记录共用目录，导出即整体。
    """

    def __init__(self, directory, save_image=None):
        if save_image is None:
            import cv2
            save_image = lambda path, frame: bool(cv2.imwrite(str(path), frame))
        self.dir = Path(directory)
        self.shots = self.dir / "screenshots"
        self.shots.mkdir(parents=True, exist_ok=True)
        self.save_image = save_image
        self.count = 0
        path = self.dir / "anomalies.jsonl"
        if path.exists():
            self.count = sum(1 for line in path.read_text(encoding="utf-8").splitlines()
                             if line.strip())

    def log(self, mode, event, frame, prototype=False):
        prefix = source_prefix(mode, prototype)
        name = f"{prefix}anomaly_{self.count + 1:04d}.png"
        shot = self.shots / name
        if not self.save_image(shot, frame):
            raise RuntimeError(f"anomaly screenshot write failed: {shot}")
        row = {
            "schema_version": SCHEMA_VERSION,
            "mode": mode,
            "prototype": bool(prototype),
            "recorded_at": datetime.now().isoformat(timespec="seconds"),
            "kind": event.get("kind"),
            "prev": event.get("prev"),
            "check_id": event.get("check_id"),
            "fails": event.get("fails"),
            "screenshot": f"screenshots/{name}",
        }
        with (self.dir / "anomalies.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        self.count += 1
        return shot
