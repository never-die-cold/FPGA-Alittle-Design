# [2026-10-12] 协作记录：协处理器 int8_result_reference 模块——类别 / margin / score_q15 / low_conf 语义

> 标签：#coprocessor #量化契约 #验证
> 平台：Codex（VS Code 插件，WSL）＋ OpenCode ｜ 模型：Codex = GPT-5 系列；OpenCode = deepseek-flash（deepseek/deepseek-flash）
> 相关 commit：`src/coprocessor/int8_result_reference.py` + `sim/coprocessor/test_int8_result.py` 随本轮同批提交

## 1. 任务与初始提示词

冻结 C02 的**最终结果语义**（要求**无浮点**）：`class_id`、`margin_q`、`score_q15`、`low_conf`，供驱动/工单判定与 RTL 结果通道对齐。

## 2. 模型第一版方案

`summarize_logits(logits, min_margin_q)`：
- 3 个 INT8 logits；按 `(-logit, class_id)` 排序，**tie-break 取较小 class**；
- `class_id = top1`；`margin_q = logits[top1] − logits[top2]`；
- `score_q15 = (margin_q*32767 + 127) // 254`（INT8 全范围映射到 Q15）；
- `low_conf = margin_q < min_margin_q`。

## 3. 失败现象（真实偏差与未决项，如实记录）

1. logits 类型/形状非 `INT8[3]`、`min_margin_q` 越界（`[0,254]`）一律**拒绝**。
2. **未决**：RTL 结果通道、板端验收未做。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | 并列类别如何取舍 | 固定 tie-break 规则 | 排序键 `(-logit, id)`，取较小 id | ✅ `result` PASS |
| 2 | score 用浮点 | 必须整数 | Q15 整数公式 | ✅ `result` PASS |
| 3 | 低置信判定 | margin 阈值 | `low_conf = margin_q < min_margin_q` | ✅ `result` PASS |

## 5. 最终结论

结果语义冻结为**纯整数实现**，`test_int8_result` PASS。score 明确为 **Q15 的 margin**（非概率）；并列与阈值都有确定规则。

## 6. 经验沉淀

- 评测结果语义必须**无浮点**、**显式 tie-break**、**显式阈值**；
- `score` 要声明为 `margin` 的 Q15 编码，**不能与概率/softmax 混为一谈**。 #skill候选
