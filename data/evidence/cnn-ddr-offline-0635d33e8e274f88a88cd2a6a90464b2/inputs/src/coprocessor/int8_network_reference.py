"""Full frozen C02 integer network; parameters may be diagnostic or formal."""
import numpy as np
from int8_reference import INT32_MIN, INT32_MAX, requantize_i8, gap_average256, classify_logits
from int8_tensor_reference import conv2d_accumulate

SHAPES = ((16,1,3,3), (32,16,3,3), (32,32,3,3), (64,32,3,3), (3,64,1,1))


def validate_model(layers):
    if not isinstance(layers,(list,tuple)) or len(layers)!=5:
        raise ValueError("five fixed Conv/FC parameter sets required")
    for layer,shape in zip(layers,SHAPES):
        if not isinstance(layer,dict) or not all(name in layer for name in ("weight","bias","multiplier","shift")):
            raise ValueError("layer must contain weight/bias/multiplier/shift")
        w,b,m,s=(layer[name] for name in ("weight","bias","multiplier","shift"))
        if (not isinstance(w,np.ndarray) or w.dtype!=np.int8 or w.shape!=shape or np.any(w == -128)
            or not isinstance(b,np.ndarray) or b.dtype!=np.int32 or b.shape!=(shape[0],)
            or not isinstance(m,np.ndarray) or m.dtype!=np.int32 or m.shape!=b.shape or np.any(m<=0)
            or not isinstance(s,np.ndarray) or s.dtype!=np.uint8 or s.shape!=b.shape or np.any(s>62)):
            raise ValueError("C02 parameter type/shape/range mismatch")
        bound=np.abs(w.astype(np.int64)).sum(axis=(1,2,3))*127
        if np.any(b.astype(np.int64)-bound < INT32_MIN) or np.any(b.astype(np.int64)+bound > INT32_MAX):
            raise OverflowError("model cannot guarantee exact INT32 accumulation")


def run_network(q_input,layers,min_margin):
    validate_model(layers)
    classify_logits([0,0,0],min_margin)  # Reject invalid thresholds before expensive convolution.
    if (not isinstance(q_input,np.ndarray) or q_input.dtype!=np.int8 or q_input.shape!=(1,64,64)
        or np.any(q_input == -128)):
        raise ValueError("input must be symmetric INT8 1x64x64")
    tensors={"input":q_input.copy()}
    current=q_input
    for index in range(4):
        layer=layers[index]
        stride=2 if index in (0,2) else 1
        accum=conv2d_accumulate(current,layer["weight"],layer["bias"],[stride,stride],[1,1])
        current=np.empty(accum.shape,np.int8)
        for oc,y,x in np.ndindex(accum.shape):
            current[oc,y,x]=requantize_i8(max(0,int(accum[oc,y,x])),int(layer["multiplier"][oc]),int(layer["shift"][oc]))
        tensors[f"conv{index+1}"]=current.copy()
    gap=np.fromiter((gap_average256(int(current[oc].astype(np.int64).sum())) for oc in range(64)),dtype=np.int8,count=64)
    tensors["gap"]=gap
    layer=layers[4]
    accum=conv2d_accumulate(gap[:,None,None],layer["weight"],layer["bias"],[1,1],[0,0])
    logits=np.fromiter((requantize_i8(int(accum[oc,0,0]),int(layer["multiplier"][oc]),int(layer["shift"][oc]))
                        for oc in range(3)),dtype=np.int8,count=3)
    tensors["logits"]=logits
    return tensors,classify_logits([int(value) for value in logits],min_margin)
