# data/golden/vision —— 视觉流水线黄金参考

各级 RTL 对拍用输入/输出向量（hex），目录按流水线级划分：
`rgb2gray` / `gaussian3x3` / `sobel` / `scaler` / `scaler_ds` / `osd` / `localize` / `fullchain`。

- 对拍入口：`sim/` 内对应 testbench 与脚本，以 `sim/scripts/` 一键入口为准。
- 生成方式：`localize/` 含 `gen_patterns.py`（生成 `patterns_*.hex`）与 `reference.py`（软件参考）；
  其余各级以各自 tb/脚本内的生成逻辑为准。
- 边界：这些是 RTL 对拍黄金，不是模型精度证据；golden 匹配不等于实机验收。
