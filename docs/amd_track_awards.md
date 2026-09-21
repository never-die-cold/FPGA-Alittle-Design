# 往届嵌赛 FPGA 赛道（AMD）获奖作品与赛制调研

> 调研日期：2026-09-11（第 9 届比赛进行中）
> 数据来源：GitHub 搜索 API + 获奖作品仓库公开自述 + 2026 官方选题指南（第三方逐页转录）
> ⚠️ 可信度说明：官方获奖名单页面（fpgachina.cn）有反爬/JS 渲染，未能直接抓取。下表奖项均来自**作品仓库/作者自述**，未经官方逐条核验；引用时请注明来源。官方原件下载入口：<http://www.fpgachina.cn/?page=download>

---

## 1. 先分清"AMD 赛道"的三层结构

FPGA 创新设计赛道由多家企业出题，2026 年共 **7 家企业 / 24 项一级选题 / 139 页选题指南**（AMD / 紫光同创 / 安路 / 高云 / 易灵思 / 复旦微 / 中科亿海微）。AMD 一家的选题方向：

| 年份（届） | AMD 赛道结构 |
|:---|:---|
| 2026（第 9 届） | ① RTL/HLS 本地智能体设计赛道 ② 具身智能赛道（AI PC + FPGA） ③ **自主选题赛道（初级组 / 高级组）← 本项目所在** |
| 2025（第 8 届） | AMD 命题式基础赛道（仓库命名 `hlstrack2025_*`）：初赛为 Vitis HLS 算子优化三题（SHA-256 / LZ4 / Cholesky），决赛为延伸设计题 |
| 2024（第 7 届） | 已有 AMD 命题式基础赛道（有选手连续参加 2024、2025 两届） |
| 其他杯赛 | 紫光同创、高云、安路、易灵思、复旦微、中科亿海微（各设题目，作品技术栈以纯 RTL 为主） |

> 结论：搜索"往届 AMD 获奖作品"时，2024–2025 大量命中是 **HLS 命题赛道**，与本项目"自主选题 + 自研 RTL"不同；自主选题赛道公开开源作品较少（见 §3）。

---

## 2. AMD 命题式基础赛道（2025）获奖作品（GitHub 可查）

### 2.1 赛道规则要点（来自公开仓库中的《初赛手册》）

- 参赛对象：大一至大三本科生；目标器件 `xc7z020-clg484-1`（Zynq-7000，即 PYNQ-Z2 器件）
- 工具：Vitis HLS 2024.2；指标 `T_exec = Clock_Period × Cosim_Latency`，越小越好
- 三题：SHA-256 / LZ4 Compress / Cholesky(Complex)，必须过 C Simulation 与 Co-simulation
- 时序违例单题扣 10 分；**官方鼓励使用 LLM 辅助优化**（DeepSeek-Coder、Qwen-Coder 等）

### 2.2 获奖作品清单

