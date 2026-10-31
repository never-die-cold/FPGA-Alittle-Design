# 技术文档（修订版 V1.0）

> 修订版（2026-10-31）：按 owner 评审意见（9 条，原文见
> [revision-feedback-2026-10-31.txt](revision-feedback-2026-10-31.txt)）完成修订；状态口径 **2026-10-30**。
> 上一版（2026-10-27 初版 V0.9）保留在 git 历史（tag/commit 可回溯）。

本目录存放技术文档及其可复现生成脚本。
当前稿：9 幅图、13 张表、16 篇参考文献；摘要 268 字。

## 文件

| 文件 | 说明 |
|:---|:---|
| `EdgeSight-技术文档-初版.docx` | 交付稿（修订版 V1.0，2026-10-30 口径） |
| `EdgeSight-技术文档-初版.pdf` | 同一稿的 PDF 预览（LibreOffice 转换） |
| `build_tech_report.py` | DOCX 生成脚本（正文、表格、图注、页眉页脚、公式字符排版） |
| `make_tech_report_figures.py` | 配图生成脚本（系统/视觉/协处理器/核/软件示意图） |
| `_import_photos.py` | 实拍插图入库脚本（改名 + 最长边 1600 缩放 + 压缩，来源见下表） |
| `revision-feedback-2026-10-31.txt` | 本次修订的评审意见原文（owner 提供） |
| `figures/` | 生成图与照片 |

## 重新生成

```bat
py docs\tech-report\make_tech_report_figures.py
py docs\tech-report\_import_photos.py
py docs\tech-report\build_tech_report.py
"C:\Program Files\LibreOffice\program\soffice.exe" --headless --convert-to pdf --outdir docs\tech-report docs\tech-report\EdgeSight-技术文档-初版.docx
```

不要直接改 DOCX：改 `build_tech_report.py` 后重新生成，保证内容与图表可复现。

## 修订记录（2026-10-31，对照 9 条意见）

1. 摘要精简：401 → 268 字，只留需求、方案、硬数字与边界声明。
2. 全文删重复：2.1 与第三部分的进展表述去重、3.3 讨论段合并；表号修复（原表 2-5 跳号为 2-4）。
3. 删除「比赛有截止时间」等收尾阶段表述；叙述性「截至…」改为现状陈述（证据日期仅保留在表格）。
4. EXE 表述全部改为 HTML 网页端；图 3-2/3-3 以真实前端截图替换原模拟界面示意图（fig_exe.png 退役）。
5. 公式字符规范排版：变量斜体 + 真·上下标（如 S_in=1/127、score_q15、margin_q），等效 LaTeX 渲染效果。
6. 表 3-2 由「四档对比」改为「特性消融」（v0 为追溯基线），新增 IPC 列与传统公开口径段落（IPC 0.623、
   CoreMark/MHz 1.974），并注明与第三方软核的同条件对照列为后续工作——不引用未经本仓库复现的外部数字。
7. 表 3-5 删除「包/bit」列；复现入口由行内命令改为表 3-6（等宽字体），路径按瘦身后的仓库核准
   （export_records.py 已迁至 src/pynq_host/）。
8. 心得体会按 owner 草稿口吻重写（「我们」视角、按人梳理 JL/NC/WC 的经历、只保留
   三级流水 WNS 失败一例、避免 AI 腔句式），约 800 字。
9. 新增 4.3 节「大语言模型协作记录与 Skills 沉淀」（llm_log 220 条 + 9 个技能包清单）。
10. 3.3 增补公开口径横向对比（表 3-3）：Ibex 官方三档 CoreMark/MHz（0.904/2.47/3.13，新增文献 [16]）、
    PicoRV32 官方 Dhrystone 0.516 DMIPS/MHz（CPI 4.100，[11]）；「业界标准指标」表述改为引证
    EEMBC [3] 与体系结构教材 [15]；表 3-3 之后表格顺延为 3-4…3-7。

## 插图来源（repo-hygiene 规则 6：用途 / sha256 / 来源与重建）

| 文件 | 用途 | sha256（前 16 位） |
|:---|:---|:---|
| `figures/photo_workstation.jpg` | 图 3-1 整机工位 | `3EC77E0DAFEA2CB4` |
| `figures/photo_board_pi.jpg` | 图 2-2 板卡与树莓派相机 | `A3F613FC00B7C4E7` |
| `figures/photo_board_closeup.jpg` | 图 3-2 板卡特写 | `9EC96A7024CF8FD4` |
| `figures/webui_live.png` | 图 3-3 网页端 LIVE 界面 | `3B69E948E472940B` |
| `figures/header_banner.png` | 每页页眉竞赛横幅（芯辰大海 FPGA · 点亮未来） | `787DB8FA20DE80A8` |

