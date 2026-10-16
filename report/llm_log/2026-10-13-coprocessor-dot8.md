# [2026-10-13] 协作记录：协处理器 dot8 模块——8 路 signed 乘积平衡求和树

> 标签：#coprocessor #架构决策 #时序优化 #验证
> 平台：Codex（VS Code 插件，WSL）＋ OpenCode ｜ 模型：Codex = GPT-5 系列；OpenCode = deepseek-flash（deepseek/deepseek-flash）
> 相关 commit：`f9a44db`（J03 dot8 reduction tree）；本文档随本轮补录提交

## 1. 任务与初始提示词

把 **8 个 signed INT8 乘积**用**固定位宽平衡树**归约，输出 signed 19 位和，供 `mac_array` 复用。

## 2. 模型第一版方案

`generate` 例化 8× `mac_lane`（`act_i[8*lane +: 8]`、`weight_i[8*lane +: 8]` → `product_bus[16*lane +: 16]`）；两级平衡加法：`sum01..sum67`（signed 17b）→ `sum0123/sum4567`（signed 18b）→ `sum_o`（signed 19b），每级**显式符号扩展**。

## 3. 失败现象（真实偏差与未决项，如实记录）

1. 关键在**平衡树 vs 串行链**（降逻辑深度）与**逐级符号扩展位宽**。
2. **未决**：时序/综合/资源未验证。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | 串行加法链深 | 改平衡树 | 两两相加两级 | ✅ `tb_dot8` 5 向量 PASS |
| 2 | 符号扩展位宽 | 每级扩 1 位 | `{sum[16], sum}` 等 | ✅ |

## 5. 最终结论

`dot8` 落地：8 路 signed 乘积经平衡树归约为 signed 19 位和；`test` 5 向量 PASS。

## 6. 经验沉淀

- 多路求和用**平衡树**而非串行，减小逻辑深度；
- 每级加法**显式符号扩展**，避免位宽/符号错误。 #skill候选
