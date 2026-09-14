# EdgeSight 备赛资料清单

> 按项目模块分类，标注了每条资料的用途和对应开发阶段。
> 优先级标记：⭐ 必读/必用　🔧 工具类随用随查　📖 学习类按需精读

---

## 0. 赛事官方

| 资料 | 链接 | 备注 |
|:---|:---|:---|
| 大赛官网（报名/赛程/公告） | http://www.fpgachina.cn/ | ⭐ 所有时间节点以此为准 |
| AMD 赛道咨询邮箱 | fpgacamp.cn@outlook.com | ⭐ 赛道规则问题直接问 |
| 竞赛交流 QQ 群 | 1087309750 | ⭐ 官方答疑群 |
| AMD 赛灵思中文社区论坛 | https://adaptivesupport.amd.com/ | 🔧 历史帖子含大量问题解答 |
| AMD 中国开发者平台（云资源申请） | https://developer.amd.com.cn/ | 验证窗口 GPU 云资源入口 |

---

## 1. AMD 工具链与官方文档（Vivado / HLS / 时序约束）

| 资料 | 链接 | 备注 |
|:---|:---|:---|
| Vivado 综合用户指南 UG901 | https://docs.amd.com/r/en-US/ug901-vivado-synthesis | ⭐ 综合属性、编码风格 |
| Vivado 实现用户指南 UG904 | https://docs.amd.com/r/en-US/ug904-vivado-implementation | 🔧 时序收敛、WNS 排查 |
| UltraFast 设计方法学 UG949 | https://docs.amd.com/r/en-US/ug949-vivado-design-methodology | ⭐ 时序约束与设计方法论，答辩常考点 |
| Vitis HLS 用户指南 UG1399 | https://docs.amd.com/r/en-US/ug1399-vitis-hls | 🔧 若协处理器用 HLS 实现 |
| AMD 官方 HLS 学习案例 | https://xilinx.github.io/xup_high_level_synthesis_design_flow/ | ⭐ 官方手把手教程 |
| AMD 技术文档总入口 | https://docs.amd.com/ | 🔧 查一切 UG/PG 文档 |

---

## 2. PYNQ 与 PYNQ-Z2 平台

| 资料 | 链接 | 备注 |
|:---|:---|:---|
| PYNQ 官方文档 | https://pynq.readthedocs.io/en/latest/ | ⭐ Overlay 加载、register_map、DMA 用法 |
| PYNQ GitHub 仓库 | https://github.com/Xilinx/PYNQ | ⭐ 源码 + issue 区查坑 |
| PYNQ-Z2 官方主页与资料 | https://www.pynq.io/boards.html | ⭐ 镜像下载、板卡文档 |
| PYNQ-Z2 参考手册（TUL 官方） | https://www.tul.com.tw/ProductsPYNQ-Z2.html | 🔧 原理图、引脚约束 |
| PYNQ 社区论坛 | https://discuss.pynq.io/ | 🔧 官方维护，回复质量高 |
| PYNQ-Z2 官方示例仓库 | https://github.com/Xilinx/PYNQ-Z2 | ⭐ 含 HDMI、基板 Overlay 参考设计 |

---

## 3. RISC-V 软核与流水线设计（模块一）

| 资料 | 链接 | 备注 |
|:---|:---|:---|
| RISC-V 官方规范（指令集手册） | https://riscv.org/technical/specifications/ | ⭐ RV32IM 指令定义的唯一权威来源 |
| riscv-arch-test 一致性测试 | https://github.com/riscv-non-isa/riscv-arch-test | ⭐ 内核验证基准 |
| 《手把手教你设计 CPU——RISC-V 处理器篇》配套代码 | https://github.com/riscv-mcu/e203_hbirdv1 | ⭐ 蜂鸟 E203，中文书 + 完整可综合 RTL，流水线/转发/分支预测实现的最佳中文参考 |
| PicoRV32 | https://github.com/YosysHQ/picorv32 | 🔧 极简 RV32 核，可读性极高，适合对照学习 |
| SERV（世界最小 RISC-V 核） | https://github.com/olofk/serv | 📖 位串行架构，开拓思路 |
| 一生一芯计划 | https://ysyx.oscc.cc/ | 📖 完整的中文处理器设计教学体系 |
| 《计算机体系结构基础》（胡伟武等，开源书） | https://foxsen.github.io/archbase/ | 📖 流水线、冒险、CPI 理论的中文权威教材 |
| riscv-gnu-toolchain | https://github.com/riscv-collab/riscv-gnu-toolchain | ⭐ 裸机程序编译工具链 |
| Dhrystone / CoreMark 基准 | https://github.com/embench/embench-iot | 🔧 CPI/性能测试参考（Embench 更现代） |

