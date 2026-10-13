"""End-to-end structural and semantic checks for the integer executor."""
import numpy as np
from int8_model_reference import run_fastener_cnn
from test_int8_model_schema import make_layers


def reject(image, layers, min_margin_q):
    try:
        run_fastener_cnn(image, layers, min_margin_q)
    except ValueError:
        return
    raise AssertionError("invalid model execution input accepted")


def main():
    image = np.zeros((64, 64), dtype=np.int8)
    layers = make_layers()
    layers[4]["bias"][:] = [0, 5, 5]
    trace = run_fastener_cnn(image, layers, 1)
    expected_shapes = {"input": (1, 64, 64), "conv1": (16, 32, 32),
                       "conv2": (32, 32, 32), "conv3": (32, 16, 16),
                       "conv4": (64, 16, 16), "gap": (64,), "logits": (3,)}
    assert tuple(trace) == (*expected_shapes, "result")
    for name, shape in expected_shapes.items():
        assert trace[name].shape == shape
        assert trace[name].dtype == np.int8 and trace[name].flags.c_contiguous
    for name in ("conv1", "conv2", "conv3", "conv4", "gap"):
        assert np.count_nonzero(trace[name]) == 0
    assert trace["logits"].tolist() == [0, 5, 5]
    assert trace["result"] == {"class_id": 1, "margin_q": 0,
                               "score_q15": 0, "low_conf": True}
    assert not np.shares_memory(image, trace["input"])
    image[0, 0] = 9
    assert trace["input"][0, 0, 0] == 0
    reject(np.zeros((1, 64, 64), np.int8), make_layers(), 1)
    reject(np.zeros((64, 64), np.int16), make_layers(), 1)
    reject(np.zeros((64, 64), np.int8), make_layers(), True)
    bad = make_layers(); bad[0]["unknown"] = 1
    reject(np.zeros((64, 64), np.int8), bad, 1)
    print("PASS: FastenerCNN execution order, traces, shapes and result semantics")


if __name__ == "__main__":
    main()
