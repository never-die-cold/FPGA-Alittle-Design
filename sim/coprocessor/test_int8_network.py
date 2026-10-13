"""Independent constant-network golden and formal-parameter rejection checks."""
import numpy as np
from int8_reference import INT32_MAX, INT32_MIN
from int8_network_reference import SHAPES, validate_model, run_network


def model():
    return [dict(weight=np.zeros(shape,np.int8),bias=np.arange(shape[0],dtype=np.int32)%6,
                 multiplier=np.ones(shape[0],np.int32),shift=np.zeros(shape[0],np.uint8)) for shape in SHAPES]


def rejected(call,exception=ValueError):
    try: call()
    except exception: return
    raise AssertionError('invalid model/input accepted')


def main():
    layers=model(); layers[-1]['bias'][:]=[-10,30,5]
    image=np.full((1,64,64),127,np.int8)
    tensors,result=run_network(image,layers,26)
    # Zero weights make every Conv output its channel bias, independent of input/padding.
    sizes=(32,32,16,16)
    for n,size in enumerate(sizes):
        expected=np.broadcast_to((np.arange(SHAPES[n][0])%6)[:,None,None],(SHAPES[n][0],size,size))
        np.testing.assert_array_equal(tensors[f'conv{n+1}'],expected)
    np.testing.assert_array_equal(tensors['gap'],np.arange(64)%6)
    np.testing.assert_array_equal(tensors['logits'],[-10,30,5])
    assert result==dict(class_id=1,margin_q=25,score_q15=3225,low_conf=True)
    assert not np.shares_memory(tensors['input'],image)
    rejected(lambda:validate_model(layers[:4]))
    for field in ('weight','bias','multiplier','shift'):
        broken=model(); del broken[1][field]; rejected(lambda:validate_model(broken))
    for field,dtype in (('weight',np.int16),('bias',np.int64),('multiplier',np.uint32),('shift',np.int32)):
        broken=model(); broken[2][field]=broken[2][field].astype(dtype); rejected(lambda:validate_model(broken))
    for field,value in (('weight',-128),('multiplier',0),('multiplier',-1),('shift',63)):
        broken=model(); broken[0][field].flat[0]=value; rejected(lambda:validate_model(broken))
    for bias in (INT32_MAX,INT32_MIN):
        broken=model(); broken[0]['weight'].flat[0]=127; broken[0]['bias'][0]=bias
        rejected(lambda:validate_model(broken),OverflowError)
    # Both exact legal INT32 bound endpoints remain accepted.
    bounded=model(); bounded[0]['weight'].flat[0]=127
    bounded[0]['bias'][0]=INT32_MAX-16129; validate_model(bounded)
    bounded[0]['bias'][0]=INT32_MIN+16129; validate_model(bounded)
    for value in (-1,256): rejected(lambda:run_network(image,layers,value))
    for value in (True,1.5): rejected(lambda:run_network(image,layers,value),TypeError)
    rejected(lambda:run_network(image.astype(np.uint8),layers,0))
    rejected(lambda:run_network(image[:,:,:63],layers,0))
    image[0,0,0]=-128; rejected(lambda:run_network(image,layers,0))
    print('PASS: full integer network independent bias/GAP/FC golden; schema, symmetric INT8 and overflow gates')


if __name__=='__main__': main()
