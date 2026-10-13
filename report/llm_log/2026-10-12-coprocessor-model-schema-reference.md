# [2026-10-12] 协作记录：协处理器 int8_model_reference 模块——FastenerCNN 整数参数 schema 与整网 trace

> 标签：#coprocessor #量化契约 #验证
> 平台：Codex（VS Code 插件，WSL）＋ OpenCode ｜ 模型：Codex = GPT-5 系列；OpenCode = deepseek-flash（deepseek/deepseek-flash）
> 相关 commit：`src/coprocessor/int8_model_reference.py` + `sim/coprocessor/test_int8_model_{schema,trace}.py` 随本轮同批提交

## 1. 任务与初始提示词

J02 整网层：把 FastenerCNN 的**整数参数 schema**（层序、形状、dtype、per-channel 参数）冻结为可校验结构，并提供**整网执行 / 逐步 trace**，作为后续 RTL 的逐位黄金参考。

## 2. 模型第一版方案

- `CONV_SPECS` 固定 `conv1–conv4` 的权重形状与 stride；`CONV_KEYS`/`LINEAR_KEYS` 固定字段集。
- `validate_fastener_layers` 校验：`bias`/`multipliers` 为 `int32` 且形状匹配、`multipliers>0`、`shifts` 为 `uint8` 且 `<=62`。
- 串整网：`conv_relu_requant` ×4 → `gap_16x16` → `linear_requant`，最终交给 `summarize_logits` 出结果。

## 3. 失败现象（真实偏差与未决项，如实记录）

1. schema 字段缺失 / dtype / 形状非法一律**拒绝**（定向负例覆盖）。
2. **未决**：正式 PTQ/QAT 权重、RTL、综合未开始。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | 层序/形状易错 | 用冻结 `CONV_SPECS` 校验 | 拒绝不合规层 | ✅ `model_schema` PASS |
| 2 | 整网执行需可对拍 | 逐步形状 + 结果语义 trace | 串 4 conv + GAP + FC | ✅ `model_trace` PASS |

## 5. 最终结论

FastenerCNN 整数参数 schema 与整网执行冻结为黄金参考；`test_int8_model_schema`、`test_int8_model_trace` 均 PASS。**仍非 RTL / 综合 / 端到端实测。**

## 6. 经验沉淀

- 把**层序/形状/dtype/per-channel 参数集**做成显式 schema 并校验，不一致直接拒绝；
- 整网用**逐步 trace**（每层形状 + 结果语义）对拍，便于 RTL 逐层比对。 #skill候选
