"""Base overlay 捕获后端（W04/N06）：hdmi_in 取帧 → vision_live_service。

一轮 = 一次新 read()（禁止复用上一帧）；prototype 结构性 = False（实时相机捕获，
C04 §3.2；FILE 后端恒 True）。read 失败（无视频/超时）归一为服务侧故障 → HTTP 503 且不产产物。

板上接线（NC 执行，板端脚本提供 read 与 overlay；取帧样板见 sim/scripts/n03_board_capture.py）：
    captures = BaseOverlayCaptures(<同步包装的 hdmi_in.readframe>)
    make_server(root=..., captures=captures,
                engine=file_engine(models/cnn-border-fill-best.pt, order, 0.8, 10), order=order)
要求：read() 返回 uint8 (720,1280,3) BGR（1280×720@60/30 源）；每轮必须重新取帧。
离板替身入口：sim/vision/test_base_captures.py（接入 run_vision_python.sh）。
"""
from pathlib import Path

import numpy as np

FRAME_SHAPE = (720, 1280, 3)


class BaseOverlayCaptures:
    backend = "BASE"
    prototype = False  # 实时相机捕获；离线产物代实时结果时才允许 true（C04 §3.2）

    def __init__(self, read, save=None):
        self.read = read
        self.seq = 0  # 软件 capture 序号（Q1）：frame_id 用，非 cop_frame_id
        self.save = save or self._save_png

    @staticmethod
    def _save_png(path, frame):
        import cv2
        from vision_live_service import atomic_write
        ok, data = cv2.imencode(".png", frame)
        if not ok:
            raise RuntimeError("base capture PNG encode failed")
        atomic_write(path, data.tobytes())

    def capture(self, round_dir):
        """一轮一次新取帧；read 失败（无视频/超时）抛 RuntimeError，调用方不产任何文件。"""
        try:
            frame = self.read()
        except OSError as error:
            raise RuntimeError(f"base capture failed: {error}") from error
        if (not isinstance(frame, np.ndarray) or frame.shape != FRAME_SHAPE
                or frame.dtype != np.uint8):
            raise RuntimeError("base capture frame geometry invalid")
        if not frame.flags["C_CONTIGUOUS"]:
            frame = np.ascontiguousarray(frame)
        path = Path(round_dir) / "capture.png"
        self.save(path, frame)
        self.seq = (self.seq + 1) & 0xFFFFFFFF
        return path
