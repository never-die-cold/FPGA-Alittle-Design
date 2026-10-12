# [2026-10-10] 协作记录：协处理器 C02 模块——整数与硬件契约（design_v0.md）

> 标签：#coprocessor #架构决策 #量化契约
> 平台：Codex（VS Code 插件，WSL）＋ OpenCode ｜ 模型：Codex = GPT-5 系列；OpenCode = deepseek-flash（deepseek/deepseek-flash）
> 相关 commit：本文件（`src/coprocessor/design_v0.md`）随本轮 G0 契约同批提交；总记录见 `2026-10-10-coprocessor-g0-contracts.md`

## 1. 任务与初始提示词

JL 负责离板计算链，要求**先做 G0 契约冻结、不写 RTL**：

> C02：FastenerCNN、64×64 灰度 ROI、per-channel 对称 INT8 权重、per-tensor 对称 INT8 激活、INT32 累加/bias、整数 multiplier+右移+饱和、8×16 MAC @100 MHz；先完整核对仓库现状，写草案与全部待拍板项。

## 2. 模型第一版方案

`src/coprocessor/design_v0.md` 冻结 C02 整数与硬件契约：首网 `FastenerCNN`；逐层形状（input→conv1–conv4→gap→logits，类别 `bolt/nut/washer`）；**per-channel 对称 INT8 权重 + per-tensor 对称 INT8 激活**；INT32 累加/bias；整数 `multiplier + 右移 + 饱和` requant；CHW/OIHW 规范排布与 C8/O16×I8 硬件排布；BRAM/DSP/周期预算；MAC 总量与拍数估算。

## 3. 失败现象（真实偏差与未决项，如实记录）

1. **延迟数字被误读**：`0.933 ms` 只是“总 MAC / 128 @100 MHz”的**理想下界**，被当成 128 MAC 延迟；按 O16×I8 调度重算为 **101,384 拍 ≈ 1.014 ms**（仍不含 GAP/DMA/控制/实现频率）。
2. **`uint8` ROI 可能被直接送 INT8**：预处理契约明确禁止 reinterpret → C02 单列 `p/255` 后按输入 scale 量化。
3. **score 字段缺整数语义**：协议只约束 0–1、模型无 softmax 硬件 → 推荐归一化 `top1−top2 margin`，明确非概率（并列待拍板）。
4. **未决**：正式 PTQ/QAT、逐层整数黄金、生产权重包、MAC/卷积 RTL、综合/时序/资源/实测延迟均未开始。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | “0.933 ms 是 128 MAC 延迟” | 那只是理想下界 | 按 O16×I8 调度重算 101,384 拍 | ✅ 文档修正 |
| 2 | `uint8` 直接进 INT8 | 契约禁止 reinterpret | 单列 `p/255` + 输入 scale 量化 | ✅ 写入契约 |
| 3 | score 无整数语义 | 无 softmax 硬件 | 归一化 margin，非概率 | ✅ 待拍板项登记 |

## 5. 最终结论

C02 契约冻结为 **v0 基线**（JL 2026-10-11 确认“契约已定稿”）：逐层形状、整数语义（对称 INT8/INT32/requant 饱和）、张量排布、资源与周期预算齐备。**仍不是 RTL、正式 INT8 模型或 M2 验收证据。**

## 6. 经验沉淀

- **理想下界 ≠ 调度拍数**：`总 MAC / 并行度` 只是下界，通道补齐 / tile 调度要另算；
- `uint8`→INT8 必须**显式量化**，不能 reinterpret；
- score 必须**声明数值含义**（margin/概率/阈值不是一回事）。 #skill候选
