import hashlib
import importlib.util
import tempfile
from pathlib import Path
from types import SimpleNamespace

root=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("probe",root/"sim/scripts/c01_status_onboard.py")
module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
class Device:
    def __init__(self,base,case): self.base,self.case=base,case
    def read(self,offset):
        if self.base==0x43000000:
            return {0x30:1 if self.case=="running" else 0,0x34:0 if self.case=="running" else 1}[offset]
        return {0:0 if self.case=="identity" else 0x43415031,4:0 if self.case=="lock" else 1,
                8:0,0x14:1280,0x18:720}.get(offset,0)
with tempfile.TemporaryDirectory(prefix="c01-probe-",dir=root/"sim/build") as folder:
    bit=Path(folder)/"capture.bit"; bit.write_bytes(b"offline bit")
    hwh=bit.with_suffix(".hwh"); hwh.write_bytes(b"offline metadata")
    bit_sha=hashlib.sha256(bit.read_bytes()).hexdigest(); hwh_sha=hashlib.sha256(hwh.read_bytes()).hexdigest()
    for case in ("normal","load","identity","lock","smoke","running","bad_hash"):
        calls=[]
        def load(path):
            calls.append("load")
            if case=="load": raise RuntimeError("load fault")
            return SimpleNamespace(ip_dict={str(base):{"phys_addr":base,"addr_range":65536}
                for base in (0x40000000,0x42000000,0x43000000)})
        def smoke():
            calls.append("smoke")
            if case=="smoke": raise RuntimeError("smoke fault")
        try:
            module.probe(bit,"0"*64 if case=="bad_hash" else bit_sha,hwh_sha,
                load,lambda base,size:Device(base,case),smoke,lambda:calls.append("restore"),lambda seconds:None)
        except (RuntimeError,TimeoutError,ValueError): assert case!="normal"
        else: assert case=="normal"
        assert calls.count("restore")== (0 if case in ("running","bad_hash") else 1), (case,calls)
        if case=="bad_hash": assert not calls
print("PASS: C01 board probe normal path, artifact reject, load/identity/lock/smoke cleanup and running-DMA protection")
for stage_case in ("normal", "bad_layout", "download_error"):
    events = []
    class MetadataOverlay:
        def __init__(self, path, download, gen_cache):
            assert download is False and gen_cache is False
            events.append("metadata")
            self.ip_dict = {str(base): {"phys_addr": base, "addr_range": 65536}
                           for base in (0x40000000, 0x42000000, 0x43000000)}
            if stage_case == "bad_layout":
                self.ip_dict.pop(str(0x42000000))
        def download(self):
            events.append("download")
            if stage_case == "download_error":
                raise RuntimeError("download failure")
    try:
        module.load_candidate("offline-only.bit", MetadataOverlay)
    except RuntimeError:
        assert stage_case != "normal"
    else:
        assert stage_case == "normal"
    assert events == (["metadata"] if stage_case == "bad_layout" else ["metadata", "download"])
print("PASS: staged metadata validates addresses before physical download and propagates download failure")
