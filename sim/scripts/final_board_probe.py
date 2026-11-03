"""Read-only SSH inventory before the final board session; no MMIO writes."""
import argparse
import json
from pathlib import Path

from board_ssh import connect

REMOTE = r'''
import json, pathlib, subprocess
out = {}
commands = {
    "date": ["date", "-Is"],
    "uptime": ["uptime"],
    "disk": ["df", "-k", "/", "/home/xilinx"],
    "listeners": ["ss", "-ltn"],
    "boot_service": ["systemctl", "show", "fpga-vision-boot.service",
                     "-p", "ActiveState,SubState,ExecMainStatus,ExecStart"],
}
for name, command in commands.items():
    p = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       universal_newlines=True, timeout=10)
    out[name] = {"exit": p.returncode, "output": p.stdout}
for name, path in {"boot_id": "/proc/sys/kernel/random/boot_id",
                   "fpga_state": "/sys/class/fpga_manager/fpga0/state"}.items():
    try:
        out[name] = pathlib.Path(path).read_text().strip()
    except OSError as e:
        out[name] = str(e)
p = subprocess.run(["ps", "-eo", "pid,ppid,etime,args"], stdout=subprocess.PIPE,
                   universal_newlines=True, timeout=10)
out["services"] = [line for line in p.stdout.splitlines()
                   if any(key in line for key in ("cop_product_service.py",
                          "vision_live_service.py", "vision_boot", "boot.py"))]
out["packages"] = [str(p) for p in pathlib.Path("/home/xilinx").glob("cop-pkg*")]
out["apps"] = [str(p) for p in pathlib.Path("/home/xilinx").glob("cop-app*")]
out["runs"] = [str(p) for p in pathlib.Path("/home/xilinx").glob("cop-live*")]
print(json.dumps(out, indent=2))
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    client = connect()
    try:
        stdin, stdout, stderr = client.exec_command("python3 -", timeout=90)
        stdin.write(REMOTE)
        stdin.channel.shutdown_write()
        raw, error = stdout.read(), stderr.read()
        code = stdout.channel.recv_exit_status()
        if code:
            raise RuntimeError(error.decode(errors="replace"))
        record = json.loads(raw)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(record, indent=2))
    finally:
        client.close()


if __name__ == "__main__":
    main()
