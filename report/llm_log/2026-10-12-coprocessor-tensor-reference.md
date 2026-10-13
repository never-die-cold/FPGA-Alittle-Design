# [2026-10-12] 协作记录：协处理器 int8_tensor_reference 模块——Conv / GAP / FC 整数算子参考

> 标签：#coprocessor #量化契约 #验证
> 平台：Codex（VS Code 插件，WSL）＋ OpenCode ｜ 模型：Codex = GPT-5 系列；OpenCode = deepseek-flash（deepseek/deepseek-flash）
> 相关 commit：`src/coprocessor/int8_tensor_reference.py` 改动 + `sim/coprocessor/test_int8_{conv_layer,gap_fc}.py` 随本轮同批提交

## 1. 任务与初始提示词

在已有标量/张量原语之上，补齐**整层算子**的整数参考，逐位对齐 C02 契约：完整 Conv 层（含 ReLU/requant），GAP（空间平均含舍入），signed FC（累加 + requant）。

## 2. 模型第一版方案

- `conv_relu_requant`：3×3、pad、stride、INT32 累加，per-channel requant + 饱和 + ReLU；
- `gap_16x16`：16×16 空间平均，**显式舍入**；
- `linear_requant`：signed FC，INT32 累加 + requant。

## 3. 失败现象（真实偏差与未决项，如实记录）

1. INT32 累加溢出 → 溢出闸拒绝；地址/padding/stride 需逐项覆盖。
2. **未决**：RTL/综合/端到端延迟未做；算子参考 PASS 只证明 Python 参考。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | Conv 层完整整数输出 | per-channel requant + ReLU | `conv_relu_requant` | ✅ `conv_layer` PASS |
| 2 | GAP/FC 语义 | 整数舍入 + signed 累加 | `gap_16x16` / `linear_requant` | ✅ `gap_fc` PASS |

## 5. 最终结论

Conv / GAP / FC 的整数算子参考完成，`test_int8_conv_layer`、`test_int8_gap_fc` PASS；与整网 schema/trace 串成 FastenerCNN 逐步黄金参考。**仍非 RTL。**

## 6. 经验沉淀

- 算子参考要覆盖**地址/padding/stride/累加溢出**与逐通道 requant；
- GAP 舍入必须显式（否则与 RTL 逐位对不齐）。 #skill候选
