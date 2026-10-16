"""Reject the permanent auxiliary reset seen in the first C01 board trial."""
import copy
import importlib.util
import xml.etree.ElementTree as ET
from pathlib import Path

root = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("artifacts", root / "sim/scripts/check_c01_artifacts.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
reset = ET.fromstring('''<MODULE><PARAMETERS>
<PARAMETER NAME="C_EXT_RESET_HIGH" VALUE="0"/>
<PARAMETER NAME="C_AUX_RESET_HIGH" VALUE="0"/></PARAMETERS><PORTS>
<PORT NAME="ext_reset_in" SIGNAME="ps7_FCLK_RESET0_N"/>
<PORT NAME="aux_reset_in" SIGNAME="high_dout"/>
<PORT NAME="mb_debug_sys_rst" SIGNAME="capture_low_dout"/>
<PORT NAME="dcm_locked" SIGNAME="high_dout"/></PORTS></MODULE>''')
modules = {"capture_reset": reset,
           "high": ET.fromstring('<MODULE><PARAMETER NAME="CONST_VAL" VALUE="0x1"/></MODULE>'),
           "capture_low": ET.fromstring('<MODULE><PARAMETER NAME="CONST_VAL" VALUE="0x0"/></MODULE>')}
module.check_reset_release(modules)
for target, tag, name, attribute, value in (
    ("capture_reset", "PORT", "aux_reset_in", "SIGNAME", "capture_low_dout"),
    ("capture_reset", "PARAMETER", "C_AUX_RESET_HIGH", "VALUE", "1"),
    ("capture_reset", "PARAMETER", "C_EXT_RESET_HIGH", "VALUE", "1"),
    ("capture_reset", "PORT", "mb_debug_sys_rst", "SIGNAME", "high_dout"),
    ("capture_reset", "PORT", "dcm_locked", "SIGNAME", "capture_low_dout"),
    ("capture_reset", "PORT", "ext_reset_in", "SIGNAME", "unconnected"),
    ("high", "PARAMETER", "CONST_VAL", "VALUE", "0x0"),
    ("capture_low", "PARAMETER", "CONST_VAL", "VALUE", "0x1")):
    faulty = copy.deepcopy(modules)
    next(node for node in faulty[target].findall(".//" + tag)
         if node.get("NAME") == name).set(attribute, value)
    try:
        module.check_reset_release(faulty)
    except ValueError:
        pass
    else:
        raise AssertionError("accepted invalid reset: " + name)
print("PASS: C01 reset deassertion accepts hex constants and rejects 8 polarity/net/constant faults")