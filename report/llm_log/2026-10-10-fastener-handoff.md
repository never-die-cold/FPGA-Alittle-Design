# 外包视觉方案接收与文档同步

用户要求：将 2026-10-07 紧固件视觉交接包并入项目目录，尽量不修改原文，可据此更新现有项目文档。
执行基线：`dev/exe @ 051aefa`。开工已读 workflow、主计划、核计划与 v0/v1 契约；已有未跟踪的 `docs/inspection-v0-contract.md` 保留原样。

完整交接包从根目录移至 `docs/outsource/紧固件视觉方案交接包-2026-10-07/`，原始 48 文件均保持 SHA256。28 个与现有文件逐字节一致，17 个仅换行/末尾空白差异，3 个为包入口及报告版本差异；16 个 JSON 解析后内容一致。没有覆盖现有算法、模型或实验结果。

更新 `plan.md`、`docs/README.md`、训练说明、项目进展汇报及受控流水线方案；新增交接索引和接收清单。根目录主计划跨目录改动已在执行前说明。采用受控工位、OpenCV 定位与小 CNN 主线，PTQ 先评估、必要时 QAT，明确原分辨率 ROI 和板端部署仍待实现/评审。

验证入口：`docs/outsource/fastener-handoff.md` 中的仓库内 PowerShell 完整性命令；原始输出 `Archive integrity PASS: 48/48 files`。本次仅文件/文档接收，没有复跑完整算法、训练或 RTL，也未宣称新增板端验收。

文档相对链接逐项检查结果：`Document links PASS: 45 local links`；`git diff --check` 退出 0，无输出。未跟踪的新索引和日志也单独检查，无行末空白。

纯文档与记录改动，按古法编程技能的纯文档豁免处理；未执行 commit。未实现/未接入项：正式板端定位、ROI 通路、INT8 模型、CNN 协处理器、完整工单闭环及连续运动去重。

## 按用户纠正拆分材料

用户明确要求文档、模型等分开放置。已移除混装整包目录：7 份外包原始 Markdown 放 `docs/outsource/fastener-vision-2026-10-07/`，16 脚本并入 `sim/vision/`，3 模型并入 `models/`，22 结果并入 `results/`。已有同内容文件合并去重；仅格式差异的模型/JSON采用交付字节，项目维护版文档独立保留。

逐文件去向写入 `data/evidence/2026-10-10-fastener-handoff/installed.csv`，同时保存原字节 SHA256 与文本规范化哈希以兼容 Git 换行规则。原字节核对输出：`Installed integrity PASS: 48/48 files`；移除整包前已核对全部目标文件，输出 `Package deduplication PASS`。上文“整包归档”仅记载此前步骤，最终目录以本节为准。

外包原文保留其历史路径，不改写；链接检查以项目维护文档及新索引为范围。未改算法、未进行模型/板端验收，未 commit。

最终复核：执行交接索引中保存的完整性命令，输出 `Installed integrity PASS: 48/48 files`；项目文档输出 `Document links PASS: 52 local links`；`git diff --check` 退出 0，无输出。外包文档目录只含 7 个 `.md` 文件，混装整包目录不存在。
