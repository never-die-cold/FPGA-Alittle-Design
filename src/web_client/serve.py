"""Serve the web client and forward its API requests to the PYNQ board."""
import argparse
import json
import re
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener


class Handler(SimpleHTTPRequestHandler):
    extensions_map = {**SimpleHTTPRequestHandler.extensions_map, ".mjs": "text/javascript"}

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def forward(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 <= length <= 4096:
                raise ValueError("request body exceeds 4096 bytes")
        except ValueError as error:
            self.send_error(400, str(error))
            return
        body = self.rfile.read(length) if self.command == "POST" else None
        request = Request(self.server.endpoint + self.path, data=body,
                          headers={"Content-Type": "application/json"}, method=self.command)
        try:
            response = build_opener(ProxyHandler({})).open(request, timeout=45)
        except HTTPError as error:
            response = error
        except (URLError, TimeoutError, OSError) as error:
            data = json.dumps({"error": "board unavailable: " + str(error)}).encode()
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        with response:
            data = response.read()
            self.send_response(response.code)
            self.send_header("Content-Type", response.headers.get("Content-Type", "application/json"))
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    def do_GET(self):
        if self.path in ("/v1/status", "/v1/latest") or re.fullmatch(r"/v1/captures/[^/]+/[0-9]{1,10}\.png", self.path):
            self.forward()
        else:
            super().do_GET()

    def do_POST(self):
        if self.path in ("/v1/check", "/v1/config"):
            self.forward()
        else:
            self.send_error(404)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--endpoint", default="http://192.168.50.99:8765")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    handler = partial(Handler, directory=str(Path(__file__).resolve().parent))
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    server.endpoint = args.endpoint.rstrip("/")
    print(f"EdgeSight http://127.0.0.1:{args.port} -> {server.endpoint}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
