"""Full C02 diagnostic network golden; not a trained/production model."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"src/coprocessor"))
from int8_network_reference import SHAPES, run_network
from generate_conv_vectors import pack_activations, pack_weights


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    output=parser.parse_args().output.resolve()
    if ROOT not in output.parents: raise ValueError("output must be in repository")
    output.mkdir(parents=True,exist_ok=True)
    rng=np.random.default_rng(20261013)
    layers=[]
    for index,shape in enumerate(SHAPES):
        co=shape[0]
        layers.append({"weight":rng.integers(-2,3,size=shape,dtype=np.int8),
            "bias":(np.arange(co,dtype=np.int32)*3-17),
            "multiplier":np.array([1+oc%3 for oc in range(co)],np.int32),
            "shift":np.array([5+oc%2 for oc in range(co)],np.uint8)})
    layers[4]["bias"]=np.array([113,-57,29],np.int32)
    weights=[word for layer in layers for word in pack_weights(layer["weight"])]
    biases=[int(v) for layer in layers for v in layer["bias"]]+[0]*13
    multipliers=[int(v) for layer in layers for v in layer["multiplier"]]+[0]*13
    shifts=[int(v) for layer in layers for v in layer["shift"]]+[0]*13
    def save_hex(folder,name,values,digits):
        payload=("\n".join(f"{int(v)&((1<<(4*digits))-1):0{digits}x}" for v in values)+"\n").encode("ascii")
        (folder/name).write_bytes(payload)
        return hashlib.sha256(payload).hexdigest()
    hashes={"weights.hex":save_hex(output,"weights.hex",weights,256),
        "bias.hex":save_hex(output,"bias.hex",biases,8),
        "multipliers.hex":save_hex(output,"multipliers.hex",multipliers,8),
        "shifts.hex":save_hex(output,"shifts.hex",shifts,2)}
    y,x=np.mgrid[:64,:64]
    inputs={"pattern":((x*5+y*3)%128).astype(np.int8)[None],"zero":np.zeros((1,64,64),np.int8)}
    manifest={"kind":"DIAGNOSTIC_INTEGER_NETWORK_NOT_TRAINED", "seed":20261013,
        "weight_words":len(weights),"weight_bytes":len(weights)*128,"model_files_sha256":hashes,
        "layout":{"activation":"C8HW8; ROI low byte per 64-bit word", "weight":"O16_KH_KW_I8; input lane fastest"},
        "source_sha256":{str(path.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(path.read_bytes()).hexdigest()
                         for path in (Path(__file__).resolve(),ROOT/'sim/coprocessor/generate_conv_vectors.py',
                                      ROOT/'src/coprocessor/int8_reference.py',ROOT/'src/coprocessor/int8_tensor_reference.py',
                                      ROOT/'src/coprocessor/int8_network_reference.py')},"cases":{}}
    for name,image in inputs.items():
        folder=output/name; folder.mkdir(parents=True,exist_ok=True)
        tensors,result=run_network(image,layers,5)
        tensor_hashes={"input.hex":save_hex(folder,"input.hex",image.reshape(-1),2)}
        for index in range(1,5):
            tensor_hashes[f"conv{index}.hex"]=save_hex(folder,f"conv{index}.hex",pack_activations(tensors[f"conv{index}"]),16)
        tensor_hashes["gap.hex"]=save_hex(folder,"gap.hex",pack_activations(tensors["gap"][:,None,None]),16)
        tensor_hashes["logits.hex"]=save_hex(folder,"logits.hex",pack_activations(tensors["logits"][:,None,None]),16)
        result_payload=(f"{result['class_id']} {result['margin_q']} {result['score_q15']} {int(result['low_conf'])} 5\n").encode("ascii")
        (folder/"result.txt").write_bytes(result_payload)
        tensor_hashes['result.txt']=hashlib.sha256(result_payload).hexdigest()
        manifest["cases"][name]={"result":result,"logits":[int(v) for v in tensors["logits"]],
            "shapes":{key:list(value.shape) for key,value in tensors.items()},"files_sha256":tensor_hashes}
    (output/"cases.txt").write_bytes(("\n".join(inputs)+"\n").encode("ascii"))
    (output/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    print("PASS: full diagnostic integer network golden",{name:case["result"] for name,case in manifest["cases"].items()})


if __name__=="__main__": main()
