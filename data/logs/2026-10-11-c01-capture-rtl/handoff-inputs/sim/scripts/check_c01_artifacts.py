"""Check generated C01 bit/HWH/XSA pairing and exported hardware contract."""
import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path


def check_reset_release(modules):
    reset = modules["capture_reset"]
    parameters = {p.get("NAME"): p.get("VALUE") for p in reset.findall(".//PARAMETER")}
    ports = {p.get("NAME"): p for p in reset.findall(".//PORT")}
    if parameters.get("C_EXT_RESET_HIGH") != "0" or parameters.get("C_AUX_RESET_HIGH") != "0":
        raise ValueError("capture reset polarity mismatch")
    for module, expected in (("high", 1), ("capture_low", 0)):
        values = {p.get("NAME"): p.get("VALUE") for p in modules[module].findall(".//PARAMETER")}
        if int(values.get("CONST_VAL", "-1"), 0) != expected:
            raise ValueError("reset constant mismatch: " + module)
    for pin, net in (("ext_reset_in", "ps7_FCLK_RESET0_N"), ("aux_reset_in", "high_dout"),
                     ("mb_debug_sys_rst", "capture_low_dout"), ("dcm_locked", "high_dout")):
        if ports[pin].get("SIGNAME") != net:
            raise ValueError("capture reset release mismatch: " + pin)

def check(bit):
    bit=Path(bit)
    data={suffix:bit.with_suffix(suffix).read_bytes() for suffix in (".bit",".hwh",".xsa")}
    with zipfile.ZipFile(bit.with_suffix(".xsa")) as archive:
        bits=[name for name in archive.namelist() if name.endswith(".bit")]
        metadata=[name for name in archive.namelist() if name.endswith(".hwh")]
        if len(bits)!=1 or len(metadata)!=1 or archive.read(bits[0])!=data[".bit"] or archive.read(metadata[0])!=data[".hwh"]:
            raise ValueError("XSA bit/HWH does not match standalone files")
    root=ET.fromstring(data[".hwh"])
    modules={m.get("INSTANCE"):m for m in root.findall(".//MODULE")}
    check_reset_release(modules)
    maps={m.get("INSTANCE"):(int(m.get("BASEVALUE"),16),int(m.get("HIGHVALUE"),16))
          for m in modules["ps7"].findall(".//MEMRANGE")}
    for name,base in (("pipe",0x40000000),("capture_status",0x42000000),("capture_dma",0x43000000)):
        if maps.get(name)!=(base,base+65535): raise ValueError("address mismatch: "+name)
    parameters={p.get("NAME"):p.get("VALUE") for p in modules["capture_dma"].findall(".//PARAMETER")}
    expected={"C_INCLUDE_MM2S":"0","C_INCLUDE_S2MM":"1","C_NUM_FSTORES":"4",
              "C_S_AXIS_S2MM_TDATA_WIDTH":"24","C_M_AXI_S2MM_DATA_WIDTH":"64","C_USE_S2MM_FSYNC":"2"}
    for name,value in expected.items():
        if parameters.get(name)!=value: raise ValueError("VDMA parameter mismatch: "+name)
    memory=modules["capture_dma"].find(".//MEMRANGE")
    if memory.get("SLAVEBUSINTERFACE")!="S_AXI_HP0": raise ValueError("capture memory is not HP0")
    formats={p.get("NAME"):p.get("VALUE") for p in modules["capture_input"].findall(".//PARAMETER")}
    if formats.get("C_M_AXIS_VIDEO_FORMAT")!="2": raise ValueError("native input is not RGB")
    return {"acceptance":"offline_candidate_only", "addresses":{name:hex(pair[0]) for name,pair in maps.items()},
            "vdma":expected,"files":{suffix:{"path":str(bit.with_suffix(suffix)),"bytes":len(blob),
                "sha256":hashlib.sha256(blob).hexdigest()} for suffix,blob in data.items()}}


if __name__=="__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("bit"); parser.add_argument("--output")
    args=parser.parse_args(); result=check(args.bit)
    if args.output:
        with Path(args.output).open("x",encoding="utf-8") as output: json.dump(result,output,indent=2)
    print(json.dumps(result,indent=2))
    print("PASS: C01 XSA/bit/HWH pairing, address map, 24-bit S2MM/4 stores/64-bit HP0/RGB/reset release")
