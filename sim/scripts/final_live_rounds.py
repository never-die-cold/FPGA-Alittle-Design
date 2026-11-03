"""Exercise the user's already-applied LIVE work order; never sets a preset."""
import argparse
import json
from pathlib import Path
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--endpoint", default="http://127.0.0.1:8000")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--rounds", type=int, default=12)
    args = parser.parse_args()
    if not 1 <= args.rounds <= 100:
        parser.error("rounds must be 1..100")
    root = Path(__file__).resolve().parents[2]
    if root not in args.output.resolve().parents:
        parser.error("output must stay inside this repository")
    args.output.mkdir(parents=True, exist_ok=False)

    def request(path, body=None):
        req = Request(args.endpoint.rstrip("/") + path,
                      data=None if body is None else json.dumps(body).encode())
        try:
            response = urlopen(req, timeout=50)
        except HTTPError as error:
            response = error
        with response:
            return response.status, json.load(response)

    code, status = request("/v1/status")
    (args.output / "status.json").write_text(json.dumps(status, indent=2), encoding="utf-8")
    if code != 200 or status.get("work_order") is None:
        raise RuntimeError("Apply the work order in the web page first; no preset was submitted")
    results = []
    for index in range(args.rounds):
        started = time.monotonic()
        code, packet = request("/v1/check", {})  # automatic checks never create a manual record
        elapsed = time.monotonic() - started
        (args.output / f"round-{index+1:03d}.json").write_text(
            json.dumps(packet, indent=2) + "\n", encoding="utf-8")
        accepted = (code == 200 and packet.get("session_id") == status["session_id"]
                    and packet.get("config_id") == status["config_id"]
                    and packet.get("decision", {}).get("expected") == status["work_order"])
        results.append({"round":index+1,"http":code,"seconds":round(elapsed,3),
                        "accepted":accepted,"status":packet.get("status"),
                        "error":packet.get("error")})
        (args.output / "results.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(results[-1]), flush=True)
        if not accepted:
            raise RuntimeError("round failed or work order/session changed; evidence retained")
    print(f"PASS: {len(results)} real LIVE rounds, same user-applied work order; not an accuracy verdict")


if __name__ == "__main__":
    main()
