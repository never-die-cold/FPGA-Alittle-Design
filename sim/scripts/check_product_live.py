"""Exercise the actual board LIVE API and preserve responses and timings."""
import argparse
import json
import time
import urllib.error
import urllib.request
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--endpoint", default="http://192.168.50.99:8765")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    timings = {}

    def call(name, route, body=None):
        data = None if body is None else json.dumps(body).encode()
        request = urllib.request.Request(args.endpoint+route, data=data,
                                         headers={"Content-Type": "application/json"})
        started = time.monotonic()
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                raw = response.read()
        except urllib.error.HTTPError as error:
            (args.output/(name+"-failed.json")).write_bytes(error.read())
            raise
        timings[name] = round(time.monotonic()-started, 3)
        (args.output/(name+".json")).write_bytes(raw+b"\n")
        return json.loads(raw)

    status = call("status", "/v1/status")
    if status.get("engine") != "COP_HW" or status.get("prototype") is not False:
        raise RuntimeError("service is not the actual hardware backend")
    config = call("config", "/v1/config", {"control": 0})
    prefix = args.output.name
    first = call("check1", "/v1/check", {"trigger_ref": prefix+"-1"})
    again = call("retry1", "/v1/check", {"trigger_ref": prefix+"-1"})
    second = call("check2", "/v1/check", {"trigger_ref": prefix+"-2"})
    if first != again:
        raise RuntimeError("retry created a different inspection")
    if second["check_id"] != first["check_id"]+1 or second["frame_id"] == first["frame_id"]:
        raise RuntimeError("second inspection did not get a fresh capture")
    for packet in (first, second):
        if packet["config_id"] != config["applied_config_id"] or packet["prototype"]:
            raise RuntimeError("configuration/source mismatch")
    (args.output/"seconds.json").write_bytes((json.dumps(timings,indent=2)+"\n").encode())
    print(json.dumps({"status": status, "seconds": timings,
                      "checks": [{"id": p["check_id"], "targets": len(p["targets"]),
                                  "decision": p["decision"]} for p in (first,second)]}, indent=2))
    print("PASS: two real capture/API rounds and idempotent retry; inspect cop_trace for hardware execution")


if __name__ == "__main__":
    main()
