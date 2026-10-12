"""Recompute the received model's counts; catch stale budget assumptions."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src/pynq_host"))
from inspection_model import PrototypeClassifier
from model_reference import folded_layers
from model_audit import audit_layers


def main():
    model = PrototypeClassifier(ROOT / "models/cnn-border-fill-best.pt").model
    result = audit_layers(folded_layers(model))
    assert [row["output_shape"] for row in result["layers"]] == [
        [16, 32, 32], [32, 32, 32], [32, 16, 16], [64, 16, 16], [64], [3]]
    assert [row["macs"] for row in result["layers"]] == [147456, 4718592, 2359296, 4718592, 0, 192]
    assert result["macs_per_roi"] == 11944128
    assert result["weight_elements"] == 32592 and result["bias_elements"] == 147
    assert result["fp32_parameter_bytes"] == 130956
    assert sum(parameter.numel() for parameter in model.parameters()) == 32883
    assert result["largest_output_elements"] == 32768 and result["adjacent_activation_elements"] == 49152
    assert result["layers"][4]["pool_additions"] == 64 * 255
    print("PASS: model audit 11944128 MAC/ROI, 32592 weights + 147 folded bias, 130956 FP32 bytes")


if __name__ == "__main__":
    main()
