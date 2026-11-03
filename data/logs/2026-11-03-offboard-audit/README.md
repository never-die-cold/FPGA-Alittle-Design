# 最终离板仓库审查

- 日期：2026-11-03（Asia/Shanghai）。
- 基线：dev/submission-slim，ffe0769，加开工时已有未提交改动；详见 baseline-status.log。
- 范围：跟踪代码/文档、未跟踪的网页与 LaTeX 稿；不接板、不修改业务代码。
- 命令和原始结果：本目录各 .log；最终命令/退出码与发现写入 AUDIT.md。
- 产物：审查报告、原始检查日志、覆盖说明。
- 边界：离板检查不代替新综合实现、实板稳定性、识别精度或工业整机验收。
- 状态：本轮审查结束。完整问题、命令、原始结果与边界见 [AUDIT.md](AUDIT.md)。20项问题（5 P1 / 15 P2），另有7项P3维护事项；业务代码未修复。
- 结果：四档CoreMark、44次arch签名、视觉25 tb、视觉Python19组、检查链17组、CNN门禁/整数参考及补充专项完成。N03生命周期夹具缺失导致失败；卫生/索引检查失败。原始all进程为避免重复BHT长测被主动结束，覆盖集合按报告中的分段入口补齐，不声称该all命令完整PASS。
- 输入锚定：`baseline-status.log`、`working-tree.diff`、`sources.sha256`；源文件哈希复核退出0。主要结构化结果为 `static-final.json`、`test-inventory.json`、`coremark-results.json`、`budget-duplicates.json`。
- 可复现缺陷探针：`node --test data/logs/2026-11-03-offboard-audit/probe-web.mjs`；`python data/logs/2026-11-03-offboard-audit/probe-codec.py`。探针PASS表示缺陷被观察到，不表示已修复。
