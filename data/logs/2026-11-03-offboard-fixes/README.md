# 离板审查问题修复

- 日期：2026-11-03（Asia/Shanghai）。
- 基线：`dev/submission-slim @ ffe0769`，加已有网页端改动及审查记录。
- 授权：用户要求修复并推送，选择快速模式；最初保留理解门槛，随后明确说“不做理解门槛了”，本轮按用户最新指令豁免，不记作答题通过。
- 材料状态：用户确认最终技术文档和海报已由队友在另一台本地电脑完成；本仓库旧稿不代表最终成品，本轮不代改队友成品。
- 验证：各 `.log` 保存实际命令结果；处理进度见 `RESOLUTION.md`。
- 边界：本轮离板修复不宣称实板稳定性、正式精度或整机验收完成；本目录记录提交前验证快照，实际提交/推送结果以Git和会话回执为准。

## 复现与实际结果

从仓库根目录执行，环境与硬件边界见`docs/runbooks/final-offboard-check.md`：

```bash
bash sim/scripts/run_offboard.sh software
git diff --cached --check
python sim/scripts/index_runs.py --check
python sim/scripts/check_repo_hygiene.py
```

- `software-final.log`：完整软件汇总退出0，末尾`PASS: offboard software`。视觉Python、INT8参考、检查链、额外数据/N03/网页HTTP/保护/工具检查全部完成；Node 18项通过。卫生0错误，10组历史重复blob告警保留。
- `software-regression.log`：第一次功能检查通过、最后因运行日志改变data目录大小导致索引过期，整体退出1；此失败尝试保留，不覆盖为成功。最终运行先输出到`sim/build/`再复制本目录，归档后另重建索引/复核卫生。
- `syntax.log`：本轮9个关键Python入口AST解析通过；`bash -n sim/scripts/run_offboard.sh`退出0。
- `codec.log`保留第一次新测试加载器漏模块常量的NameError，已修正；教程有符号边界/失败退出码的最终PASS见`software-final.log`。`node.log`为早期16项网页测试记录，最终增至18项。
- `service.log`、`n03.log`为定向复验；`diff-check.log`为空，暂存差异检查退出0。最终冻结检查与输入哈希见`verification.json`、`sources.sha256`。
- `source-check-before.log`保留哈希清单CRLF导致Git Bash把回车读入文件名的首次失败；清单已改LF，`sha256sum -c data/logs/2026-11-03-offboard-fixes/sources.sha256`对26个输入全部通过，退出0，见`source-check-final.log`。业务代码未因此改变。

## 发布边界

必需网页模块、服务转发、测试、10/30实板证据、原N03夹具及本次审查/修复记录纳入本次发布提交。本地未跟踪`docs/tech-report/latex/`保持原样并排除，不代替队友最终材料。

代码讲解、原三道理解题与用户豁免原话见`report/llm_log/2026-11-03-offboard-fixes.md`；不伪造用户答案，不将豁免写成答题通过。原审查RTL/CoreMark分项证据沿用，本轮没有改RTL，新增`run_offboard.sh all`尚未整条执行；不作新实板/综合/精度结论。
