"""Offline receiver integrity/failure tests; evidence stays inside sim/build."""
import base64
import gzip
import hashlib
import importlib.util
import io
import tempfile
from pathlib import Path

root=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("receiver",root/"sim/scripts/pynq_file_receiver.py")
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
raw=bytes(range(256))*32
payload=base64.b64encode(gzip.compress(raw))
sha=hashlib.sha256(raw).hexdigest()
class Fragmented(io.BytesIO):
    def read(self,n=-1): return super().read(min(n,17))
with tempfile.TemporaryDirectory(prefix="uart-receiver-",dir=root/"sim/build") as folder:
    target=Path(folder)/"capture.bit"
    args=(len(payload),len(raw),sha,target,"TEST")
    module.receive(*args,stream=io.BytesIO(payload))
    assert target.read_bytes()==raw
    fragmented=Path(folder)/"fragmented.bit"
    module.receive(len(payload),len(raw),sha,fragmented,"TEST",Fragmented(payload))
    assert fragmented.read_bytes()==raw
    try: module.receive(*args,stream=io.BytesIO(payload))
    except FileExistsError: pass
    else: raise AssertionError("overwrote existing target")
    assert target.read_bytes()==raw
    for encoded,size,digest,error in ((payload[:-1],len(raw),sha,ValueError),
        (b"!"*len(payload),len(raw),sha,ValueError),
        (payload,len(raw)+1,sha,ValueError),(payload,len(raw),"0"*64,ValueError)):
        bad=Path(folder)/"bad.bit"
        try: module.receive(len(payload),size,digest,bad,"TEST",io.BytesIO(encoded))
        except error: pass
        else: raise AssertionError("accepted corrupt payload")
        assert not bad.exists()
print("PASS: UART receiver binary roundtrip, no overwrite, short/corrupt/length/hash rejection")
