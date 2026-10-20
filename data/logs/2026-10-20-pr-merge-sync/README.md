# PR #86 合并前验证与三人分支同步

- 日期：2026-10-20；执行者：Codex，用户授权检查差异、合并 PR、同步分支与清理旧分支。
- 初始版本：`dev/riscv@04024d1`，主干 `411d9ee`；本地与同名远端无提交差异，riscv 领先主干 25 个提交。
- 目标：保留 `main`、JL 的 `dev/riscv`、NC 的 `dev/vision`、WC 的 `dev/exe`；仅在独有提交已合入且分支头未变化时删除 `dev/model`、`chore/repo-cleanup`。
- 本轮新增内容：卫生修复记录、日志索引、四分支协作说明；群内作战单精确忽略，不提交文件及其索引入口。
- 原始 Vivado 报告保留工具排版，按已有原始报告规则配置空白检查例外；补正文档中的 CRC 后资源数据与返回 CDC 未收口边界，不修改报告数值或 RTL。

## 验证命令与产物

从仓库根目录、MSYS2 UCRT64 工具链环境执行：

```bash
COPROCESSOR_PYTHON=python VISION_PYTHON=python RISCV_CROSS=riscv32-unknown-elf- bash sim/scripts/run_iverilog.sh all
python sim/scripts/index_runs.py --check
python sim/scripts/check_repo_hygiene.py
git diff --check
```

- `core-all.log`、`core-all.exit_code`：全量回归原始输出和真实退出码；本次单次全量已完成，退出码 0。
- `environment.json`：Python 3.12.10、Git 2.55.0.windows.2、Icarus 13.0、RISC-V GCC 14.2.0 的实际版本输出。
- `regression-summary.json`：被测源码提交、PASS/失败行统计、四档完整 CoreMark 结果与日志 SHA256；四档退休指令数均为 10,106,386，CRC/最终结果检查通过。
- `test_vision_gate.sh` 的 8 项自测包含故意注入的 FAIL/FATAL/ERROR；只按该明确自测区段及逐项 CASE 期望分类，9 行预期错误均被正确拒绝，其余区段无未预期失败，不删除原始输出。
- `branch-audit-before.json`：操作前本地/远端分支指纹与主干差异。
- `branch-retire.txt`：两个旧分支无独有提交、按精确旧头删除远端并安全删除本地的结果；已完成，原提交仍由主干保留。
- 结果：全量回归 PASS，包含核基础、协处理器 RTL/Python、四档短基准/完整 CoreMark、流控/冒险与视觉 RTL/Python。卫生/索引/差异检查原始结果另见 `quality-checks.txt`。
- 合并入口为 PR #86；合并和同步后使用 `gh pr view 86`、`git fetch --prune origin`、`git branch -avv` 核对实际结果，不在自身提交内硬编码未来合并 SHA；不修改保护规则。

## 边界 / 未完成

本记录不代表实体存储、完整 SoC 协处理器仿真或上板验收完成；不重跑 Vivado、不生成位流。新提交只有文档、配置与数据记录，按理解门槛技能的对应豁免处理；不替已有 PR 代码代签人工理解或审查。
