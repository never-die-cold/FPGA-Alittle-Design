# 2026-10-27 提交前定向检查

- 日期：2026-10-27，Asia/Shanghai；基线 dev/riscv / bc37c08 加工作区改动。
- 用户指令：分多个 commit、push、开 PR 合并后同步分支；沿用快速模式、理解题留后。
- RTL：run_iverilog.sh cop_axi_cdc_skew / cop_multitarget_commit；run_coprocessor_iverilog.sh axi_lite_cdc / task_ctrl / firmware_e2e，均退出 0，原始输出为同目录 txt。
- Python：test_cop_driver、test_cop_engine、test_vision_live_service、test_cop_service、test_localize、test_cop_payload_loader，均退出 0。
- 新 Python 脚本 AST 检查通过；这不代替板端验收。git diff --check 在提交前执行。
- 产物：本目录测试文本；没有重新运行全量 all 回归，没有新增烧写/训练/界面操作。
- 限制：多目标修复尚未上板；识别质量、手动按钮与 CSV 导出仍未完成。详见[交接](../../../docs/runbooks/pynq-coexist-handoff-2026-10-27.md)。
- 仓库卫生检查仍未通过：根目录已有 Vivado/缓存生成物及历史报告错误链接；未删除这些既有文件。索引随后重新生成并检查，原始卫生输出保存在 repo-hygiene.json。
