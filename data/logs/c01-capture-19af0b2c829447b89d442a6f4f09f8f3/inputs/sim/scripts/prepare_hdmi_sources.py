"""Download immutable PYNQ v3.0.1 inputs; extract only pins and PS configuration."""
import hashlib
import re
import urllib.request
from pathlib import Path

root = Path(__file__).resolve().parents[2]
dest = root / "sim/build/hdmi-source"
dest.mkdir(parents=True, exist_ok=True)
base = "https://raw.githubusercontent.com/Xilinx/PYNQ/v3.0.1/boards/Pynq-Z2/base/"
inputs = {
    "base.xdc": ("vivado/constraints/base.xdc", "05d99c9032ceb21b2f6850955dd897a14a30d77ebda21d57867daa65caef2d3b"),
    "base.tcl": ("base.tcl", "e88b88b4b3e2a9c4d0856c37a26ef8550303a3f9ccddfd5c521e3f9d5d8bc8ff"),
}
for name, (url, expected) in inputs.items():
    path = dest / name
    data = path.read_bytes() if path.exists() else urllib.request.urlopen(base + url, timeout=60).read()
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError(f"official input hash mismatch: {name}")
    path.write_bytes(data)
text = (dest / "base.tcl").read_text()
match = re.search(r"set ps7_0 \[ create_bd_cell.*?set_property -dict (\[ list.*?\]) \$ps7_0", text, re.S)
if not match:
    raise ValueError("PS7 configuration not found")
(dest / "ps7_config.tcl").write_text("# Xilinx PYNQ v3.0.1, BSD-3-Clause, extracted properties.\nset_property -dict " + match[1] + " $ps\n")
pins = [line for line in (dest / "base.xdc").read_text().splitlines()
        if line.startswith("set_property -dict") and "[get_ports" in line and "hdmi_" in line]
(dest / "hdmi_pins.xdc").write_text("# Xilinx PYNQ v3.0.1, BSD-3-Clause, HDMI pins unchanged.\n" + "\n".join(pins) + "\ncreate_clock -name hdmi_pixel_in -period 13.468 [get_ports hdmi_in_clk_p]\n")
