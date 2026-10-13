"""C02 operator diagnostics: CHW software golden versus C8HW8/O16I8 RTL ports."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/"src/coprocessor"))
from int8_tensor_reference import conv2d_accumulate
from int8_reference import requantize_i8


def pack_activations(image):
    channels, height, width = image.shape
    return [sum((int(image[block*8+lane,y,x]) & 255) << (lane*8)
                for lane in range(8) if block*8+lane < channels)
            for block in range((channels+7)//8) for y in range(height) for x in range(width)]


def pack_weights(weights):
    outputs, inputs, kh, kw = weights.shape
    return [sum((int(weights[ob*16+o,ib*8+i,ky,kx]) & 255) << ((o*8+i)*8)
                for o in range(16) for i in range(8) if ob*16+o < outputs and ib*8+i < inputs)
            for ob in range((outputs+15)//16) for ky in range(kh) for kx in range(kw)
            for ib in range((inputs+7)//8)]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    output=parser.parse_args().output.resolve()
    if ROOT not in output.parents: raise ValueError("output must be in repository")
    output.mkdir(parents=True,exist_ok=True)
    rng=np.random.default_rng(20261013)
    cases=[("padding_tail",1,17,5,7,3,2,1,True), ("conv1",1,16,64,64,3,2,1,True),
        ("conv2",16,32,32,32,3,1,1,True), ("conv3",32,32,32,32,3,2,1,True),
        ("conv4",32,64,16,16,3,1,1,True), ("fc",64,3,1,1,1,1,0,False)]
    manifest={"kind":"C02_OPERATOR_DIAGNOSTIC", "seed":20261013,"cases":{}}
    for name,ci,co,h,w,k,s,p,relu in cases:
        folder=output/name; folder.mkdir(parents=True,exist_ok=True)
        image=rng.integers(-127,128,size=(ci,h,w),dtype=np.int16).astype(np.int8)
        weights=rng.integers(-2,3,size=(co,ci,k,k),dtype=np.int8)
        bias=np.arange(co,dtype=np.int32)*3-17
        accum=conv2d_accumulate(image,weights,bias,[s,s],[p,p])
        multipliers=[1+oc%3 for oc in range(co)]; shifts=[5+oc%2 for oc in range(co)]
        result=np.empty(accum.shape,np.int8)
        for oc,y,x in np.ndindex(accum.shape):
            value=int(accum[oc,y,x]); value=max(0,value) if relu else value
            result[oc,y,x]=requantize_i8(value,multipliers[oc],shifts[oc])
        packed_in,packed_weight,packed_out=pack_activations(image),pack_weights(weights),pack_activations(result)
        def save_hex(filename,values,digits):
            payload=("\n".join(f"{value & ((1<<(4*digits))-1):0{digits}x}" for value in values)+"\n").encode("ascii")
            (folder/filename).write_bytes(payload)
            return hashlib.sha256(payload).hexdigest()
        fingerprints={"input.hex":save_hex("input.hex",packed_in,16),
            "weights.hex":save_hex("weights.hex",packed_weight,256),
            "expected.hex":save_hex("expected.hex",packed_out,16),
            "bias.hex":save_hex("bias.hex",[int(bias[oc]) if oc<co else 0 for oc in range(64)],8),
            "multipliers.hex":save_hex("multipliers.hex",[multipliers[oc] if oc<co else 0 for oc in range(64)],8),
            "shifts.hex":save_hex("shifts.hex",[shifts[oc] if oc<co else 0 for oc in range(64)],2)}
        (folder/"config.txt").write_text(f"{ci} {co} {h} {w} {k} {s} {p} {int(relu)} {len(packed_in)} {len(packed_weight)} {len(packed_out)}\n",encoding="ascii")
        manifest["cases"][name]={"input_shape":list(image.shape),"output_shape":list(result.shape),
            "accumulator_min":int(accum.min()),"accumulator_max":int(accum.max()),"files_sha256":fingerprints}
    (output/"cases.txt").write_bytes(("\n".join(case[0] for case in cases)+"\n").encode("ascii"))
    (output/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    print("PASS: full-shape C02 convolution/FC diagnostics",list(manifest["cases"]))


if __name__ == "__main__": main()
