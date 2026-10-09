"""HUD 状态渲染校验（非产品代码）：用产品 draw_hud 渲染"等待/过期"与"UVC-only"两种状态。

02/03 两张图由真实运行产生（preview.py --mock [--endpoint]）；本脚本补渲染另外两条
状态分支供人工目检（值字典与 preview.main 中的组装一致）。
运行：set PYTHONPATH=<deps> && py render_hud_states.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # worktree 根（data/logs/<date>/<file> 上溯 3 层）
sys.path.insert(0, str(ROOT / "src/pynq_host"))
sys.path.insert(0, str(ROOT / "src/vision_client"))
import cv2
from preview import AMBER, AMBER_DEEP, CYAN, DIM, RED, TEXT, metrics_cells, mock_frame, render
from vision_protocol import mock_packet

OUT = Path(__file__).resolve().parent
packet = mock_packet("b564747f-0000-0000-0000-000000000000", 7, 2, 7)

# 等待/过期状态（endpoint 模式、结果超龄）：值字典同 preview.main 的 waiting 分支
waiting_hud = {
    "badge": ("MOCK ONLY", AMBER),
    "status": ("WAITING FOR RESULT", AMBER_DEEP, 2),
    "metrics": metrics_cells(None, 2, "1.4s", AMBER_DEEP),
    "fresh": (1.0, RED),
}
cv2.imwrite(str(OUT / "04_waiting_state.png"), render(mock_frame(packet), None, waiting_hud))

# UVC-only 状态（无结果服务）：指标面板隐藏
uvc_hud = {
    "badge": ("VIDEO ONLY", DIM),
    "status": ("UNASSOCIATED | no board recognition", DIM, 1),
    "metrics": None,
    "fresh": None,
}
cv2.imwrite(str(OUT / "05_uvc_only.png"), render(mock_frame(packet), None, uvc_hud))
print("PASS: hud state renders ->", OUT)
