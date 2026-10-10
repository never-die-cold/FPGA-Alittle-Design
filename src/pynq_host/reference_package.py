"""Export the FP32 software reference, full layer goldens and portable checker."""
import json
import platform
from pathlib import Path
import numpy as np
import torch
from inspection_model import PrototypeClassifier
from model_reference import folded_layers, original_trace
from model_audit import audit_layers
from numpy_reference import reference_trace, RTOL, ATOL
from reference_tensors import write_tensor, sha256


def export_reference(weights, output):
    output = Path(output).resolve()
    if output.exists():
        raise ValueError("reference output already exists; choose a new directory")
    torch.set_num_threads(4)
    classifier = PrototypeClassifier(weights)
    layers = folded_layers(classifier.model)
    crops = {"zero": np.zeros((64, 64), np.uint8),
             "seed2026": np.random.default_rng(2026).integers(0, 256, (64, 64), dtype=np.uint8),
             "stripes": np.tile(np.array([0, 255], np.uint8), (64, 32))}
    expected = original_trace(classifier.model, list(crops.values()))
    agreement = {}
    for index, (name, crop) in enumerate(crops.items()):
        actual = reference_trace(crop, layers)
        agreement[name] = {}
        for stage, values in expected.items():
            np.testing.assert_allclose(actual[stage], values[index], rtol=RTOL, atol=ATOL)
            agreement[name][stage] = float(np.max(np.abs(actual[stage] - values[index])))
        if actual["logits"].argmax() != expected["logits"][index].argmax():
            raise ValueError("reference argmax mismatch")
    root = Path(__file__).resolve().parents[2]
    sources = ["src/pynq_host/" + name + ".py" for name in
               ("inspection_model", "model_reference", "model_audit", "numpy_reference", "reference_tensors", "reference_package")]
    sources += ["sim/vision/train_fastener_classifier.py", "sim/vision/check_model_reference.py"]
    manifest = {"schema_version": 1, "mode": "FP32_SOFTWARE_REFERENCE", "hardware_connected": False,
                "model": classifier.metadata, "rtol": RTOL, "atol": ATOL, "audit": audit_layers(layers),
                "oracle": "original PyTorch model; evaluation BN retained", "truth_labels": None,
                "input_kind": "diagnostic pixels; no dataset accuracy claim", "hex": "uint8 pixels or IEEE754 FP32; not INT8 weights",
                "runtime": {"python": platform.python_version(), "numpy": np.__version__, "torch": str(torch.__version__)},
                "code_sha256": {name: sha256((root / name).read_bytes()) for name in sources},
                "agreement_max_abs": agreement, "layers": [], "tensors": {}, "cases": [], "tools": {}}
    output.mkdir(parents=True, exist_ok=False)
    for layer in layers:
        row = {key: value for key, value in layer.items() if key not in ("weight", "bias")}
        for key, layout in (("weight", "OIHW" if layer["kind"] == "conv_relu" else "OI"), ("bias", "O")):
            if key in layer:
                name = layer["name"] + "_" + key
                manifest["tensors"][name] = write_tensor(output, name, layer[key], layout)
                row[key] = name
        manifest["layers"].append(row)
    for index, (name, crop) in enumerate(crops.items()):
        pixels = name + "_pixels"
        manifest["tensors"][pixels] = write_tensor(output, pixels, crop, "HW")
        case = {"name": name, "pixels": pixels, "expected": {}, "predicted_class": classifier.metadata["classes"][int(expected["logits"][index].argmax())]}
        for stage, values in expected.items():
            key = name + "_" + stage
            manifest["tensors"][key] = write_tensor(output, key, values[index], "CHW" if values[index].ndim == 3 else "C")
            case["expected"][stage] = key
        manifest["cases"].append(case)
    (output / "tools").mkdir()
    for source in sources:
        if Path(source).name not in ("numpy_reference.py", "reference_tensors.py", "model_audit.py", "check_model_reference.py"):
            continue
        filename, raw = "tools/" + Path(source).name, (root / source).read_bytes()
        (output / filename).write_bytes(raw)
        manifest["tools"][filename] = sha256(raw)
    raw = (json.dumps(manifest, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()
    (output / "manifest.sha256").write_text(sha256(raw) + "\n", encoding="ascii")
    (output / "manifest.json").write_bytes(raw)
    return manifest
