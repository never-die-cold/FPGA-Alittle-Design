# 2026-10-03 ROSS 赛事通知与项目关联研究

## 用户请求

研究赛事群消息所关联的网站，说明与当前项目各部分的关系，报告放在 docs/。
用户随后说明 DOCX 是笔误，要求改为 Markdown 并提交。

## 基线与范围

- 分支 `codex/vision-offboard`，HEAD `a2c29d8`。
- 开工读取 workflow、计划与相关契约；保留原有两个未跟踪上板脚本。
- 初次生成 Word 报告；按用户更正，最终交付 `docs/amd-ross-project-relevance-report.md`。
- 格式转换时分支仍为 `codex/vision-offboard`，HEAD 已到 `e1f3ac7`。
- 报告保留研究基线 `a2c29d8`，明确状态不代表后续最新进度；不改 RTL。
- 纯文档交付，理解门槛技能明确豁免文档类提交；用户已授权提交。

## 研究结果

ROSS 关联核/视觉验证、Skill 与报告；云算力关联模型训练。
本地智能体参考仓库属于独立参赛交付，本项目 README 明确为自主选题初级组。
官网产品页、仓库 FAQ、安装指南的版本表述不同，报告区分宣传兼容与实测基线。
官方指南以 2026.1 为测试基线；单项仿真 Skill 有 2025.2/2026.1 验证记录。
本地检索库不自动意味着回答模型和整个工作流断网运行。
HLS 与 NPU 工具不能直接替代 PYNQ-Z2 上自研 INT8 协处理器。

赛事总仓库与 RTL 页访问失败；未据此断言新规则或评分。
报告中的培训时间、QQ群和体验申请入口来自用户提供的群消息。
正式约束仍待赛方公告复核；已读 HLS 规则不作为自主选题约束。

## 验证与修正

标准 render_docx.py 报 `LibreOffice soffice.exe was not found on PATH`。
申请授权后用后台 WPS 导出 PDF，使用运行时 Poppler 渲染。
初版发现孤页、空白页和默认 Title 蓝线，修正样式与分页后复渲染。
最终 9 页逐页 PNG 全部检查；结构检查 17 编号来源、21 外链、4 表 PASS。
这些检查属于初版 Word 排版过程。格式更正后清理本次生成的 DOCX、
正文 JSON、Word 生成脚本以及 PDF/PNG 排版证据，避免留下重复交付。

## Markdown 转换与最终检查

- 保留全部 37 段正文和 4 张表的所有行，编号引用转为可点击的来源链接。
- 结构核对原始输出：

```text
PASS: all 37 paragraphs and all table rows retained; 17 sources; 21 unique URLs; 4 tables.
Markdown lines: 205
```

- 验证方式：从正文 JSON 转换后逐段、逐表行比对，统计来源及外链；
  再检查暂存内容的 `git diff --cached --check`。本次无需 FPGA 回归。
- 最终提交仅包含 Markdown 报告和本研究日志。
- 最终结构检查原始输出：`PASS: Markdown sources, URLs, table columns, whitespace and obsolete artifact cleanup.`
- `git diff --cached --check` 无输出，退出码 0；暂存区仅上述两个 Markdown 文件。

## 未实现和未验证

没有安装或接入 ROSS，没有实际官方 MCP 调用案例，没有申请云资源或运行云训练。
未重新验证 FPGA 功能；核集成、正式模型、协处理器及工业闭环仍按原计划待完成。
报告中的采用顺序与效率记录方案为建议，不宣称已有提效数据。
