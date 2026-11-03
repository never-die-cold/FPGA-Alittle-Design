"""Browser delivery and board API forwarding, using the existing mock server."""
import json
import sys
import threading
import unittest
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import ProxyHandler, Request, build_opener

root = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(root / "src/web_client"), str(root / "src/pynq_host")]
from serve import Handler
from vision_mock_service import make_server


class WebServerTests(unittest.TestCase):
    def setUp(self):
        self.board = make_server(port=0, live=True)
        self.web = ThreadingHTTPServer(("127.0.0.1", 0),
            partial(Handler, directory=str(root / "src/web_client")))
        self.web.endpoint = f"http://127.0.0.1:{self.board.server_port}"
        for server in (self.board, self.web):
            threading.Thread(target=server.serve_forever, daemon=True).start()

    def tearDown(self):
        for server in (self.web, self.board):
            server.shutdown()
            server.server_close()

    def request(self, path, body=None):
        request = Request(f"http://127.0.0.1:{self.web.server_port}" + path,
                          data=None if body is None else json.dumps(body).encode())
        try:
            return build_opener(ProxyHandler({})).open(request, timeout=5)
        except HTTPError as error:
            return error

    def test_module_mime_and_static_root(self):
        with self.request("/protocol.mjs") as response:
            self.assertEqual(response.status, 200)
            self.assertEqual(response.headers["Content-Type"], "text/javascript")
        with self.request("/plan.md") as response:
            self.assertEqual(response.status, 404)

    def test_board_round_and_error_forwarding(self):
        with self.request("/v1/status") as response:
            self.assertTrue(json.load(response)["hardware_connected"])
        with self.request("/v1/check", {"trigger_ref": "web-manual"}) as response:
            self.assertEqual(json.load(response)["trigger_ref"], "web-manual")
        with self.request("/v1/check", {"unknown": True}) as response:
            self.assertEqual(response.status, 400)
        with self.request("/v1/config", {"control": 0}) as response:
            self.assertIn("applied_config_id", json.load(response))

    def test_unreachable_board_is_502(self):
        self.board.shutdown()
        self.board.server_close()
        with self.request("/v1/status") as response:
            self.assertEqual(response.status, 502)


if __name__ == "__main__":
    unittest.main()
