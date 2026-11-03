"""Wait for a responsive reboot, then resume the fixed filming app and saved user order."""
import argparse
import json
from pathlib import Path
import socket
import time
from urllib.request import Request, urlopen

from board_ssh import connect, run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--order-from", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[2]
    if repo not in args.output.resolve().parents:
        parser.error("output must stay in repository")
    args.output.mkdir(parents=True, exist_ok=False)
    previous = json.loads(args.order_from.read_text(encoding="utf-8"))
    deadline = time.monotonic() + 240
    client = None
    print("Waiting for responsive SSH and completed video boot service", flush=True)
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("192.168.50.99",22),timeout=2) as probe:
                probe.settimeout(2)
                if not probe.recv(128).startswith(b"SSH-"):
                    continue
            client = connect()
            _,stdout,stderr = client.exec_command("systemctl show fpga-vision-boot.service -p SubState --value",timeout=5)
            phase = stdout.read().decode().strip()
            if phase == "exited":
                _,stdout,_ = client.exec_command("cat /proc/sys/kernel/random/boot_id",timeout=5)
                boot = stdout.read().decode().strip()
                break
            client.close(); client = None
        except Exception:
            if client is not None: client.close(); client = None
        time.sleep(2)
    else:
        raise RuntimeError("board still unresponsive; physical reboot is required")
    print("Responsive boot=" + boot, flush=True)
    try:
        root = "/home/xilinx/cop-live-filming-" + boot[:8]
        script = f'''#!/usr/bin/env bash
set -euo pipefail
test "$(cat /proc/sys/kernel/random/boot_id)" = {boot}
if ss -lnt 'sport = :8765' | grep -q LISTEN; then
    curl -fsS --max-time 3 http://127.0.0.1:8765/v1/status
    exit 0
fi
test ! -e {root}
mkdir {root}
py=/usr/local/share/pynq-venv/bin/python3
app=/home/xilinx/cop-app-filming-guard-20261103
pkg=/home/xilinx/cop-pkg-r9-20261103
flock -n /home/xilinx/fpga-product.lock true
nohup "$py" -u "$app/src/pynq_host/cop_product_service.py" --package "$pkg" --root {root}/live --background-mode local-fast --color-threshold 25 --min-score .8 >{root}/service.log 2>&1 </dev/null &
pid=$!
echo "$pid" >{root}/service.pid
for i in {{1..60}}; do
    if curl -fsS --max-time 1 http://127.0.0.1:8765/v1/status >{root}/status.json; then cat {root}/status.json; exit 0; fi
    if ! kill -0 "$pid" 2>/dev/null; then cat {root}/service.log; exit 1; fi
    sleep 1
done
cat {root}/service.log
exit 1
'''
        local = args.output / "start-service.sh"
        local.write_text(script,encoding="utf-8",newline="\n")
        remote = "/home/xilinx/resume-filming-" + boot[:8] + ".sh"
        sftp = client.open_sftp(); sftp.put(str(local),remote); sftp.close()
        code = run(client,"bash " + remote,args.output / "start-service.log",sudo=True)
        if code:
            raise RuntimeError("service startup failed; inspect preserved log")
        order = previous.get("work_order")
        endpoint = "http://192.168.50.99:8765"
        if order is not None:
            ack = json.load(urlopen(Request(endpoint+"/v1/config",data=json.dumps({"control":0,"order":order}).encode()),timeout=40))
            assert ack["work_order"] == order
        status = json.load(urlopen(endpoint+"/v1/status",timeout=5))
        (args.output / "status.json").write_text(json.dumps(status,indent=2),encoding="utf-8")
        print("FILMING_SERVICE_READY " + json.dumps(status),flush=True)
    finally:
        client.close()


if __name__ == "__main__":
    main()