---

## 4. RTL / Verilog 基本功（上机考核 + 日常开发）

| 资料 | 链接 | 备注 |
|:---|:---|:---|
| HDLBits | https://hdlbits.01xz.net/ | ⭐⭐ 决赛上机考核的最佳刷题平台，时序/状态机/计数器全覆盖，带在线仿真 |
| Nandland | https://nandland.com/ | 📖 Verilog/VHDL 教程与常见模块写法 |
| ASIC-World | http://www.asic-world.com/verilog/ | 📖 经典 Verilog 语法参考 |
| ChipVerify | https://www.chipverify.com/ | 📖 语法 + testbench 写法，示例简洁 |
| Wavedrom（波形图绘制） | https://wavedrom.com/ | 🔧 写设计报告画时序图必备 |

---

## 5. HDMI 视频与图像处理（模块二）

| 资料 | 链接 | 备注 |
|:---|:---|:---|
| Digilent PYNQ-Z2 参考工程 | https://digilent.com/reference/programmable-logic/pynq-z2/start | 🔧 HDMI in/out 底层参考 |
| PYNQ-Z2 HDMI Overlay 示例 | https://github.com/Xilinx/PYNQ-Z2 | ⭐ 官方 HDMI 直通示例（在 base overlay 中） |
| FPGA4Fun | https://www.fpga4fun.com/ | 📖 小型 RTL 项目集，适合练手 |
| Project F（FPGA 图形与显示） | https://projectf.io/ | 📖 高质量 FPGA 视频/图形教程 |
| ZipCPU 博客 | https://zipcpu.com/ | 📖 硬核 FPGA 设计文章（AXI、形式验证） |

---

## 6. CNN 推理加速（模块三）

| 资料 | 链接 | 备注 |
|:---|:---|:---|
| FINN（Xilinx 量化神经网络加速器框架） | https://github.com/Xilinx/finn | ⭐ 面向 Zynq 的 INT8/二值网络加速，最重要的参考 |
| FINN 官方教程 | https://finn.readthedocs.io/ | ⭐ 从训练到部署全流程 |
| hls4ml | https://github.com/fastmachinelearning/hls4ml | 📖 神经网络→HLS 代码自动生成，思路可借鉴 |
| Vitis AI | https://github.com/Xilinx/Vitis-AI | 🔧 官方 AI 部署栈（本赛题用不到 DPU，但量化工具链可参考） |
| Vitis Libraries | https://github.com/Xilinx/Vitis_Libraries | 🔧 官方优化过的可复用算子库 |
| LeNet/MNIST（PyTorch 官方示例） | https://github.com/pytorch/examples | 🔧 训练 + INT8 量化（torch.ao.quantization）的起点 |

---

## 7. 计算机体系结构 / CPI 理论

| 资料 | 链接 | 备注 |
|:---|:---|:---|
| 《计算机组成与设计：RISC-V 版》（Patterson & Hennessy） | 图书馆/电商购买 | ⭐ 流水线、冒险、CPI、分支预测的标准教材，答辩理论依据 |
| 《计算机体系结构基础》开源版 | https://foxsen.github.io/archbase/ | ⭐ 胡伟武著，中文，免费下载 |
| RISC-V 中文社区 | https://riscv.org.cn/ | 📖 中文资讯与技术文章 |

---

## 8. 中文社区与学习平台

| 资料 | 链接 | 备注 |
|:---|:---|:---|
| 电子森林 | https://www.eetree.cn/ | 📖 FPGA 教学项目与板卡资料 |
| 硬禾学堂 | https://class.eetree.cn/ | 📖 FPGA 实战课程 |
| 与非网 FPGA 专区 | https://www.eefocus.com/ | 🔧 技术文章与行业资讯 |
| B 站搜索关键词 | "PYNQ-Z2"、"蜂鸟E203"、"HDLBits" | 📖 大量中文实操视频 |

---

## 9. 模块一学习路线资料清单（配合 src/riscv/plan.md）

> 按 plan.md 的阶段与三条支路组织：阶段 0 公共基础（全员）→ 支路一逻辑开发（阶段 1→2）→ 支路二调试验证（阶段 1→3）→ 支路三文档答辩（理论线）。与上文第 3/4/7 节有重叠的只列入口，不再重复。