| 奖项 | 作品/仓库 | 技术要点 | 来源 |
|:---|:---|:---|:---|
| **全国一等奖** | [hongpengWu/hlstrack2025_40562](https://github.com/hongpengWu/hlstrack2025_40562) | 初赛三题成绩：sha256 6109ns(73.09)、lz 19923ns(68.53)、Cholesky 6221ns(94.3)，归一化 78.9；决赛选项三：SR-UKF 硬件加速（含 YOLO+UKF 追踪工程、PYNQ Notebook 软/硬件双版本） | 仓库自述 |
| **全国二等奖** | [teresasousa585-max/fpga-innovation-competition-amd-2025](https://github.com/teresasousa585-max/fpga-innovation-competition-amd-2025) | 初赛 HMAC-SHA256+LZ4+Cholesky；决赛 Zynq-7000 实时频谱仪：32MSPS ADC → DDC(NCO/积分抽取) → Hann 窗+可配置 FFT → AXI DMA → PYNQ，另支持 UDP 音频输入；HLS 2024.2 / Vivado 2025.2 | 仓库自述 |
| **全国二等奖（决赛）** | [VincentttWang/FPGA_SocChina_2025](https://github.com/VincentttWang/FPGA_SocChina_2025) | PYNQ-Z2 全栈实时音频处理：4096 点 FFT + FIR 的 HLS IP，Stream Dataflow 架构 SSR=2，PyQt5/Web 双上位机可视化 | 仓库自述 |
| 全国二等奖（初赛） | [VincentttWang/hlstrack2025_44844](https://github.com/VincentttWang/hlstrack2025_44844)、[honghongv/hlstrack2025_44057](https://github.com/honghongv/hlstrack2025_44057) | 三算子 HLS 优化 | 仓库自述 |
| 全国三等奖 | [Su-gif-cpu/hlstrack2025_43478](https://github.com/Su-gif-cpu/hlstrack2025_43478)、[ceasonen/hlstrack2025-44686](https://github.com/ceasonen/hlstrack2025-44686)、[Foxywort/hlstrack2025_41622](https://github.com/Foxywort/hlstrack2025_41622)、[milk-dragon666/hlstrack2025_46586](https://github.com/milk-dragon666/hlstrack2025_46586)、[Shaojie-bit/hlstrack2025_44192](https://github.com/Shaojie-bit/hlstrack2025_44192) | HLS 三算子优化；`milk-dragon666` 报告：循环展开/流水线/数组分区/DATAFLOW，三项延迟均降约 60–67%，并完整记录 LLM 辅助优化过程 | 仓库自述 |
| 未进决赛 | [Okinami2/hlstrack2025_40923](https://github.com/Okinami2/hlstrack2025_40923) | 同赛道参赛记录 | 仓库自述 |

> 其他相关：`Benzene-k/hlstrack2025-43205` 用 FPGA 加速 YOLOv3-Tiny 交通标志检测（8-bit 量化）；初赛题目、评分细则、决赛延伸题（UKF / 频谱仪 / 音频）都可在上述仓库找到完整资料。

**技术共性**：HLS `DATAFLOW` 流式架构、SSR（每拍多采样）、数组分区、Vitis L1 库二次开发、AXI DMA、PS+PL 协同、PYNQ 可视化、延迟/资源对比表。

---

## 3. AMD 自主选题相关获奖作品线索（2024–2025，待核验）

`fpgachina2025_*` 命名仓库中，基于 PYNQ/ZCU104 的自主选题类作品（赛道归属未逐条核验）：

| 仓库 | 内容 | 备注 |
|:---|:---|:---|
| [cxwTony/fpgachina2025_45594](https://github.com/cxwTony/fpgachina2025_45594) | 基于 3DGS 的实时 SLAM：Vitis HLS 改版 3DGS + AMD ZCU104 + PYNQ | HLS 2024.2，含完整 platform/overlay/notebook |
| [paulgeorge66/fpgachina2025_49257](https://github.com/paulgeorge66/fpgachina2025_49257) | 异构加速肺结节检测系统 | 作者标注"2025 FPGA 大赛国三作品" |
| [brandon-lee-bo/fpgachina2025_47488](https://github.com/brandon-lee-bo/fpgachina2025_47488) | 面向稀疏矩阵-稠密矩阵乘的行数据流向量处理器 | VHDL |
| [THEM-bot/fpgachina2025_41737](https://github.com/THEM-bot/fpgachina2025_41737) | 2025 年 FPGA 创新设计赛道 41737 队作品开源 | 内容待核 |

> 观察：自主选题赛道公开开源比例明显低于命题赛道（命题赛道自带模板、更倾向开源）。**本项目的自研 RISC-V 核 + 视觉 SoC 在公开作品中属于稀缺方向**，可作为差异化卖点。

---

## 4. 其他杯赛高价值参考（图像/视频/RTL 重度相关）

| 作品 | 成绩 | 与本项目相关性 |
|:---|:---|:---|
| [Floatkyun/Ultra-Vision](https://github.com/Floatkyun/Ultra-Vision)（2024，易灵思） | 国一 + 易灵思创新杯 | ⭐ 无极缩放：640×480@60 输入 → 1080P@60 / 2K@50 输出，缩放步长 1 像素，含时延指标与架构海报——直接对标模块二（缩放/预处理） |
| [maojinxiang/FPGA-ANLU-National-First-Prize](https://github.com/maojinxiang/FPGA-ANLU-National-First-Prize)（2025，安路） | 国一 | ⭐ OV5640 采集 + SDRAM 帧缓存 + 实时图像处理 + 千兆 UDP + HDMI 双板系统——对标模块二/三的接口与缓存设计 |
| [InitialXE/Multi-Function-Image-Processing-PLAT](https://github.com/InitialXE/Multi-Function-Image-Processing-PLAT)（2024，安路） | 国二 | Hu 不变矩手势识别，图像算法硬件化参考 |
| [Thes0me/pango_video_local_dimming](https://github.com/Thes0me/pango_video_local_dimming)（2022，紫光同创） | 赛道作品 | 视频色度/亮度提取 |
| [BigPig-Bro/udp_gmii_ov5640](https://github.com/BigPig-Bro/udp_gmii_ov5640)（2023，高云） | 赛道作品 | 多路网络视频监控编码 |
| [xiaoan109/Pango-FPGA](https://github.com/xiaoan109/Pango-FPGA)（2024，紫光同创） | 赛道作品 | 第七届紫光同创杯 |

---

## 5. 高价值公共资源（强烈建议全员使用）

| 资源 | 说明 |
|:---|:---|
| [nbstarhkc/Qian-Sai](https://github.com/nbstarhkc/Qian-Sai) | ⭐ 2026 官方选题指南整理：7 企业 24 选题 139 页全文（AMD 指南 28 页含 PDF/逐页 TXT），附在线可视化；来源标注为官网下载中心 |
| [Ultra-Vision 路演视频](https://www.bilibili.com/video/BV1WjzsY2E4v/?p=1) | 2024 国一 + 企业杯获奖作品答辩演示（B 站） |
| 官方下载中心 | <http://www.fpgachina.cn/?page=download>（选题指南与通知原件） |

---

## 6. 2026 AMD 自主选题赛道规则摘要（本项目所在，官方指南要点）

来自 2026 AMD 选题指南 §3.3（第三方逐页转录，建议核对官方 PDF）：

> ✅ **2026-09-14 交叉核验**：团队会议对官方 7 份 PDF 全量提取的摘要（见 [`docs/track_guides_2026_summary.md`](track_guides_2026_summary.md)）与本节第三方转录**逐项一致**（评分权重 30/20/20/15/15、初级组器件范围、协作记录与技能包强制要求、推荐目录结构）。本节可信度升级为"双源一致"；关键时间节点仍以官网为准。

- **分组**：初级组（大一至大三）可用 7 Series / Zynq-7000 / UltraScale(+)；高级组（大四/硕士）不设器件限制。按队内最高学历归组。
- **考察侧重**：作品完整性与工程水平（功能正确、实测验证、数据真实、可复现），**创新性与应用价值占最高权重**。
- **实现方式**：RTL、Vitis HLS、AI Engine、PS 软件任意组合；核心价值可体现在硬件加速、系统集成、接口设计或应用创新。
- **初级组推荐 PYNQ**：PS 侧 Python/Jupyter 组织数据流，PL 侧 HLS/RTL 封装 Overlay；**通用的 PYNQ Skill 单独加分**（换题换板仍可用，如 Overlay 加载校验、DMA 搬运封装、接口契约生成脚本、指标采集报告工具）。
- **工具版本**：Vivado/Vitis **2026.1（推荐）或 2025.2**；允许使用任意公开大模型并须提交协作记录（提示词、回答、自我纠错轨迹）。
- **开源要求**：强烈要求 GitHub/Gitee 开源，推荐 MIT 或 Apache-2.0。
- **提交物**：工程包 + 技能包（`skill/`）+ 设计报告；推荐目录结构与本项目 README 已对齐（目录对照说明也已具备）。
- **评分权重**：创新性与应用价值 30 / 性能与资源优化效果 20 / 功能正确性与设计完整性 20 / 大模型协作与技能包 15 / 文档质量与可复现性 15。

---

## 7. 对 EdgeSight 的启示

1. **权重导向**：30 分创新性靠"自研 RISC-V 三级流水 + 视觉 SoC"的芯片设计含量；15 分大模型协作与技能包、15 分文档与可复现——我们现有的 `llm_log`（含真实纠错轨迹）、`skill/`、目录对照说明正是对着这 30 分建设的，继续保持。
2. **实测与基线**：所有国奖作品都给出延迟/资源对比表。我们的"先测基线再谈优化"铁律与 `data/metrics.csv` 骨架正确（原顶层 `metrics/` 已并入 `data/`，对齐指南 §3.3.5.4）；M3 实测时务必留原始日志。
3. **技术栈参考**：往届高分作品大量使用 HLS DATAFLOW + AXI DMA + PYNQ 可视化；我们的 CNN 协处理器的 DMA 搬运与 PS 侧采集脚本可借鉴其架构，但核心创新保留在自研核。
4. **风险提示**：自主选题赛道公开参考少、竞争看"完整作品 + 实测数据"；器件限制在 7 Series/Zynq-7000 内（PYNQ-Z2 合规）。
5. **工具版本**：官方推荐 2026.1，也允许 2025.2（2026-09-14 团队决议采用 **2026.1 BASIC 免费档**：实测限制为 XSim ≤ 50K 实例、仅 Windows，对本项目核级 tb 无阻塞；2025.2 留作回退，见 issue #2），需在报告中说明版本与可复现脚本。

---

## 附录：检索方法与数据边界

- GitHub API 关键词：`嵌入式芯片与系统设计竞赛`、`hlstrack2025`、`fpgachina2024/2025`、`AMD自主选题`、`PYNQ 竞赛` 等；命中 19 + 57 + 44 等仓库，本文件收录与 AMD/图像/RTL 相关的代表作品。
- 搜索引擎（Bing/搜狗/DDG）当日对中文竞赛关键词返回无关或反爬验证页，故以 GitHub API 为准；官方名单未取得。
- 奖项字段为作者自述，可能存在组别/年份偏差；使用前建议核对官方公告或联系作者。
- 2026 赛制要点来自第三方转录（Qian-Sai），关键节点请以 <http://www.fpgachina.cn/> 官方发布为准。
