"""Compare captured ROI bytes with the packaged integer model, without RTL simulation."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/"src/coprocessor"))
from int8_network_reference import SHAPES, validate_model


def layers_from_payload(folder):
    manifest = json.loads((folder/"manifest.json").read_bytes())
    payload = (folder/manifest["payload_file"]).read_bytes()
    fields = {item["name"]: payload[item["offset"]:item["offset"]+item["length"]]
              for item in manifest["tensors"]}
    layers = []
    for name, (outputs, inputs, kh, kw) in zip(("conv1","conv2","conv3","conv4","fc"), SHAPES):
        padded = np.frombuffer(fields[name+".weight"], np.int8)
        padded = padded.reshape((outputs+15)//16,kh,kw,(inputs+7)//8,16,8)
        weights = padded.transpose(0,4,3,5,1,2).reshape(-1,((inputs+7)//8)*8,kh,kw)
        layer = {"weight": weights[:outputs,:inputs].copy()}
        for key, dtype in (("bias","<i4"),("multiplier","<i4"),("shift","u1")):
            layer[key] = np.frombuffer(fields[name+"."+key], dtype)[:outputs].copy()
        layers.append(layer)
    validate_model(layers)
    return layers


def requant(accum, layer):
    out = np.empty(accum.shape, dtype=np.int8)
    for channel in range(accum.shape[0]):
        value = accum[channel].astype(np.int64)*int(layer["multiplier"][channel])
        shift = int(layer["shift"][channel])
        magnitude = np.abs(value)
        rounded = magnitude if shift==0 else (magnitude+(1<<(shift-1)))>>shift
        out[channel] = np.clip(np.where(value<0,-rounded,rounded),-127,127)
    return out


def predict(raw, layers):
    current = np.frombuffer(raw, np.int8).reshape(1,64,64)
    for index, layer in enumerate(layers[:4]):
        stride = 2 if index in (0,2) else 1
        padded = np.pad(current, ((0,0),(1,1),(1,1)))
        windows = np.lib.stride_tricks.sliding_window_view(padded,(3,3),axis=(1,2))[:,::stride,::stride]
        # Integer products and every partial sum fit INT32 (validate_model).
        # Float64 dot products therefore represent these integer sums exactly.
        h,w = windows.shape[1:3]
        matrix = windows.transpose(1,2,0,3,4).reshape(h*w,-1).astype(np.float64)
        accum = (matrix @ layer["weight"].reshape(layer["weight"].shape[0],-1).T.astype(np.float64))
        accum = accum.T.reshape(-1,h,w).astype(np.int64)+layer["bias"][:,None,None]
        current = requant(np.maximum(accum,0), layer)
    gap = ((current.astype(np.int64).sum(axis=(1,2))+128)>>8)
    fc = layers[4]
    accum = fc["weight"][:,:,0,0].astype(np.int64)@gap+fc["bias"]
    return [int(v) for v in requant(accum,fc)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--round", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    layers = layers_from_payload(args.package/"payload/provisional-model")
    roi = bytes(int(v,16) for v in (args.package/"golden/roi_001/input.hex").read_text().split())
    golden = predict(roi,layers)
    if golden != [-12,-30,41]:
        raise RuntimeError("integer evaluator failed the known packaged golden: "+str(golden))
    trace = json.loads((args.round/"cop_trace.json").read_bytes())
    rows = []
    hardware = trace["driver"]["targets"]
    for index, item in enumerate(trace["rois"]):
        expected = predict((args.round/item["path"]).read_bytes(),layers)
        actual = [v-256 if v>127 else v for v in hardware[index]["logits"]]
        rows.append({"index":index,"reference":expected,"hardware":actual,"match":expected==actual,
                     "valid":hardware[index]["valid"]})
    args.output.write_bytes((json.dumps({"golden":golden,"rois":rows},indent=2)+"\n").encode())
    print(json.dumps(rows))


if __name__ == "__main__":
    main()
