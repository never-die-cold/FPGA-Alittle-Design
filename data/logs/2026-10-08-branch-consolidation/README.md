# bench 合入与分支整理复验

基线 main `f7102d2`，bench `9ee0214`。在仓库根目录执行：

- `python sim/vision/test_localization_data.py`：5 项 PASS，退出 0。
- `python sim/vision/test_class_aware_metrics.py`：3 tests OK，退出 0。
- MSYS2 `/usr/bin/bash -n sim/scripts/pi_password_reset_once.sh`：退出 0；不执行密码重置。
- 对 main...bench 的 17 个 Python 文件使用 Python 3.12.10 `ast.parse`：全部通过。
- `git diff --check origin/main...HEAD`：保留三组原始串口 txt/log 的定向例外，文档尾随空格清理后通过。

日志与退出码在本目录。此前未设置 MSYS PATH 的尝试误调用系统 WSL Bash，退出 1；指定 `/usr/bin/bash` 后语法检查通过。

此次不修改 RTL，核/tb 与 main 相同，沿用模块一收口证据。视觉实验合成集及局部测试不替代真实工位、PYNQ/CNN 部署或整机验收，完整训练未重跑。
