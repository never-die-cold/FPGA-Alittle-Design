"""轮次叠加会话状态机（EXE 侧）——D2 触发 / D3 有效性撤框 / D5 会话重连。

preview.py 只负责取帧与渲染；状态机抽离为纯 stdlib 模块（不依赖 cv2），
离板可测：sim/vision/test_vision_rounds.py。

语义要点（决策单 docs/vision-sync-protocol-decisions.md）：
- poll 的 last_trigger 记"最近一次尝试"而非"最近一次成功"——失败重试也被节流；
- 连续失败达 FAIL_LIMIT 重握手，重握手自身失败不许外泄异常（服务重启窗口期）；
- 服务重启 = 新会话：poll 检测到 session 变化立即重握手，本轮不采纳报文（D5）；
- overlay 撤框条件 = 无报文 / 连续失败达限 / 超龄 / 会话不符 / 配置号不符 /
  LIVE 模式未联接（MOCK 模式豁免 hardware_connected=false）；
- trigger()：手动触发（c 键/检查按钮）立即发起下一轮并标记为批次记录候选（D8），
  0.3s 防抖防按键自动重复灌爆批次表。
"""
import json
import urllib.error
import urllib.request

from vision_protocol import is_current, validate_packet

REQUEST_TIMEOUT = 2.0
FAIL_LIMIT = 3
WAITING = "WAITING FOR RESULT"


def http_json(url, body=None):
    data = None if body is None else json.dumps(body).encode()
    headers = {"Content-Type": "application/json"} if body is not None else {}
    request = urllib.request.Request(url, data, headers)
    with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
        return json.loads(response.read(65537))


class RemoteRounds:
    """握手 → 周期触发 → 有效性判定；失败计数、会话变化与重握手在 poll 收口。"""

    def __init__(self, endpoint, max_age):
        self.endpoint = endpoint.rstrip("/")
        self.max_age = max_age
        self.session = None
        self.mode = None
        self.hardware_connected = False
        self.expected_config = None
        self.fails = 0
        self.last_trigger = 0.0
        self.packet = None
        self.manual_pending = False
        self.last_round_manual = False
        self.last_manual = None

    def handshake(self):
        status = http_json(self.endpoint + "/v1/status")
        applied = http_json(self.endpoint + "/v1/config", {"control": 0})["applied_config_id"]
        self.session = status["session_id"]
        self.mode = status["mode"]
        self.hardware_connected = status["hardware_connected"]
        self.expected_config = applied
        self.fails = 0
        self.packet = None
        self.last_trigger = 0.0
        self.manual_pending = False
        self.last_round_manual = False
        return status

    def trigger(self, now, min_gap=0.3):
        """手动触发下一轮；min_gap 内重复触发忽略（防按键自动重复）。该轮为批次记录候选（D8）。"""
        if self.last_manual is not None and now - self.last_manual < min_gap:
            return False
        self.last_manual = now
        self.manual_pending = True
        self.last_trigger = 0.0
        return True

    def rehandshake(self):
        try:
            self.handshake()
        except (urllib.error.URLError, OSError, KeyError, ValueError) as error:
            print(f"WARN: re-handshake failed: {error}", flush=True)

    def poll(self, now, interval):
        if now - self.last_trigger < interval:
            return
        self.last_trigger = now
        manual = self.manual_pending
        self.manual_pending = False
        self.last_round_manual = manual
        try:
            # 传空 JSON 对象：http_json 以"有无 body"区分 GET/POST，/v1/check 仅接受 POST。
            packet = validate_packet(http_json(self.endpoint + "/v1/check", {}))
        except (urllib.error.URLError, OSError, ValueError) as error:
            self.fails += 1
            print(f"WARN: check failed ({self.fails}/{FAIL_LIMIT}): {error}", flush=True)
            if self.fails >= FAIL_LIMIT:
                self.rehandshake()
            return
        if self.session is not None and packet["session_id"] != self.session:
            print("WARN: service session changed; re-handshaking", flush=True)
            self.rehandshake()
            return
        self.packet = packet
        self.fails = 0

    def overlay(self, now):
        """返回 (是否叠加, 横幅文本)；撤框条件见 D3。"""
        if (self.packet is not None and self.session is not None and self.fails < FAIL_LIMIT
                and (self.mode == "MOCK" or self.hardware_connected)
                and is_current(self.packet, self.session, self.expected_config, self.max_age)):
            age = now - self.packet["created_at"]
            return True, (f"ROUND {self.packet['check_id']} | {age:.1f}s ago | "
                          f"{len(self.packet['targets'])} targets")
        return False, WAITING
