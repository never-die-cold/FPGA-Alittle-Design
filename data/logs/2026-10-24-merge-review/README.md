# PR #87 合并候选复核与 NC 取证归档

- 日期：2026-10-24；执行者：Codex；本轮未连接板卡、相机或 SSH。
- 版本：初始 `dev/riscv@5f8abe2`；候选 `dev/exe@41ff8936f54da0f5aabef2bd1f532edda841e342`，包含 JL `94af6f6`；本地另有 NC 相机工具与取证记录。
- 命令：下方仓库内入口；测试输出保留在本目录与 `sim/build/2026-10-24-merge-review/`。
- 结果：完整 `bash sim/scripts/run_iverilog.sh all` 第二次运行 exit 0；检查链 19 组、视觉 Python 21 组、独立协处理器 all 均 exit 0；SSH 2 项测试及 Python/Shell 语法检查通过。
- 产物：本次原始回归日志、退出码、`source-inputs.json` 源码字节指纹及三组 NC 取证的压缩包/逐文件哈希清单。
- 边界：本轮未复验硬件；相机出图、40 MHz 板级推理、PS payload/ROI loader、正式模型均未完成。

## 复跑入口

在仓库根目录、已有 Python/NumPy/OpenCV/Paramiko、MSYS2 与 RISC-V 工具链的环境中：

```bash
python sim/scripts/test_nc_ssh_session.py
bash -n sim/scripts/pi_camera_matrix.sh
bash -n sim/scripts/pi_camera_native.sh
bash -n sim/scripts/pi_camera_rebind.sh
bash -n sim/scripts/pi_camera_recovery.sh
bash -n sim/scripts/run_pynq_watch.sh
bash sim/scripts/run_inspection_python.sh
bash sim/scripts/run_vision_python.sh
bash sim/scripts/run_iverilog.sh all
python sim/scripts/index_runs.py --check
python sim/scripts/check_repo_hygiene.py
git diff --check
```

本机 PATH 原无 Python，使用已安装的 Python312；`VISION_PYTHON` / `COPROCESSOR_PYTHON` 显式指定解释器。首轮 `all` 在进入协处理器阶段因 `python: command not found` 退出 1，保留失败原文，不计 PASS。测试可能按本机 GCC 重建 `cop_job.hex/dis`，该工具链漂移须排除在提交外。

本机第二次完整回归在 MSYS2 Bash 中实际使用：

```bash
export PATH=/usr/bin:/ucrt64/bin:$PATH
export VISION_PYTHON=/c/Users/ASUS/AppData/Local/Programs/Python/Python312/python.exe
export COPROCESSOR_PYTHON="$VISION_PYTHON"
bash sim/scripts/run_iverilog.sh all
```

判据沿用冻结契约：CoreMark 的 `errors_raw=1` 含仿真运行时间不足 10 秒的框架报错，只作证据，见 `docs/contracts/coremark.md` §5.4；实际核验退出码、迭代数、CRC 和最终结果。视觉门禁自测的 8 项故障注入含预期 FAIL/FATAL/ERROR，须按 `CASE` 期望分类，原始文本保留。

`source-inputs.json` 同时记录 405 个文件的工作区 SHA256、Git 暂存 blob 与其 SHA256。唯一工作区/暂存字节差异为既有 `sim/vision/test_c01_ddr_onboard.py` 的 CRLF/LF，统一换行后完全相同；本次未修改该文件。原始日志由既有 `data/logs/** -text` 属性保留字节。

## NC 取证与预算

三个现场目录的原始文件共 348 个：`nc-board` 251、`nc-camera-recheck` 15、`nc-camera-recovery` 82。逐文件与归档解压流比对一致，SHA256/路径/字节见各目录 `ARCHIVE-MANIFEST.json`；恢复命令见各 README。原文件另存仓库忽略目录 `sim/build/2026-10-24-merge-review/original-evidence/`，未删除。

为减少文件数与重复 PNG 开销，板端证据使用 xz；另两组使用 gzip。新增原始取证由 348 个散文件缩为 3 个压缩包；每包均小于 5 MiB。历史失败、未确认远端完成、诊断图案与真实相机图像的区别均保留。

合并候选原有 5,571 个跟踪文件、196,489,172 字节，已超过 4,800 文件/175 MB 的仓库预算；本轮归档减少新增开销，未消除既有预算债。卫生脚本没有预算检查，因此 `errors: 0` 不代表预算达标。未删除历史证据或放宽门槛。

## 提交与分支边界

完整回归原文为 `rtl-all-retry.log`、真实退出码为 `rtl-all-retry.exit`；`regression-summary.json` 记录日志 SHA256、预期故障注入与四档完整 CoreMark 结果。四档退休指令数均为 10,106,386，周期数依次为 19,057,438 / 17,114,141 / 16,335,562 / 16,232,079，与上轮基线一致。

PR #87 先以草稿保存远端已提交的 77 个提交；本地 NC 源码理解门槛已 3/3 通过，问答原文及判定见 `report/llm_log/2026-10-24-pr87-merge-sync.md`。完整回归已结束，提交并更新 PR 后合并。合并后只允许快进或普通合并同步四个分支，禁止 reset/强推覆盖独有提交；不直接 push main。未来合并 SHA 由 GitHub PR 状态和同步后分支查询核对，不在本提交中预写。
