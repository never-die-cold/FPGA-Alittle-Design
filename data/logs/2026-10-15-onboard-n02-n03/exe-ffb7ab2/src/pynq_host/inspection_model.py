"""CPU-only loader for the received FP32 prototype; not a deployment model."""
import hashlib
import io
import sys
from pathlib import Path
import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "sim/vision"))
from train_fastener_classifier import CLASSES, FastenerCNN
from roi_preprocess import PREPROCESS_VERSION


class PrototypeClassifier:
    def __init__(self, weights):
        path = Path(weights).resolve()
        raw = path.read_bytes()
        checkpoint = torch.load(io.BytesIO(raw), map_location="cpu", weights_only=True)
        if (not isinstance(checkpoint, dict) or tuple(checkpoint.get("classes", ())) != CLASSES
                or checkpoint.get("input_size") != 64
                or checkpoint.get("architecture") != "fastener-4conv-bn-v1"
                or checkpoint.get("preprocess") != PREPROCESS_VERSION
                or checkpoint.get("preprocess_mode") != "border"):
            raise ValueError("model metadata does not match border/64 prototype contract")
        self.model = FastenerCNN()
        self.model.load_state_dict(checkpoint["state_dict"], strict=True)
        self.model.eval()
        self.metadata = {"name": path.name, "sha256": hashlib.sha256(raw).hexdigest(),
                         "architecture": checkpoint["architecture"], "classes": list(CLASSES),
                         "preprocess": PREPROCESS_VERSION, "input_size": 64, "precision": "FP32"}

    def predict(self, crops):
        if not crops:
            return []
        if any(not isinstance(crop, np.ndarray) or crop.dtype != np.uint8
               or crop.shape != (64, 64) for crop in crops):
            raise ValueError("model requires uint8 64x64 crops")
        images = torch.from_numpy(np.stack(crops).astype(np.float32)[:, None] / 255)
        with torch.inference_mode():
            probabilities = self.model(images).softmax(dim=1)
        if not torch.isfinite(probabilities).all():
            raise ValueError("nonfinite model output")
        return [{"class": CLASSES[int(row.argmax())], "score": float(row.max()),
                 "probabilities": [float(value) for value in row]} for row in probabilities]
