"""Prevent an old ready snapshot matching a new firmware job receipt."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src/pynq_host"))
import cop_regs as R
from cop_driver import CopDriver, CopProtocolError

class Transport:
    def __init__(self, previous, stuck=False):
        self.regs={"DMA_BYTES":previous,"STATUS":R.STATUS_MODEL_VALID}
        self.commits=[]; self.stuck=stuck
    def read32(self, offset):
        return self.regs.get(next(k for k,v in R.OFFSETS.items() if v==offset),0)
    def write32(self, offset, value):
        name=next(k for k,v in R.OFFSETS.items() if v==offset)
        self.regs[name]=value
        if name=="CFG_COMMIT":
            self.commits.append((self.regs["CFG_SEQ"],self.regs["ROI_COUNT"]))
            if len(self.commits)==1:
                assert self.regs["ROI_COUNT"]*R.ROI_BYTES != self.regs["DMA_BYTES"]
            self.regs["CFG_APPLIED"]=self.regs["CFG_SEQ"]
            if not self.stuck:self.regs["STATUS"]=0
class Dma:
    def __init__(self,t): self.t=t; self.loaded=False
    def load_model(self,*args):
        assert len(self.t.commits)==2 and not self.t.regs["STATUS"]&R.STATUS_MODEL_VALID
        self.loaded=True
    def load_rois(self,*args): pass
    def load_descriptors(self,*args): pass

for previous in (4096,28672,40960):
    t=Transport(previous); dma=Dma(t)
    driver=CopDriver(t,dma,{"bolt":1,"nut":0,"washer":0},.8,dma_after_commit=True)
    job={"targets":[{"target_id":0,"roi":bytes(4096)}],"work_order_rev":1,
         "job_id":1,"capture_id":1,"source_config_id":1}
    driver._configure(job,1)
    assert t.commits[-1]==(2,1) and dma.loaded
t=Transport(4096,stuck=True); dma=Dma(t)
driver=CopDriver(t,dma,{"bolt":1,"nut":0,"washer":0},.8,dma_after_commit=True,config_timeout_s=.01)
try:
    driver._configure(job,1)
    raise AssertionError("stale MODEL_VALID accepted")
except CopProtocolError:
    assert not dma.loaded and len(t.commits)==1
print("PASS: guard receipt cannot match old DMA_BYTES; real job waits for cleared MODEL_VALID")
