# 开工前准备清单（Prep Checklist）

> 目标：开工第一天直接进入 M1（两级流水基线跑通单条指令），不把时间耗在装环境上。
> 用法：完成一项打一个勾，负责人认领后把名字填在括号里。

## 🔴 必须完成（卡脖子项）

- [ ] **PYNQ 镜像烧录验证**（负责人：never-die-cold；依赖板子到货，issue #1）
  - 下载 PYNQ-Z2 v3.x 镜像烧 SD 卡
  - 通过标准：板子联网、Jupyter 可打开、base overlay 可加载、能点亮板载 LED
- [x] **RISC-V 工具链可用**（负责人：never-die-cold）
  - MSYS2 ucrt64 版 `riscv32-unknown-elf`（RV32IM，全队统一；安装与构建步骤见 [src/riscv_fw/README.md](../src/riscv_fw/README.md)）
  - 通过标准：能编译出 helloworld 的 elf 文件 ✅ 2026-09-11 跑通 elf/反汇编/hex（GCC 14.2.0，记录见 `report/llm_log/2026-09-11-riscv-toolchain.md`）

> 2026-09-11 收敛：原「PYNQ-Z2 板子落实来源」「Vivado 安装」两条移出本清单——板子已购置，到货跟踪见 issue #1；Vivado 为全员自备，进度见 issue #2。

## 🟡 建议完成（省后面时间）

- [ ] **报名状态核对**（负责人：never-die-cold）
  - fpgachina.cn 核对报名、赛道（AMD 自主选题·初级组）、官方时间节点
  - README 中日期沿用旧稿，一切以官网公告为准
- [ ] **加入官方 QQ 群 1087309750**，翻一遍往届答疑记录（负责人：never-die-cold）
- [ ] **三人仓库权限与 git 流程跑通**（负责人：全员）
  - 每人完成一次 clone / commit / push
  - 确认 commit message 约定（AI 产出注明 prompt 要点）
- [ ] **HDLBits 开刷**（负责人：全员）
  - 每人每天 5 题，开工前刷完 Verilog Language 部分
  - 直接对应决赛现场上机考核（细则与题型见 [exam_prep.md](exam_prep.md)）
- [ ] **《手把手教你设计 CPU》（蜂鸟 E203）流水线章节读完**（负责人：never-die-cold）

## 🟢 可选加分

- [x] **协作记录流程空跑一遍**（负责人：never-die-cold）
  - ✅ 2026-09-11 已产出多条真实记录（工具链、Vivado 选型、plan 合并、跳过野火板等），模板与 push 流程验证通过
- [ ] **固定每周例会与刷题时间**（负责人：全员）
  - **每周日下午固定 1.5h 决赛备考**：限时真题 / HDLBits 专题交替，题目与进度跟踪见 [exam_prep.md](exam_prep.md)
  - 工作日晚开发时段不被备考占用；三人课表对齐，例会互讲进度（答辩质询不分工）

---

> ✅ 全部🔴项完成 = 具备开工条件（2026-09-11：RISC-V 工具链已完成；仅剩镜像烧录待板到货，不阻塞 RTL/仿真开发）
