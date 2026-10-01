"""Local M2 API mock. No MMIO, board access, inference or batch counting."""
import argparse
import json
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from vision_protocol import mock_packet, uint


class State:
    def __init__(self):
        self.session_id = str(uuid.uuid4())
        self.config_id = 0
        self.frame_id = 0
        self.control = 0
        self.lock = threading.Lock()

    def latest(self):
        with self.lock:
            self.frame_id = (self.frame_id + 1) & 0xFFFFFFFF
            return mock_packet(self.session_id, self.frame_id, self.config_id)

    def configure(self, request):
        if not isinstance(request, dict) or set(request) != {"control"}:
            raise ValueError("expected control only")
        control = uint(request["control"], "control")
        if control > 15:
            raise ValueError("reserved control bits")
        with self.lock:
            self.control = control
            self.config_id = (self.config_id + 1) & 0xFFFFFFFF
            return {"mode": "MOCK", "applied_config_id": self.config_id}


def make_server(host="127.0.0.1", port=8765):
    state = State()
    class Handler(BaseHTTPRequestHandler):
        def reply(self, status, body):
            data = json.dumps(body, allow_nan=False).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if self.path == "/v1/latest":
                self.reply(200, state.latest())
            elif self.path == "/v1/status":
                self.reply(200, {"mode": "MOCK", "session_id": state.session_id, "hardware_connected": False})
            else:
                self.reply(404, {"error": "unknown route"})

        def do_POST(self):
            if self.path != "/v1/config":
                self.reply(404, {"error": "unknown route"})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 4096:
                    raise ValueError("body size")
                self.reply(200, state.configure(json.loads(self.rfile.read(length))))
            except (ValueError, TypeError) as error:
                self.reply(400, {"error": str(error)})

        def log_message(self, *args):
            pass
    return ThreadingHTTPServer((host, port), Handler)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    print(f"MOCK ONLY: http://127.0.0.1:{args.port}/v1/status", flush=True)
    make_server(port=args.port).serve_forever()
