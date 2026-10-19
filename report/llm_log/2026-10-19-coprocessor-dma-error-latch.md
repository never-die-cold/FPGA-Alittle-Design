# [2026-10-19] 协作记录：cop_dma_loader / cop_top 模块——数据载入错误锁存

> 标签：#coprocessor #验证 #架构决策
> 平台：Codex（VS Code 插件，WSL，夜间）＋ OpenCode ｜ 模型：Codex = GPT-5 系列；OpenCode = deepseek-flash（deepseek/deepseek-flash）
> 相关 commit：`07d5576`（J04-22）；总记录见 `2026-10-18-j04-closeout.md`（J04-22 段）

## 1. 任务与初始提示词

J04-22：DataMover 载入出现**短包 / 长度错 / payload CRC 不匹配**时，必须让错误对核/PS **可见**——输出单拍错误事件，并锁存为 **sticky `STATUS.ERROR`**（由核 W1C 清除），不能静默继续。

## 2. 模型第一版方案

- `cop_dma_loader`：每拍默认清 `error_o`，短包/长度错/CRC 失败产生**单拍** `error_o`。
- `cop_top`：`model_crc_error = loader_done && !load_kind && loader_crc32 != weight_crc32`；将其与短包错误一起锁存到 sticky `STATUS.ERROR`，由核 `W1C` 清除。

## 3. 失败现象（真实偏差与未决项，如实记录）

1. 无功能失败。
2. **未决**：CRC 不匹配负例与真实 36,032 B payload 的完整 CRC 由后续 P0 扩展；综合/上板未验证。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | 载入失败被静默 | 需单拍事件 | `dma_loader` error 脉冲 | ✅ `dma_loader` PASS |
| 2 | 错误需保持可见 | sticky + W1C | `cop_top` 锁存 STATUS.ERROR | ✅ `cop_top` PASS |

## 5. 最终结论

数据载入错误锁存落地：短包/长度错/CRC 不匹配 → 单拍事件 → sticky `STATUS.ERROR` → 核 W1C 清除；独立 `dma_loader`/`cop_top` 与 `all` PASS。硬件验证未做。

## 6. 经验沉淀

- 一次性错误用**单拍事件 + sticky 状态 + W1C** 三件套，既不丢也不重复；
- CRC 校验只应作用于 **weight payload**（`!load_kind`），别误判模型/ROI 载入。 #skill候选
