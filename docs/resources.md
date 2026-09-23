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
| AMD 赛道官方仓库（fpgachina26-amd） | https://gitee.com/Vickyiii/fpgachina26-amd | ⭐ 官方赛道入口：三赛道规则、选题指南全文（TRACK_GUIDE_2026.md）、开发板获取、技术支持；RTL/HLS 参考仓库 hlsagent2026 / rtlagent2026 亦由此索引 |

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

## 4. RTL / Verilog 基本功（日常开发）

| 资料 | 链接 | 备注 |
|:---|:---|:---|
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
| B 站搜索关键词 | "PYNQ-Z2"、"蜂鸟E203" | 📖 大量中文实操视频 |

---

## 9. 往届获奖作品与赛制调研（AMD 赛道）

- ⭐ [往届嵌赛 FPGA 赛道（AMD）获奖作品与赛制调研](amd_track_awards.md)
  - 2025 AMD 命题式基础赛道（HLS）国奖作品清单与得分、2024–2025 自主选题线索
  - 2026 AMD 自主选题赛道官方规则摘要（分组/工具/评分权重/开源要求）
  - 高价值资源：2026 选题指南全文（第三方整理）、国一路演视频
  - 对本项目 EdgeSight 的启示（创新性权重、PYNQ Skill 加分、实测数据要求等）
