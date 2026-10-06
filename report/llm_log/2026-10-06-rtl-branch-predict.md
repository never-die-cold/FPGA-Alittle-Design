# [2026-10-06] 协作记录：branch_predict 模块——64 项三档方向 BHT

> 标签：#riscv #流水线 #架构决策 #验证
> 平台：Codex（VS Code 插件，WSL）＋ OpenCode ｜ 模型：Codex = GPT-6 Astra（gpt-6-astra）；OpenCode = deepseek-flash（deepseek/deepseek-flash）
> 相关 commit：本模块（`src/riscv/branch_predict.v` + `sim/riscv/tb_branch_predict.v`）与契约 §16/D17 同批提交

## 1. 任务与初始提示词

启动 Part C：给核加**可切换分支预测**，减少控制气泡。要求先把契约冻结（`design_v1.md` §16 / D10 / D17），再落 RTL：**同一 RTL 顶层参数切关闭/1-bit/2-bit**、命中率要有来源、禁止复制源码、不改 ISA/异常/存储器接口。

## 2. 模型第一版方案

`branch_predict.v`：
- 参数 `BHT_MODE`（0=关闭 / 1=1-bit / 2=2-bit）、`INDEX_BITS=6`（64 项）；
- 索引 `pc[INDEX_BITS+1:2]`（即 `pc[7:2]`，4 字节对齐、跳过字节偏移）；
- 1-bit 表 `reg bht[]`；2-bit **饱和计数器**（00/01/10/11，饱和不溢出）；
- `lookup` 组合输出 `predict_taken = lookup_state[1]`、`lookup_state`；`update` 在时钟沿按 `update_taken` 更新（2-bit 饱和加减）；
- 关闭档 `predict_taken` 恒 0。

## 3. 失败现象（真实偏差与未决项，如实记录）

1. 无功能失败；**未决**：XSim / Vivado WNS/资源、实机与 125 MHz 仍由验证/上板线执行。
2. 命中率**由 tb 层次化事件统计**（片上不放大计数器，避免污染资源/Fmax）。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | 三档要单变量可比 | 顶层参数切换、禁止复制 | `BHT_MODE` 0/1/2 `generate` | ✅ `tb_branch_predict` 21 checks PASS |
| 2 | 2-bit 要抗单次抖动、饱和不溢出 | 00/11 边界不加不减 | 饱和加减逻辑 | ✅ 单元覆盖翻转/饱和 |
| 3 | 索引要对齐 | 用 `pc[7:2]` 取 64 项 | `INDEX_BITS=6` | ✅ |
| 4 | 命中率要有来源 | tb 层次化事件线 + 自洽断言 | `bp_lookup/hit/miss_event` | ✅ `hit+miss=lookup`、关闭档 `lookup=0` |

## 5. 最终结论

`branch_predict.v` 三档 BHT 落地：64 项、1-bit/2-bit 饱和计数器、关闭档恒不跳。单元 tb **21 checks PASS**。CoreMark 命中率：**1-bit 1,587,055/1,854,101 = 85.6%**；**2-bit 1,690,538/1,854,101 = 91.2%**；关闭档 `lookup=0`（显著优于无预测）。外部时序/资源待验证。

## 6. 经验沉淀

- BHT 用**顶层参数切三档**、索引 `pc[7:2]`；2-bit 饱和计数器抗单次抖动；
- 命中率用 **tb 层次化事件线**统计，断言 `hit+miss=lookup`、关闭档 `lookup=0`——数据有来源且不占片上资源。
- #skill候选
