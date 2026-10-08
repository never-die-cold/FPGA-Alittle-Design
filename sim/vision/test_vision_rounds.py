"""轮次叠加状态机（src/vision_client/rounds.py）离线测试——D2/D3/D5 撤框与恢复。

运行在真实 mock 服务（本地回环）上，不依赖 cv2/窗口：
触发节流、超龄撤框、配置不符撤框、断联（连续失败）撤框且不崩溃、服务重启（新会话）自动恢复。
"""
import sys
import threading
import time
import urllib.request
from pathlib import Path

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / "src/pynq_host"))
sys.path.insert(0, str(root / "src/vision_client"))
from vision_mock_service import make_server
from rounds import RemoteRounds, WAITING


def start_server(port):
    server = make_server(port=port)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def main():
    server = start_server(0)
    port = server.server_port
    base = f"http://127.0.0.1:{port}"
    try:
        remote = RemoteRounds(base, max_age=1.0)
        status = remote.handshake()
        assert status["mode"] == "MOCK" and remote.expected_config == 1
        assert remote.overlay(time.time()) == (False, WAITING)
        now = time.time()
        # D2：到点触发一轮；新鲜结果叠加（MOCK 模式不受 hardware_connected=false 影响）
        remote.poll(now, 0.5)
        assert remote.packet["check_id"] == 1
        current, label = remote.overlay(time.time())
        assert current and label.startswith("ROUND 1 |") and "2 targets" in label
        # 节流：间隔内不重复触发；过间隔后触发（last_trigger 记"尝试"时刻）
        remote.poll(now + 0.1, 0.5)
        assert remote.packet["check_id"] == 1
        remote.poll(now + 0.6, 0.5)
        assert remote.packet["check_id"] == 2
        # D3：结果超龄撤框
        remote.packet["created_at"] = time.time() - 1.5
        assert remote.overlay(time.time()) == (False, WAITING)
        # D3：服务端配置变化 → 新结果配置号不符撤框；重握手后恢复
        urllib.request.urlopen(urllib.request.Request(
            base + "/v1/config", b'{"control":3}', {"Content-Type": "application/json"}), timeout=2)
        remote.poll(now + 1.2, 0.5)
        assert remote.packet["config_id"] == remote.expected_config + 1
        assert remote.overlay(time.time()) == (False, WAITING)
        remote.handshake()
        remote.poll(now + 1.8, 0.5)
        assert remote.packet["config_id"] == remote.expected_config
        assert remote.overlay(time.time())[0]
        # D5：断联 → 连续失败达限撤框，且重握手失败不外泄异常
        server.shutdown()
        server.server_close()
        for step in (2.4, 3.0, 3.6):
            remote.poll(now + step, 0.5)
        assert remote.fails >= 3
        assert remote.overlay(time.time()) == (False, WAITING)
        # D5：服务恢复（新会话）→ 自动重握手（本轮不采纳报文）→ 下轮恢复叠加
        server = start_server(port)
        remote.poll(now + 4.2, 0.5)
        assert remote.packet is None and remote.expected_config == 1
        remote.poll(now + 4.8, 0.5)
        current, label = remote.overlay(time.time())
        assert current and label.startswith("ROUND ") and "2 targets" in label
    finally:
        server.shutdown()
        server.server_close()
    print("PASS: round overlay trigger/throttle/stale/config-change/outage/session-recovery")


if __name__ == "__main__":
    main()
