#!/usr/bin/env python3
"""Board-side bounded UART ZIP receiver. Run from a serial login shell.

Never overwrites the working vision_m2 package; diagnostic files go to a
separate directory. Binary transfer uses raw terminal mode, restored finally.
"""
import hashlib
import io
import os
from pathlib import Path
import select
import sys
import termios
import tty
import zipfile

ALLOWED = {"vision.bit", "vision.hwh", "vision_regs.py", "display_view.py",
           "m2_onboard.py", "vision_demo.py", "RUNBOOK.md", "manifest.json"}


def main():
    size, digest = int(sys.argv[1]), sys.argv[2]
    if not 0 < size <= 8 * 1024 * 1024 or len(digest) != 64:
        raise ValueError("invalid size/digest")
    fd = sys.stdin.fileno()
    previous = termios.tcgetattr(fd)
    blob = bytearray()
    try:
        tty.setraw(fd, termios.TCSADRAIN)
        print("UART-READY", flush=True)
        while len(blob) < size:
            if not select.select([fd], [], [], 15)[0]:
                raise TimeoutError("UART stalled; transfer rejected")
            chunk = os.read(fd, min(4096, size - len(blob)))
            if not chunk:
                raise EOFError("UART ended")
            blob.extend(chunk)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, previous)
    if hashlib.sha256(blob).hexdigest() != digest:
        raise ValueError("archive SHA256 mismatch; nothing installed")
    with zipfile.ZipFile(io.BytesIO(blob)) as archive:
        names = archive.namelist()
        if len(set(names)) != len(names) or set(names) != ALLOWED:
            raise ValueError("package names invalid")
        if any(item.file_size > 8 * 1024 * 1024 for item in archive.infolist()):
            raise ValueError("oversize entry")
        contents = {name: archive.read(name) for name in names}  # CRC before writes
    target = Path.home() / "vision_diag"
    target.mkdir(exist_ok=True)
    for name, content in contents.items():
        (target / name).write_bytes(content)
        print(f"FILE {name} SHA256={hashlib.sha256(content).hexdigest()}")
    print(f"PASS: UART package {len(blob)} bytes SHA256={digest} -> {target}", flush=True)


if __name__ == "__main__":
    main()
