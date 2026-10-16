"""C01 捕获后端适配（W04）：SingleFrameCapture → vision_live_service。

一轮 = 一个单次所有权租约：factory() 现场构造 SingleFrameCapture（单次使用），capture() 返回
独立完整副本，本适配器立即编码 PNG 并原子落盘 capture.png；服务统一写 capture.sha256。
prototype 由后端结构性决定：C01 = 真实硬件捕获 → False（FILE 后端恒 True，C04 §3.2）。
捕获失败（CaptureError/RuntimeError）由服务转 503，且不产生 packet.json / 正常结果。

板上接线（NC 实测，板端脚本提供工厂）：
    from c01_capture import SingleFrameCapture
    factory = lambda: SingleFrameCapture(dma=<VDMA S2MM MMIO 读写口>, status=<CAP1 读写口>,
                                         allocate=<物理缓冲分配器>, identity=<代次函数>)
    captures = C01Captures(factory)
    make_server(root=..., captures=captures, engine=..., order=...)

操作顺序与验收矩阵见 docs/c01-ddr-frame-ownership-v0.md §3/§5/§7；离板替身入口
sim/vision/test_c01_backend.py（接入 run_vision_python.sh）。
"""
from pathlib import Path

FRAME_SHAPE = (720, 1280, 3)


class C01Captures:
    backend = "C01"
    prototype = False  # 真实硬件捕获；离线产物代实时结果时才允许 true（C04 §3.2）

    def __init__(self, factory, save=None):
        self.factory = factory
        self.seq = 0  # 软件 capture 序号（Q1）：frame_id 用，非 cop_frame_id
        self.save = save or self._save_png

    @staticmethod
    def _save_png(path, frame):
        import cv2
        from vision_live_service import atomic_write
        ok, data = cv2.imencode(".png", frame)
        if not ok:
            raise RuntimeError("c01 capture PNG encode failed")
        atomic_write(path, data.tobytes())

    def capture(self, round_dir):
        """一轮一个新租约；失败（错误/超时/代次变化）抛 CaptureError 且不产任何文件。"""
        frame = self.factory().capture()
        if getattr(frame, "shape", None) != FRAME_SHAPE:
            raise RuntimeError("c01 capture frame geometry invalid")
        path = Path(round_dir) / "capture.png"
        self.save(path, frame)
        self.seq = (self.seq + 1) & 0xFFFFFFFF
        return path
