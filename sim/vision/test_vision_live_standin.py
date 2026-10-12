"""LIVE 网络替身（vision_mock_service --live）离板测试——W06 第一步。

不依赖 cv2/窗口/板卡：--live 替身模拟"服务正常 + 硬件已连接"，发 v1.2 LIVE 报文，
prototype 恒 true（C04 §3.2：替身结果永远不是实时推理）；场景按 check_id % 3 循环
CHECK_PASS / CHECK_FAIL / RECHECK。替身的记录/截图不得作为板上证据。
"""
import sys
import threading
import time
from pathlib import Path

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / "src/pynq_host"))
sys.path.insert(0, str(root / "src/vision_client"))
from vision_mock_service import make_server
from vision_protocol import mock_packet, validate_packet
from rounds import RemoteRounds, live_view


def main():
    server = make_server(port=0, live=True)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        remote = RemoteRounds(base, max_age=1.0)
        status = remote.handshake()
        assert status["mode"] == "LIVE" and status["hardware_connected"] is True
        assert remote.expected_config == 1
        # 三场景循环 + D3 叠加（LIVE 且 hardware_connected=True → 不因 offline 撤框）
        packets = []
        for want in ("CHECK_PASS", "CHECK_FAIL", "RECHECK"):
            time.sleep(0.55)  # 越过 0.5s 轮询节流（last_trigger 记"最近尝试"）
            remote.poll(time.time(), 0.5)
            packet = remote.packet
            packets.append(packet)
            validate_packet(packet)
            assert packet["mode"] == "LIVE" and packet["status"] == want, packet["status"]
            assert packet["prototype"] is True, "stand-in must flag prototype"
            assert packet["decision"]["verdict"] == want
            assert remote.overlay(time.time())[0], f"{want} round must overlay"
        fail = packets[1]["decision"]
        assert fail["missing"] == {"bolt": 0, "nut": 0, "washer": 1}, fail["missing"]
        assert len(packets[1]["targets"]) == 5
        recheck = packets[2]
        assert recheck["targets"][5]["class"] is None and recheck["targets"][5]["score"] == 0.42
        assert recheck["decision"]["reasons"], "RECHECK must carry reasons"
        # D8 手动触发在 LIVE 替身上同样成立（采纳点才标记）
        assert remote.trigger(time.time()) is True
        time.sleep(0.55)
        remote.poll(time.time(), 0.5)
        assert remote.last_round_manual and remote.packet["check_id"] == 4
        assert remote.packet["status"] == "CHECK_PASS"  # (4+2) % 3 == 0 → PASS
        # live_view 显示摘要（endpoint_state 的纯函数核心）：判定/差额/实际工单/类别分数
        pass_view, fail_view, recheck_view = (live_view(p) for p in packets)
        assert pass_view["verdict"] == "CHECK_PASS" and pass_view["delta"] == ""
        assert pass_view["targets"] == "6/6"
        assert pass_view["labels"][0] == ("bolt", "0.97") and pass_view["labels"][3] == ("nut", "0.88")
        assert fail_view["verdict"] == "CHECK_FAIL" and fail_view["delta"] == "-washerx1"
        assert fail_view["targets"] == "5/6"
        assert recheck_view["verdict"] == "RECHECK" and recheck_view["delta"] == "-washerx1"
        assert recheck_view["labels"][5] == ("unclassified", "0.42")
        # 退化路径：LOCATION_ONLY（MOCK 报文无类别/分数）→ 目标数 + unclassified/-- + 无差额
        only = live_view(mock_packet("sess", 1, 0, 1))
        assert only == {"verdict": "LOCATION_ONLY", "delta": "", "targets": "2",
                        "labels": [("unclassified", "--"), ("unclassified", "--")]}
    finally:
        server.shutdown()
        server.server_close()
    print("PASS: live stand-in v1.2 packets (PASS/FAIL/RECHECK cycle, prototype=true, D8 manual)")


if __name__ == "__main__":
    main()