### 9.1 阶段 0 公共基础：HDLBits + COAD 第 4 章 + RV32I 编码

| 资料 | 链接 | 备注 |
|:---|:---|:---|
| HDLBits 官网（全部题集） | https://hdlbits.01xz.net/ | ⭐ 阶段 0 主刷题平台 |
| HDLBits：Verilog Language 题集 | https://hdlbits.01xz.net/wiki/Verilog_Language | ⭐ 语法全部，每天 5 题 |
| HDLBits：Circuits → Sequential Logic 题集 | https://hdlbits.01xz.net/wiki/Sequential_Logic | ⭐ 锁存器/触发器/计数器/移位寄存器/FSM，上机考核对应 |
| 《计算机组成与设计：RISC-V 版》（Patterson & Hennessy）第 4 章 The Processor | 图书馆/电商购买；配套资源 https://www.elsevier.com/books/computer-organization-and-design-risc-v-edition/patterson/978-0-12-820331-6 | ⭐ 阶段 0 只看 4.1–4.5（单周期数据通路）；4.6–4.9 留到支路一阶段 2 |
| RISC-V 官方指令集手册（Unprivileged ISA） | 总入口 https://riscv.org/technical/specifications/；PDF 下载 https://github.com/riscv/riscv-isa-manual/releases | ⭐ 第 2 章 RV32I 是编码唯一权威来源 |
| RISC-V 指令编码速查卡（Reference Card） | https://github.com/jameslzhu/riscv-card | 🔧 阶段 0 自测（汇编↔机器码）随身查 |
| 中文辅助：B 站搜 "RV32I 指令编码" / "单周期 CPU 数据通路" | B 站 | 📖 手算编码卡壳时的中文讲解 |

**阶段 0 自测验收**（对应 plan.md）：HDLBits 能独立写状态机；能徒手画单周期 RV32I 数据通路并标控制信号；给定汇编指令能手算机器码、给定机器码能反汇编。

### 9.2 支路一：逻辑开发主线（阶段 1→2，对应 Part A/B）

| 资料 | 链接 | 备注 |
|:---|:---|:---|
| 《手把手教你设计 CPU——RISC-V 处理器篇》前 3 章 | https://github.com/riscv-mcu/e203_hbirdv1 | ⭐ 阶段 1 中文实践对照，随书源码 |
| PicoRV32 源码速读 | https://github.com/YosysHQ/picorv32 | 🔧 阶段 1 极简核对照，可读性最高 |
| riscv-gnu-toolchain 安装与使用 | https://github.com/riscv-collab/riscv-gnu-toolchain | ⭐ 阶段 1 工具链闭环（编译→反汇编→转 hex） |
| （练手）8 位迷你核：Nandland 教程 | https://nandland.com/ | 📖 阶段 1 可选练手，一天跑通加法/跳转 |
| COAD 第 4 章 4.6–4.9：流水线、冒险、旁路与停顿 | 同 9.1 COAD 条目 | ⭐ 阶段 2 理论核心 |
| 《计算机体系结构基础》（胡伟武）流水线章节 | https://foxsen.github.io/archbase/ | ⭐ 阶段 2 中文理论互证 |
| 蜂鸟 E203 流水线/转发章节精读 | 同上 E203 仓库 | ⭐ 阶段 2 工程实现参考（long-pipe 结构、旁路路径） |
| Vivado 逻辑仿真用户指南 UG900（XSim 波形操作） | https://docs.amd.com/r/en-US/ug900-vivado-logic-simulation | 🔧 阶段 2 波形阅读、气泡计数 |

### 9.3 支路二：调试验证线（阶段 1→3，对应 Part C 主测）

