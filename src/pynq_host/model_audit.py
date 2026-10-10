"""Exact shape/MAC/parameter counts for the folded software reference."""
import math


def audit_layers(layers):
    shape, rows = [1, 64, 64], []
    previous, adjacent_peak = math.prod(shape), 0
    for layer in layers:
        inputs = list(shape)
        weights = biases = macs = additions = divisions = 0
        if layer["kind"] == "conv_relu":
            out_channels, in_channels, kh, kw = layer["weight"].shape
            if shape[0] != in_channels:
                raise ValueError("audit channel mismatch")
            shape = [out_channels] + [(shape[axis + 1] + 2 * layer["padding"][axis] - kernel)
                                     // layer["stride"][axis] + 1 for axis, kernel in enumerate((kh, kw))]
            weights, biases = layer["weight"].size, layer["bias"].size
            macs = math.prod(shape) * in_channels * kh * kw
        elif layer["kind"] == "global_average":
            additions, divisions = shape[0] * (shape[1] * shape[2] - 1), shape[0]
            shape = [shape[0]]
        elif layer["kind"] == "linear":
            if shape != [layer["weight"].shape[1]]:
                raise ValueError("audit linear input mismatch")
            weights, biases = layer["weight"].size, layer["bias"].size
            shape, macs = [layer["weight"].shape[0]], weights
        else:
            raise ValueError("unknown audit operator")
        elements = math.prod(shape)
        if min(shape) < 1:
            raise ValueError("invalid audit output shape")
        adjacent_peak = max(adjacent_peak, previous + elements)
        previous = elements
        rows.append({"name": layer["name"], "kind": layer["kind"], "input_shape": inputs,
                     "output_shape": list(shape), "weights": weights, "biases": biases,
                     "macs": macs, "bias_additions": elements if biases else 0,
                     "pool_additions": additions, "pool_divisions": divisions,
                     "fp32_parameter_bytes": 4 * (weights + biases), "output_elements": elements})
    return {"layers": rows, "macs_per_roi": sum(row["macs"] for row in rows),
            "weight_elements": sum(row["weights"] for row in rows),
            "bias_elements": sum(row["biases"] for row in rows),
            "fp32_parameter_bytes": sum(row["fp32_parameter_bytes"] for row in rows),
            "largest_output_elements": max(row["output_elements"] for row in rows),
            "adjacent_activation_elements": adjacent_peak,
            "scope": "counts only; excludes framework/workspace/scale/IO and scheduling overhead"}
