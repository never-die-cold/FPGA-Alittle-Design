# [2026-09-20] 协作记录：PYNQ-Z2 LED smoke test 真实上板（JTAG 下载）与记录/PR 口径纠偏

> 标签：#hardware #验证 #board #工具链
> 平台：OpenCode ｜ 模型：deepseek-flash
> 相关 commit：`d176493`（上板实测记录，PR #24 已由组长合并进 `main`）
> 用途：基准线承担的上板验证实做；「仿真 → 构建 → 真实上板」全链路闭环；Zynq JTAG 链选器件的踩坑

## 1. 任务与初始提示词

> "板子接的就是这台电脑，Vivado 2026.1 已经安装好可以使用……我现在只需要关于如何在板上验证测试项目的指令"

被测件 = `board/smoke_test/` 的 PYNQ-Z2 LED 流水灯（纯 PL，无 PS/overlay）。队友已完成 iverilog 仿真与 Vivado 构建（`BUILD PASSED`，证据 `data/logs/2026-09-20-pynq-z2-smoke-vivado/`），**仅差真实上板**。用户用 MobaXterm（串口 COM4 已登入板内 Linux），询问如何上板。

## 2. 模型第一版方案

给出 Vivado 命令行 JTAG 下载方案：

1. `build.tcl` batch 构建 bitstream（产物写 `C:\fpga_build`，不入库）；
2. `program_pl.tcl`：`open_hw_manager` → `connect_hw_server` → `open_hw_target` → `current_hw_device [lindex [get_hw_devices] 0]` → `set_property PROGRAM.FILE ...` → `program_hw_devices`；
3. 肉眼验收 LED 顺序移动 / BTN0 复位。

## 3. 失败现象（真实偏差）

1. **选错 JTAG 器件**：`[lindex [get_hw_devices] 0]` 取到 ARM 调试口，运行报
   `ERROR: [Labtoolstcl 44-10] Device arm_dap_0 is not programmable`。
2. **术语口径分歧**：队长指出"用的是 SD 卡烧录而不是 JTAG"，用户一度要求把记录改成 SD 卡。
3. **push 被拒**：把上板记录提交到 `dev/bench` 后 `git push` 报
   `! [rejected] dev/bench -> dev/bench (fetch first)`——远端已有同名同文件提交 `c8bd5fa`（更早的初稿）。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | `Device arm_dap_0 is not programmable` | Zynq 的 JTAG 链上同时存在 `arm_dap_0`（ARM DAP）与 `xc7z020_1`（PL），不能用 index 0 | 遍历 `get_hw_devices`，按 PART 过滤 `xc7z020*` 再编程 | ✅ `FOUND: xc7z020_1` → `*** PL PROGRAMMED ***` |
| 2 | "用 SD 卡烧录而不是 JTAG" | 概念混淆：SD 卡烧录=写 PYNQ Linux 镜像（系统启动，PS 侧）；JTAG=下载 `.bit` 配置 PL。实测确为 JTAG | 记录不改事实，增加"两种下载"对照表，明确区分两者 | ✅ 队长/用户认可口径 |
| 3 | push rejected (fetch first) | 远端 `dev/bench` 已有初稿 `c8bd5fa`，本地 `f70a628` 是其超集 | `git reset --soft origin/dev/bench` + 线性追加提交 `d176493`，**不强推** | ✅ push 成功，PR #24 head 更新 |
| 4 | 用户确认板上 LED/BTN0 现象正常 | — | 记录 commit `d176493`；PR #24 由组长合并进 main | ✅ 上板遗留项闭环 |

## 5. 最终结论

- 构建 `BUILD PASSED`；JTAG 下载 `FOUND: xc7z020_1` → `*** PL PROGRAMMED ***`；板上 LED 0→1→2→3 每 0.5 s 移动、BTN0 按住 LED0 常亮 → **上板 PASS**。
- 记录如实区分「SD 卡=系统启动 / JTAG=PL 下载」（`board/logs/2026-09-20-pynq-z2-smoke/README.md`，commit `d176493`，PR #24 已并入 `main`）。
- 与远端冲突采用 `reset --soft` 线性叠加，未 force push；bitstream SHA256 `AA65F0B1…C4B1`。

## 6. 经验沉淀

- 触发条件：在 Zynq（PS+PL 同一 JTAG 链）上用 hw_manager 配置 PL；或"实测方法与文档表述不一致" #skill候选
- 排查步骤：
  1. 先 `get_hw_devices` 列出全部器件与 PART，**按 PART 过滤**目标 PL（`xc7z020*`），不要用 `lindex 0`；
  2. 术语先对齐再记录：SD 卡烧录=系统启动、JTAG=PL 配置，两者不互替；**记录只写真发生的事**；
  3. 自己的 dev 分支可能已被他人/初稿推过——push 被拒先 `fetch` 再决定叠加，禁止 force push。
- 适用范围（换题目/换板卡是否成立）：成立；任何 PS+PL 异构 SoC 的 JTAG 上板、任何"文档要改但事实不同"的场景。