| 资料 | 链接 | 备注 |
|:---|:---|:---|
| riscv-gnu-toolchain（链接脚本实操） | GNU ld 官方手册 https://sourceware.org/binutils/docs/ld/ | 🔧 阶段 1 补 linker script；中文搜 "链接脚本 教程" |
| riscv-arch-test 一致性测试 | https://github.com/riscv-non-isa/riscv-arch-test | ⭐ 阶段 3：README 讲清编译与 signature 比对机制 |
| Dhrystone 原始实现 | https://github.com/Keith-S-Thompson/dhrystone | 🔧 阶段 3 benchmark 思路来源（整型运算/循环/函数调用） |
| CoreMark 基准 | https://github.com/eembc/coremark | 🔧 阶段 3 可选替代/对照 |
| Embench 嵌入式基准套件 | https://github.com/embench/embench-iot | 🔧 阶段 3 更现代的整型基准参考 |
| testbench 写法速查（ChipVerify） | https://www.chipverify.com/ | 🔧 阶段 1/3 自写 tb 规范 |
| Vivado 综合/实现用户指南（读报告、WNS 分析） | UG901 https://docs.amd.com/r/en-US/ug901-vivado-synthesis；UG904 https://docs.amd.com/r/en-US/ug904-vivado-implementation | ⭐ 阶段 3 时序分析、定位最差路径 |
| UltraFast 设计方法学 UG949（时序约束） | https://docs.amd.com/r/en-US/ug949-vivado-design-methodology | 🔧 阶段 3 约束与收敛方法论 |

### 9.4 支路三：文档与答辩线（理论深挖 + 记录工具）

| 资料 | 链接 | 备注 |
|:---|:---|:---|
| 阶段 0 三件套全通（HDLBits / COAD 4.1–4.5 / RV32I 编码） | 见 9.1 | ⭐ 答辩基础，任何模块都能讲清 |
| 《计算机体系结构基础》（胡伟武）全书 | https://foxsen.github.io/archbase/ | ⭐ CPI 推导、冒险分类的理论依据 |
| COAD 第 1 章（性能公式与 CPI） | 同 9.1 COAD 条目 | ⭐ "CPI 降低 ≥25%"指标的推导来源 |
| Wavedrom（波形/时序图绘制） | https://wavedrom.com/ | 🔧 设计报告画流水线时序图必备 |
| 蜂鸟 E203 书全本（讲清我们与 E203 的差异） | 同上 E203 仓库 | 📖 答辩"为什么不直接例化现成核"的论据 |
| 协作记录模板与流程 | 本仓库 `report/llm_log/` | ⭐ 每个设计决策点按模板留痕，标 `#skill候选` |

---

## 使用建议

1. **开工前（阶段 0）**：按第 9.1 节清单过一遍（约 1 周），HDLBits 刷完 Verilog Language + Sequential Logic，COAD 4.1–4.5 读完，RV32I 编码能互译
2. **开工后**：按自己支路走第 9.2 / 9.3 / 9.4 节清单；🔧 标记的放在浏览器书签栏随用随查
3. **写报告时**：UG949 + 《计算机组成与设计》是理论依据来源；所有实测数据引用原始日志
4. **每条踩坑**如果通过上述某个资料解决，记进 `report/llm_log/` 的经验沉淀节，注明出处

---

## 10. 前置验证开发板：野火 ZYNQ7010/7020（PYNQ-Z2 到货前的替身）

> 背景：2026-09 购置的 PYNQ-Z2 尚未到货，借到野火 ZYNQ7010/7020（XC7Z020）开发板做前置验证。决策全过程见 `report/llm_log/2026-09-08-wildfire-board-interim.md`。
> **核心结论：模块一可 100% 在野火板上完成（含上板验收）；模块二需做视频接口抽象层；模块三不受影响；PS 侧 PYNQ 上位机暂不可复刻，用 Vitis 裸机串口菜单过渡。最终指标必须在 PYNQ-Z2 上复测。**
>
> ⚠️ **2026-09-11 更新：跳过野火板前置验证，等 PYNQ-Z2 到货（issue #3 取消）。** 本节 10.1–10.4 保留备查，不再执行；排期影响与替代路径见 `report/llm_log/2026-09-11-skip-wildfire-board.md`。

### 10.1 两板差异速查

| 项目 | PYNQ-Z2（比赛目标板） | 野火 ZYNQ7010/7020（前置验证板） |
|:---|:---|:---|
| 主芯片 | XC7Z020-1CLG400C（-1 速度等级） | XC7Z020（速度等级以芯片丝印为准，需确认） |
| PL 资源 | 13,300 slices / 630KB BRAM / 220 DSP | ✅ 完全一致（同芯片） |
| DDR3 | 512MB，16 位 @1050Mbps | 2 片（容量以实物/资料为准，通常更大） |
| 视频接口 | HDMI 输入 + HDMI 输出 | LCD RGB888 FPC 座（未见 HDMI 口，以实物/原理图为准） |
| 以太网 | 1 路千兆 | 2 路 RJ45 |
| 工业接口 | 无 | RS232（DB9）、RS485 端子、RTC |
| 人机交互 | 4 LED / 4 按键 / 2 开关 / 2 RGB LED | 数码管、更多按键、LED |
| 扩展 | Arduino / 树莓派 / 2× Pmod | PL 端 2.54mm 排针 |
| 调试下载 | 单根 Micro-USB 搞定 JTAG+UART | 排针式 JTAG，需自备 Xilinx 兼容下载器 |
| 软件生态 | PYNQ v3.x 官方镜像（Jupyter） | 裸机 Vitis / PetaLinux / 野火 BSP，无现成 PYNQ 镜像 |

