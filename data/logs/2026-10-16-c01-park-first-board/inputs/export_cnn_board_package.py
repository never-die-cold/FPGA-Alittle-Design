"""Fold the frozen FP32 prototype checkpoint into a NumPy-only board package.

Loads models/cnn-border-fill-best.pt with the same strict metadata contract as
PrototypeClassifier, folds BN into convolutions via model_reference.folded_layers
(unmodified import), and saves one NPZ holding the four conv_relu layers'
OIIDHW weights/biases with strides/paddings plus the GAP/linear head and the
metadata needed to re-verify identity on the board (checkpoint sha256, classes,
preprocess version/mode, input size). A rebuild must be byte-equal.
"""
import hashlib
import io
import sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "sim/vision"))
sys.path.insert(0, str(ROOT / "src/pynq_host"))
sys.path.insert(0, str(ROOT / "src"))
import torch  # noqa: E402
from train_fastener_classifier import CLASSES, FastenerCNN  # noqa: E402
from roi_preprocess import PREPROCESS_VERSION  # noqa: E402
from model_reference import folded_layers  # noqa: E402

WEIGHTS = ROOT / "models/cnn-border-fill-best.pt"
OUTPUT = Path(__file__).resolve().parent / "cnn_board_package.npz"


def main():
    raw = WEIGHTS.read_bytes()
    checkpoint = torch.load(io.BytesIO(raw), map_location="cpu", weights_only=True)
    if (not isinstance(checkpoint, dict) or tuple(checkpoint.get("classes", ())) != CLASSES
            or checkpoint.get("input_size") != 64
            or checkpoint.get("architecture") != "fastener-4conv-bn-v1"
            or checkpoint.get("preprocess") != PREPROCESS_VERSION
            or checkpoint.get("preprocess_mode") != "border"):
        raise ValueError("model metadata does not match border/64 prototype contract")
    model = FastenerCNN()
    model.load_state_dict(checkpoint["state_dict"], strict=True)
    model.eval()
    layers = folded_layers(model)
    package = {
        "checkpoint_sha256": hashlib.sha256(raw).hexdigest(),
        "classes": np.array(CLASSES, dtype="U8"),
        "preprocess_version": np.array(str(PREPROCESS_VERSION)),
        "preprocess_mode": np.array("border"),
        "input_size": np.array(64),
    }
    for layer in layers:
        for key in ("weight", "bias", "stride", "padding", "name", "kind"):
            if key in layer:
                package[f"{layer['name']}_{key}"] = np.array(layer[key])
    np.savez(OUTPUT, **package)
    size = OUTPUT.stat().st_size
    print('EXPORTED: %s bytes=%d sha256=%s' % (OUTPUT, size, hashlib.sha256(OUTPUT.read_bytes()).hexdigest()))


if __name__ == '__main__':
    main()
