"""One authenticated Pi SSH connection; local request files contain no password."""
import getpass
import json
import os
from pathlib import Path
import time

import paramiko

ROOT = Path(__file__).resolve().parents[2]
SESSION = ROOT / "sim/build" / f"nc-ssh-{time.strftime('%Y%m%d-%H%M%S')}-{os.getpid()}"
HOST, USER = "192.168.50.2", "edgesight"


def execute(client, request):
    command = request["command"]
    limit = float(request.get("timeout_s", 30))
    if not isinstance(command, str) or not command or len(command) > 16384:
        raise ValueError("invalid command")
    if not 1 <= limit <= 180:
        raise ValueError("timeout must be 1..180 seconds")
    started = time.monotonic()
    stdin, stdout, stderr = client.exec_command(command, timeout=10)
    stdin.close()
    channel = stdout.channel
    output, errors = bytearray(), bytearray()
    try:
        while True:
            while channel.recv_ready():
                output.extend(channel.recv(32768))
            while channel.recv_stderr_ready():
                errors.extend(channel.recv_stderr(32768))
            if len(output) + len(errors) > 2 * 1024 * 1024:
                raise RuntimeError("output limit; remote completion unconfirmed")
            if channel.exit_status_ready() and not channel.recv_ready() and not channel.recv_stderr_ready():
                exit_code = channel.recv_exit_status()
                return {"exit_code": exit_code, "completion_confirmed": exit_code >= 0,
                        "stdout": output.decode("utf-8", "replace"),
                        "stderr": errors.decode("utf-8", "replace"),
                        "elapsed_s": round(time.monotonic() - started, 3)}
            if time.monotonic() - started > limit:
                raise TimeoutError("remote completion unconfirmed; do not assume command stopped")
            time.sleep(0.05)
    finally:
        channel.close()


def main():
    if SESSION.exists():
        raise RuntimeError(f"Preserve earlier session; directory already exists: {SESSION}")
    client = paramiko.SSHClient()
    client.load_host_keys(str(Path.home() / ".ssh/known_hosts"))
    client.set_missing_host_key_policy(paramiko.RejectPolicy())
    password = getpass.getpass(f"SSH password for {USER}@{HOST} (not logged): ")
    try:
        client.connect(HOST, username=USER, password=password, allow_agent=False,
                       look_for_keys=False, timeout=10, auth_timeout=15, banner_timeout=15)
    except BaseException:
        client.close()
        raise
    finally:
        del password
    own_session = False
    try:
        client.get_transport().set_keepalive(15)
        SESSION.mkdir(parents=True)
        own_session = True
        info = {"host": HOST, "user": USER, "pid": os.getpid(), "connected": True}
        (SESSION / "state.json").write_text(json.dumps(info), encoding="utf-8")
        print(f"READY: {SESSION}; leave this window open; Ctrl+C closes SSH", flush=True)
        deadline = time.monotonic() + 3600
        while time.monotonic() < deadline and not (SESSION / "STOP").exists():
            for path in sorted(SESSION.glob("*.request.json")):
                response = path.with_name(path.name.replace(".request.json", ".response.json"))
                if response.exists():
                    continue
                try:
                    result = execute(client, json.loads(path.read_text(encoding="utf-8-sig")))
                except Exception as error:
                    result = {"error": str(error), "completion_confirmed": False}
                pending = response.with_suffix(".pending")
                pending.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
                pending.replace(response)
                print(f"COMPLETED: {path.name} confirmed={result['completion_confirmed']}", flush=True)
                if not result["completion_confirmed"]:
                    return
            time.sleep(0.2)
    finally:
        client.close()
        if own_session:
            info["connected"] = False
            (SESSION / "state.json").write_text(json.dumps(info), encoding="utf-8")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("SSH session closed")
