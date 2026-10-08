"""Prepare this project's Pi card for one boot that resets pi/edgesight passwords."""
import pathlib
import re
import shutil
import subprocess
import sys

boot = pathlib.Path(sys.argv[1]).resolve()
if boot != pathlib.Path("F:/").resolve():
    raise SystemExit("Expected the explicitly identified F: project card")
issue = (boot / "issue.txt").read_text()
cmdline = (boot / "cmdline.txt").read_text().strip()
userdata = (boot / "user-data").read_text()
userconf = (boot / "userconf.txt").read_text()
if "Raspberry Pi reference 2026-09-15" not in issue:
    raise SystemExit("Unexpected card image")
if "root=PARTUUID=22b1b901-02" not in cmdline or "systemd.run=" in cmdline:
    raise SystemExit("Unexpected root partition or pending boot command")
if "\n" in cmdline or userconf.split(":", 1)[0] != "pi":
    raise SystemExit("Unexpected boot command line or userconf account")
if re.findall(r"^\s*-\s*name:\s*(\S+)\s*$", userdata, re.M) != ["edgesight"]:
    raise SystemExit("Unexpected cloud-init users")
backup = boot / "pi-password-reset-backup"
if backup.exists():
    raise SystemExit("Backup already exists; do not overwrite the original")
hashes = {}
for name in ("pi", "edgesight"):
    hashes[name] = subprocess.check_output(
        ["C:/msys64/usr/bin/openssl.exe", "passwd", "-6", "-stdin"],
        input=(name + "\n").encode(),
    ).decode().strip()
    if not hashes[name].startswith("$6$"):
        raise SystemExit("Password hashing failed")
userdata, count = re.subn(
    r"^(\s*)passwd:.*$",
    lambda m: m[1] + "passwd: '" + hashes["edgesight"] + "'",
    userdata, flags=re.M,
)
if count != 1:
    raise SystemExit("Expected exactly one cloud-init password")
script = pathlib.Path(__file__).with_name("pi_password_reset_once.sh").read_bytes()
backup.mkdir()
for name in ("cmdline.txt", "user-data", "userconf.txt"):
    shutil.copy2(boot / name, backup / name)
updates = {
    "pi-password-reset.sh": script,
    "pi-password-reset.hashes": "".join(n + ":" + hashes[n] + "\n" for n in hashes).encode(),
    "user-data": userdata.encode(),
    "userconf.txt": ("pi:" + hashes["pi"] + "\n").encode(),
    "cmdline.txt": (cmdline + ' systemd.run="/bin/bash /boot/firmware/pi-password-reset.sh"'
                    ' systemd.run_success_action=reboot systemd.run_failure_action=none'
                    ' systemd.unit=kernel-command-line.target\n').encode(),
}
try:
    for name, contents in updates.items():
        (boot / name).write_bytes(contents)
        if (boot / name).read_bytes() != contents:
            raise OSError("Card readback mismatch: " + name)
except Exception:
    for name in ("cmdline.txt", "user-data", "userconf.txt"):
        shutil.copy2(backup / name, boot / name)
    raise
print("PASS: card files prepared and read back; original files backed up")
print("PENDING: boot Pi to apply pi/edgesight password hashes")
