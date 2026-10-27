"""Push a board package to the PYNQ board over SSH and run loader commands.

The password is read from BOARD_PASSWORD and never printed or logged.  Only the
default PYNQ account is used (xilinx); no account or password is changed.
"""
import argparse
import os
import posixpath
import sys
from pathlib import Path

import paramiko

HOST = "192.168.50.99"
USER = "xilinx"


def password():
    return os.environ.get("BOARD_PASSWORD") or "xilinx"


def connect():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=password(), timeout=15,
                   allow_agent=False, look_for_keys=False)
    return client


def upload(client, local, remote):
    sftp = client.open_sftp()
    count = 0
    local = Path(local)

    def ensure(path):
        parts = path.strip("/").split("/")
        for index in range(1, len(parts) + 1):
            try:
                sftp.mkdir("/" + "/".join(parts[:index]))
            except IOError:
                pass

    ensure(remote)
    for item in sorted(local.rglob("*")):
        target = posixpath.join(remote, item.relative_to(local).as_posix())
        if item.is_dir():
            ensure(target)
        else:
            sftp.put(str(item), target)
            count += 1
    sftp.close()
    print(f"uploaded {count} files -> {remote}")
    return count


def upload_file(client, local, remote):
    sftp = client.open_sftp()
    sftp.put(str(local), remote)
    sftp.close()


def run(client, command, log, sudo=True):
    argv = ("sudo -S -p '' " + command) if sudo else command
    stdin, stdout, stderr = client.exec_command(argv, timeout=None)
    if sudo:
        stdin.write(password() + "\n")
        stdin.flush()
    lines = []
    for stream in (stdout, stderr):
        for raw in stream:
            line = raw.rstrip("\n")
            print(line, flush=True)
            lines.append(line)
    status = stdout.channel.recv_exit_status()
    if log:
        Path(log).parent.mkdir(parents=True, exist_ok=True)
        Path(log).write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"log={log}")
    return status


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upload", type=Path, help="local directory to push")
    parser.add_argument("--remote", default="/home/xilinx/cop-pkg")
    parser.add_argument("--command", help="shell command to run with sudo on the board")
    parser.add_argument("--log", type=Path, help="write command output here")
    parser.add_argument("--no-sudo", action="store_true", help="run without sudo")
    parser.add_argument("--script", type=Path, help="upload a local script and run it with bash")
    parser.add_argument("--put", type=Path, help="upload one file; --remote is the full remote path")
    args = parser.parse_args()
    client = connect()
    try:
        if args.put:
            upload_file(client, args.put, args.remote)
            print(f"put {args.put} -> {args.remote}")
        if args.upload:
            upload(client, args.upload, args.remote)
        if args.script:
            remote = "/home/xilinx/_board_step.sh"
            upload_file(client, args.script, remote)
            command = "bash " + remote
        else:
            command = args.command
        if command:
            return run(client, command, args.log, sudo=not args.no_sudo)
        return 0
    finally:
        client.close()


if __name__ == "__main__":
    sys.exit(main())
