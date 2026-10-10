# 数据审计与远端协议整合复验

复验代码版本：`bfddb1b`，包含本轮数据审计三批提交和远端 `dev/exe @ 7101a33`。
未修改远端作者的协议实现；通过 merge 保留其原始提交和双方历史。

| 仓库入口 | 原始结果 | 结论 |
| --- | --- | --- |
| `bash sim/scripts/run_vision_python.sh` | `vision.log`、`vision.exit.txt` | 八组通过，退出0；含 LIVE v1.2 校验正负例 |
| `bash sim/scripts/run_inspection_python.sh` | `inspection.log`、`inspection.exit.txt` | 十三组通过，退出0 |
| `git diff b51d46b..HEAD --check` | `diff-check.log`、`diff-check.exit.txt` | 退出0 |

测试均由仓库脚本执行，临时输出均在仓库 sim/build 内。
vision 日志中的 timeout/re-handshake WARN 是断联与恢复测试激励，最终由回归门检查通过。
没有 RTL 改动，因此不将 Python 回归作为核或硬件验证。

## 实现边界与待办

- 数据审计已用合成图和虚构标签验证；真实来源、标签、类别覆盖和分类精度尚未验收。
- LIVE v1.2 的报文字段校验已由远端提交实现并在本次复验通过。
- 网络预览 `endpoint_state` 仍按 remote.mode 显示 LIVE/MOCK；没有消费 packet.prototype。
  **网络 PROTOTYPE 标识尚未实现**，不能把决策单中的界面要求当作已接入。
- 真实 LIVE 服务、工单判定展示、板端闭环、正式 INT8 和 CNN RTL 仍未完成。
- 相似帧检测、GT CSV 对照、朝向统计、未知/遮挡扩展和来源认证未实现。

用户第39–50题及补测51通过，完整记录见
[理解记录](../../../report/llm_log/2026-10-10-dataset-audit.md)。
