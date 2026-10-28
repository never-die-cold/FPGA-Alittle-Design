# 技术文档（初版）

本目录存放技术文档初版及其可复现生成脚本。状态口径：**2026-10-27**。
当前稿：18 页、7 幅图、10 张表、15 篇参考文献。

## 文件

| 文件 | 说明 |
|:---|:---|
| `EdgeSight-技术文档-初版.docx` | 交付稿（V0.9，2026-10-27 口径） |
| `EdgeSight-技术文档-初版.pdf` | 同一稿的 PDF 预览（LibreOffice 转换） |
| `build_tech_report.py` | DOCX 生成脚本（正文、表格、图注、页眉页脚） |
| `make_tech_report_figures.py` | 配图生成脚本（系统/视觉/协处理器/核/软件） |
| `figures/` | 生成后的 PNG；`fig_exe.png` 为 2026-10-21 模拟后端界面截图 |

## 重新生成

```bat
py docs\tech-report\make_tech_report_figures.py
py docs\tech-report\build_tech_report.py
"C:\Program Files\LibreOffice\program\soffice.exe" --headless --convert-to pdf --outdir docs\tech-report docs\tech-report\EdgeSight-技术文档-初版.docx
```

不要直接改 DOCX：改 `build_tech_report.py` 后重新生成，保证内容与图表可复现。

## 结构

按竞赛参考模板的五部分组织：

1. 作品概述：功能与特性、应用领域、主要技术特点、主要性能指标、主要创新点、设计流程；
2. 系统组成及功能说明：整体、硬件、软件，另加 2.4 软硬件责任边界；
3. 完成情况及性能参数：完成度矩阵、工程成果、特性成果、结果讨论与验收边界；
4. 总结：可扩展之处、心得体会；
5. 参考文献（15 篇）。

字数上限已核对：摘要 401 字（限 800）、1.1 约 200 字（限 400）、1.2 约 161 字（限 400）、1.3 约 199 字（限 400）、1.5 约 141 字（限 200）、1.6 约 114 字（限 200）、4.1 约 108 字（限 300）、4.2 约 540 字（限 1000）。

## 事实口径

- 核：v1 三级 + 三路转发 + Radix-4 + 可切换 BHT；CoreMark 2K/32 四档 CPI 1.886→1.606；44/44 arch-test 签名；OOC 86.806 MHz。
- 视觉：22 个仓库内 tb；720p60；video_pipeline OOC WNS +0.330 ns；物理 HDMI 板级直通 108 帧。
- 协处理器：128 MAC INT8；36,032 B PROVISIONAL 清单；6/6 离板门禁；40 MHz 全系统门禁 WNS +2.498 ns。
- 板上（2026-10-26/27）：zero/pattern 各 3 轮全匹配；zero/pattern/roi_001/frame 四例黄金全匹配；10,000 次寄存器读取无错误；共存位流 `b2690b0a` 同时输出 HDMI、抓取 BGR 原帧并运行硬件 CNN；检查记录链路经真实 UVC/HTTP 联调验证（工单 2/4/4，RECHECK）。
- 多目标：旧包结果槽错位（第 0 槽空、后续槽错位）；`COMMIT_RESULT` 修复的三目标用例仿真 PASS，但新包构建失败、未上板；不得把多目标写成板上通过。
- 软件：Icarus 172 PASS；Python 17+20 组；服务+前端模拟轮次 CHECK_PASS 1/1/1；4 轮服务异常 + 9 个引擎场景；真机手动按钮与 CSV 未完成。
- 严格区分「离板仿真 / 软件联调 / 单目标板上推理 / 整机验收」；PROVISIONAL 黄金对拍不等于识别精度，也不等于整机验收。

## 待补

- 实物图已补：`figures/photo_plate.jpg`（左为整体布置，右为 PYNQ-Z2 板卡与接线）。前端实机运行照片暂缺，当前保留模拟后端截图并标注 PROTOTYPE。
- 正式 PTQ/QAT 模型与真实数据精度报告未完成；四例黄金只证明整数链与硬件输出一致，不证明识别精度。
- 多目标修复包需重新构建并上板；连续作业、长时/温度稳定性、SD/mmc 历史故障复现未完成。
- 真机手动按钮核验与 CSV 导出中断未完成。
- 参赛队伍名称/学校信息按模板要求未写入。

## 证据入口

- 核：`data/logs/2026-10-05-partB-*`、`2026-10-06-partC-*`、`2026-10-07-partC-postopt/`
- 视觉：`data/logs/2026-10-02-vision-offboard/`、`2026-10-03-vision-onboard/`
- 协处理器：`data/logs/2026-10-25-dma16-merge-gates/`、`2026-10-26-board/`、`2026-10-26-board-gate566b/`
- 共存与软件：`data/logs/2026-10-27-startup-clock-repair/`、`2026-10-27-product-coexist/`
- 交接说明：`docs/runbooks/pynq-coexist-handoff-2026-10-27.md`