### 10.2 分模块适用性（对应 README 三大核心模块）

| 模块 | 野火板适用性 | 说明 |
|:---|:---|:---|
| 模块一：自研 RISC-V 核 | ✅ 完全适用 | SoC 外壳为纯 PL（BRAM 预载 hex + LED/UART），不碰 PS/DDR/HDMI/PYNQ；板子仅用于 JTAG 下载与上板验收（plan.md Part A）。仿真与 CPI 数据与板型无关；Fmax 报告同器件直接可比 |
| 模块二：HDMI 预处理流水线 | 🟡 需接口抽象层 | 行缓存/滤波/缩放/AXI-Stream 核心 RTL 零改动迁移；把"视频源/显示输出"做成可替换接口层，野火板上用 LCD 屏或内部 Test Pattern 验证，PYNQ-Z2 到手后换接 HDMI |
| 模块三：CNN 协处理器 | ✅ 完全适用 | 纯 PL（INT8 MAC 阵列 + 自定义指令 + AXI DMA），PS 仅跑 RISC-V 裸机调度 |
| PS 侧 PYNQ 上位机 | ❌ 暂不可复刻 | 过渡期：Vitis 裸机串口菜单读写 AXI-Lite 寄存器；黄金参考比对放 PC 离线做；`src/pynq_host/` 框架照 PYNQ 文档先写，真板到了联调 |

### 10.3 上野火板前的准备清单（已冻结）

> 2026-09-11：跳过野火板，本清单不再执行，保留备查。

- [x] ~~**Xilinx 兼容 JTAG 下载器**~~ 取消：现有下载器可用；最终板 PYNQ-Z2 板载 Micro-USB JTAG（Digilent SMT2），无需外购
- [ ] 野火资料包：底板原理图 + 引脚定义（写 XDC 用，模块一顶层仅 clk/LED/UART 少量引脚）
- [ ] 确认芯片速度等级丝印（-1/-2），Fmax 数据注明"器件+速度等级+测试板卡"
- [ ] 若走 LCD 验证路线：野火 RGB LCD 屏（或先用内部 Test Pattern 发生器）
- [ ] 核对 prep_checklist：PYNQ-Z2 最迟 10 月中旬到手（M3 全链路上板需要）

### 10.4 参考链接

| 资料 | 链接 | 备注 |
|:---|:---|:---|
| PYNQ-Z2 官方规格（AMD 大学计划） | https://www.amd.com/zh-tw/corporate/university-program/aup-boards/pynq-z2.html | ⭐ 目标板权威规格（-1 速度等级、512MB DDR3） |
| PYNQ 官方文档 | https://pynq.readthedocs.io/en/latest/ | ⭐ pynq_host 开发与（可选）board-agnostic 镜像移植 |
| 野火资料中心 | https://doc.embedfire.com/ | ⭐ 底板原理图、XDC/引脚定义、Linux BSP 教程入口 |
| 野火官网产品页 | https://www.embedfire.com/ | ZYNQ7010/7020 开发板资料下载 |
| Vivado 综合/实现用户指南 | 见 9.3 节 UG901/UG904 | Fmax/WNS 报告阅读（两板通用） |

---

## 11. 往届获奖作品与赛制调研（AMD 赛道）

- ⭐ [往届嵌赛 FPGA 赛道（AMD）获奖作品与赛制调研](amd_track_awards.md)
  - 2025 AMD 命题式基础赛道（HLS）国奖作品清单与得分、2024–2025 自主选题线索
  - 2026 AMD 自主选题赛道官方规则摘要（分组/工具/评分权重/开源要求）
  - 高价值资源：决赛 Verilog 上机真题（2019–2025）、2026 选题指南全文（第三方整理）、国一路演视频
  - 对本项目 EdgeSight 的 6 条启示（创新性权重、PYNQ Skill 加分、实测数据要求等）