来源：owner 2026-10-31 拍摄（前三张）与 2026-10-30 23:56 前端联调截图（webui_live），
原图存 `D:\Desktop\contests\2026fpga\技术文档插图\`（仓外）；入库件由 `_import_photos.py` 生成
（最长边缩至 1600，JPEG q88 / PNG optimize），可用该脚本从原图一键重建。fig_* 示意图由
`make_tech_report_figures.py` 生成；`fig_exe.png`、`photo_plate.jpg` 已不被文档引用，保留作历史素材。
页眉横幅 `header_banner.png` 提取自官方参考模板《技术文档参考.docx》（owner 提供），
显示尺寸 6.52 cm × 1.19 cm 居中，每页生效。

## 结构

按竞赛参考模板五部分组织：

1. 作品概述：功能与特性、应用领域、主要技术特点、主要性能指标、主要创新点、设计流程；
2. 系统组成及功能说明：整体、硬件（含树莓派视频源实物）、软件，另加 2.4 软硬件责任边界；
3. 完成情况及性能参数：完成度矩阵、工程成果（图 3-1/3-2/3-3）、特性消融与时序资源、板上时间线、复现入口；
4. 总结：可扩展之处、心得体会、4.3 大语言模型协作记录与 Skills 沉淀；
5. 参考文献（15 篇）。

字数核算（build 输出）：摘要 268（限 800）、1.1 约 203（限 400）、1.2 约 161（限 400）、1.3 约 202（限 400）、
1.5 约 141（限 200）、1.6 约 114（限 200）、4.1 约 108（限 300）、4.2 约 463（限 1000）、4.3 约 334。

## 事实口径

- 核：v1 三级 + 三路转发 + Radix-4 + 可切换 BHT；CoreMark 2K/32 四档消融 CPI 1.886→1.606（IPC 0.623、
  CoreMark/MHz 1.974）；44/44 arch-test 签名；OOC 86.806 MHz。公开口径对比：Ibex 官方 0.904/2.47/3.13
  CoreMark/MHz [16]；PicoRV32 官方 Dhrystone 0.516 DMIPS/MHz、CPI 4.100 [11]——编译器与运行条件有差异，作量级参照。
- 视觉：22 个仓库内 tb；720p60；video_pipeline OOC WNS +0.330 ns；物理 HDMI 板级直通 108 帧。
- 协处理器：128 MAC INT8；36,032 B PROVISIONAL 清单；6/6 离板门禁；40 MHz 全系统门禁 WNS +2.498 ns。
- 板上（2026-10-26/27）：zero/pattern 各 3 轮全匹配；四例黄金全匹配；10,000 次寄存器读取无错误；共存位流
  `b2690b0a` 同时输出 HDMI、抓取 BGR 原帧并运行硬件 CNN。
- 前端（2026-10-30）：网页端 LIVE 形态接入 USB 采集卡回传与板端服务，完成手动轮次触发、页面批次记录与
  CSV 导出联调（工单 3/3/3，判定 RECHECK，原因 low_score）；低置信目标不进入通过结论，**不作为识别精度或整机验收证据**。
- 多目标：旧包结果槽错位；`COMMIT_RESULT` 修复的三目标用例仿真 PASS，新包未上板；不得把多目标写成板上通过。
- 软件：Icarus 172 PASS；Python 17+20 组；服务+前端模拟轮次 CHECK_PASS 1/1/1；4 轮服务异常 + 9 个引擎场景。
- 严格区分「离板仿真 / 软件联调 / 单目标板上推理 / 整机验收」；PROVISIONAL 黄金对拍不等于识别精度，也不等于整机验收。

## 待补

- 正式 PTQ/QAT 模型与真实数据精度报告未完成；四例黄金只证明整数链与硬件输出一致，不证明识别精度。
- 多目标修复包需重新构建并上板；连续作业、长时/温度稳定性、SD/mmc 历史故障复现未完成。
- 与第三方软核（如 PicoRV32）的同板卡、同工具链性能对照未做。
- 参赛队伍名称/学校信息按模板要求未写入。

## 证据入口

- 核：`data/logs/2026-10-05-partB-*`、`2026-10-06-partC-*`、`2026-10-07-partC-postopt/`
- 视觉：`data/logs/2026-10-02-vision-offboard/`、`2026-10-03-vision-onboard/`
- 协处理器：`data/logs/2026-10-25-dma16-merge-gates/`、`2026-10-26-board/`、`2026-10-26-board-gate566b/`
- 共存与软件：`data/logs/2026-10-27-startup-clock-repair/`、`2026-10-27-product-coexist/`
- 前端联调（2026-10-30）：截图见 `figures/webui_live.png`，来源与运行形态见上文插图来源表
- 交接说明：`docs/runbooks/pynq-coexist-handoff-2026-10-27.md`
