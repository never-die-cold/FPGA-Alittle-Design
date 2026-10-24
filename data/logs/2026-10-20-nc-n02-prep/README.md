# NC N02 操作卡：离板准备，未签实测

- 日期/执行人：2026-10-20，nc_n02 agent；未连接串口、相机、板卡或任何服务。
- 版本：dev/riscv@5f8abe25906d918f15809c888a7d3c1182aa3e08；本卡开工时无源码改动，工作区只有本轮并行 agent 的未提交记录目录与自动生成的 data/logs/README.md 索引。
- 命令/方法：只读 Git 状态、仓库脚本与历史原始输出；本卡中的板端命令未执行。
- 结果：操作入口已核对并列出证据；N01/N02 本轮全部待主控实测，不生成硬件 PASS。
- 产物：本 README、[run-sheet.md](run-sheet.md)（四例逐条顺序单，未执行）与 [watch-mock.txt](watch-mock.txt)；无输入快照，无复制源码。
- 边界：只准备 N02；首网硬件输出、N03、工业验收均不在本卡通过范围。

## 一次只允许一个人操作板子

主控独占 COM12、PL、相机、UVC、EXE；其它 agent 只读文件。
同一时刻只有一个 MMIO 配置写入者；watch 与 smoke/服务不得并发写配置。
冷上电、改接线及源端开停由 NC 在场操作；日志 agent 不代做。
每例独立新目录，记录前后 boot_id、PL 实例、bit/hwh SHA、源模式、状态、画面、动作时间及恢复耗时。
本轮已由主控取到的当前基线：boot_id `9d7a5170-2b47-4a53-8b1e-8ec3fc418369`，PL 未加载（`PL.bitfile_name=None`），四例均须与它比对前后值。

## 公共前置与恢复

1. 在原 vision 已确认、无 DMA/服务占用、串口已登录且 sudo 可用后操作；认证由本人输入。
2. `sim/scripts/run_pynq_baseline.ps1 -Port COM12 -OutputDirectory <仓库内新目录>` 收系统/网络/文件/PL 信息；该脚本不采 boot_id，也不验证视频功能。输出目录必须尚不存在且在仓库内（`run_pynq_baseline.ps1:4,6-7`）。
3. 用 `sim/scripts/pynq_serial_command.ps1 -Port COM12 -Command 'cat /proc/sys/kernel/random/boot_id' -LogPath <仓库内新文件>` 单独留 boot_id；每条命令立即保存原始退出码。该包装器只收单行命令、日志文件不得已存在（`:13-14`）。
4. 以下是已存在的板端恢复命令（主控执行，不能在电脑/Pi 执行）：

```bash
sudo bash -c 'source /etc/profile.d/xrt_setup.sh && source /etc/profile.d/pynq_venv.sh && python3 /home/xilinx/vision_m2/m2_onboard.py load'
# 等至少3秒；历史恢复检查采用5秒。
sudo bash -c 'source /etc/profile.d/xrt_setup.sh && source /etc/profile.d/pynq_venv.sh && python3 /home/xilinx/vision_m2/m2_onboard.py smoke'
```

load 应打印 `pipe @ 0x40000000` 与 `PASS: load`；smoke 应见配置确认号正确及 `PASS: smoke`。NOVIDEO（退出 3）不能算通过（`m2_onboard.py:53,64-66`）。
预期字节（可写在每例记录里）：vision.bit `4f0c491a6383d8a11f87cd2de260027f519dbd466942d0b1b6e36198e39d5be5`、vision.hwh `c0adfd3656c2fdb0468de356dc8232857580286d48977c41d6ee61edc3b7b5a5`；两者与归档 XSA 内部文件相同，且与板端 2026-10-20 只读基线相同。
电脑采集入口：`python sim/scripts/capture_uvc_raw.py --output-dir <仓库内新目录> --frames 24 [--save-all]`；先关闭 EXE 等其它采集程序，完成释放后再开 EXE。
默认模式连续读取 24 帧但只保存最后一张 raw.png 及其像素 SHA，metadata 里只有 24 条读帧耗时——此时不能冒称 24 张原帧/逐帧 SHA 齐全。`--save-all` 是主控 2026-10-20 在工作区新加的**未提交**改动（逐帧 `frame-NNN.png`、`saved_frames[]` 逐帧像素/Png SHA、逐帧回读校验），本卡未实测；要签"24 帧逐帧证据"必须显式带该参数，并核对 PNG 张数、`saved_frames` 条数与 `frames_read` 三者相等。

## 本轮只读核对结果

核对对象：本工作区文件（dev/riscv@5f8abe2）与主控 2026-10-20 板端只读基线 `data/logs/2026-10-20-nc-board/baseline/*.txt`。以下结论只针对仓库文件与既有原始输出，未新增任何板端观察。

| 主张 | 证据 | 结论 |
| --- | --- | --- |
| 板端 m2_onboard.py / vision_regs.py 与本仓库同内容 | 仓库 SHA256 `679befc3…64cd` / `1b30a62d…0479` 等于板端 `baseline/artifacts.txt` | 字节一致；这不证明板端由 5f8abe2 部署，也不证明当前 PL 正在跑该位流 |
| onboard_smoke.py 已在板端 | `artifacts.txt` 只哈希 vision.bit/hwh、m2_onboard.py、vision_regs.py | 未部署/未核对；其仓库 SHA256 为 `1d27c8c7…95c8`，使用前必须上传再对哈希 |
| 仓库有没有能直接跑的部署入口 | `deploy_vision_onboard.sh:21-25` 要求本地 `sim/build/hdmi-project/vision.bit`（本工作区不存在）；`make_board_pkg.sh:22` 的包不含该脚本 | 都不能直接用；手工 scp 或用 `send_pynq_file.ps1` 的 c01 目录，步骤见 [run-sheet.md](run-sheet.md) §0 |
| 包装器上限 | `pynq_serial_command.ps1:5` ValidateRange(1,300) | 600 秒连续观测不能直接交给它（与卡片一致） |
| 退出 124 的含义 | `:49-52` 写 `timeout; remote completion unconfirmed; no interrupt sent` | 与卡片一致：不能当作任务已停 |
| watch 不加载 overlay | `onboard_smoke.py:91` 直接构造 VisionRegs，`stage_watch` 无 Overlay/ip_dict | 前置必须已有 load PASS；未装载时 MMIO 可能挂死或表现为持续 BUSY |
| watch 摘要与判定 | `:107-122` | 字段与卡片审计串一致；**BUSY 分支也会置 `saw_stall`**（`:104-108`），必须同看 `saw_busy` |
| watch 失败码 | `:175-178` | FAIL(W)=9；全程无流也 9；`end_stream` 取最后状态，未进入循环为 None |
| 逐帧证据入口 | 工作区 `git diff sim/scripts/capture_uvc_raw.py`（主控未提交改动）：新增 `--save-all` | 默认仍只存最后一帧；逐帧必须显式带参，本卡未实测，该改动也不能算已验收 |
| watch 摘要契约可离板复跑 | 本次实跑 `python src/pynq_host/onboard_smoke.py watch-mock`，输出见 [watch-mock.txt](watch-mock.txt) | PASS(W)、exit 0，且同一次运行 `saw_stall=True saw_busy=True` 仍给 PASS——印证修正 3；仅验证逻辑后端，不验证板端 MMIO 路径 |

## 需要主控注意的三处修正

1. **交互串口不留本地日志**：`pynq_serial_console.ps1:11` 明确 "No local input echo or file log"。600 秒的完整日志只能落在板端文件，再用短包装器分段 `tail`/`wc -c`/`cat` 取回；不能拿控制台滚屏当证据，也不要把多段 `tail` 拼成"连续观测"。
2. **watch 没有现成可跑的部署入口**：唯一打包 onboard_smoke.py 的 `deploy_vision_onboard.sh:21-25` 要求本地 `sim/build/hdmi-project/vision.bit`，本工作区已确认不存在，脚本会 `exit 1`；`make_board_pkg.sh:22` 的包只有 vision_regs/vision_demo/m2_onboard。因此只能手工 `scp` 到 `/home/xilinx/vision_m2/`（PC 侧 ssh/scp 可用、公钥已存在，板端 authorized_keys 由主控确认），或退而用 `send_pynq_file.ps1:5` 传进 `c01-<32位hex>/` 并置 `PYTHONPATH=/home/xilinx/vision_m2`。上传后立刻核对 `1d27c8c7…95c8`。
3. **`saw_stall` 不等于断流**：BUSY 样本同样把 `saw_stall` 置真。持续在流的判据必须同时是 `saw_stream=True saw_stall=False saw_busy=False end_stream=STREAM`。离板自测已复现这种组合：`saw_stall=True saw_busy=True end_stream=STREAM` 依然 PASS(W) 且 exit 0（[watch-mock.txt](watch-mock.txt)）。因此 600 秒用例只贴 PASS(W) 或退出码等于没贴。

## 600 秒观测的建议骨架（未执行、未核对）

历史唯一跑通过的形态是 2026-10-12 的 `-TimeoutSeconds 275` + 板端 `timeout -k 5s 255s`（见 `data/logs/2026-10-12-n02-extended/README.md:15`）。600 秒需要单进程持久任务，骨架如下；`setsid` 与超时保护是否在板端可用、日志属主如何，须由主控先核对，本卡未实测。

```bash
sudo bash -c 'source /etc/profile.d/xrt_setup.sh && source /etc/profile.d/pynq_venv.sh && cd /home/xilinx/vision_m2 && PYTHONPATH=. setsid timeout -k 5s 620s python3 -u onboard_smoke.py watch 600 > /home/xilinx/vision_m2/watch-600.log 2>&1 &'
# 之后每次用短包装器只读查询，不启动第二个 watch：
sudo tail -n 5 /home/xilinx/vision_m2/watch-600.log
pgrep -af onboard_smoke
```

只有 `timeout` 结束、进程退出、日志出现 `WATCH-SUMMARY` 且 `wc -c` 与起止时间自洽，才算一次 600 秒。

## 四项检查，按主控板卡窗口串行做

| 用例 | 做什么 | 何时算通过 |
| --- | --- | --- |
| 冷启动 | NC 在场正常停服务/停止DMA，记录关机前状态；安全断电再上电，重新认证，只读基线；手动原vision load/smoke，再采UVC | 新boot_id、预期文件哈希、load/smoke和真实画面齐；本项目没有PYNQ自动加载保证，不把手动恢复记成自动恢复 |
| 在流600秒 | 原vision稳定后，用下述watch入口连续观测600秒，期间不改源、不重载；采集程序可旁路观察，但不能写PL配置 | 原始完整时长、前后boot_id相同，SUMMARY持续STREAM且无STALL/BUSY，画面正常；配置心跳非逐帧质量保证 |
| 软件断源恢复 | 确认源控制通路，启动有界watch；NC在源设备停止输出再恢复；记录动作时间和真实画面 | 观察STREAM→STALL/BUSY→STREAM，恢复后smoke/UVC正常，PYNQ boot_id不变；未观测断流不能签软断用例 |
| overlay重载 | 先停watch/服务/DMA，记录前状态，再执行公共load→等待→smoke→UVC | 原vision路径/哈希正确，boot_id不变、load/smoke及真实画面恢复，记录恢复耗时 |

仓库正式监视入口：`src/pynq_host/onboard_smoke.py watch 600`，需要其同目录依赖 vision_regs.py；先核实板端副本路径与 SHA，不能假定已部署。
板端运行时初始化上述 XRT/PYNQ 环境；以 `python3 -u <已核对绝对路径>/onboard_smoke.py watch 600` 执行。watch 自身不下载 overlay。
持续在流需审计 `WATCH-SUMMARY: saw_stream=True saw_stall=False saw_busy=False end_stream=STREAM`；watch 允许断流后恢复时 exit0，只有 PASS(W)/exit0 不够。
软件断源必须核实实际源。如果当前 Pi 确实运行既有 `pi-camera-preview.service`，在 Pi 执行 `sudo systemctl stop pi-camera-preview.service`，恢复执行 `sudo systemctl start pi-camera-preview.service`，并保存 status/journal；不在 PYNQ 上运行这些源命令，不并发启动第二个 rpicam 进程。该服务本身就是 Pi 侧预览，停它等于停 HDMI IN 的源——本卡未确认当前源究竟由它还是手动 rpicam 提供。

## 失败时先保留现场

串口包装器退出 124 只表示远端完成未知，且未发中断；不能当成任务已停，不能另开捕获。
遇 UNSAFE-STOP 保持板端进程/原生缓冲存活，禁止强杀、自动退出或重载 overlay；NC 在场按对应复位流程恢复。
物理拔插曾导致异常重启（`nc-offline-readiness-2026-10-12.md:33`），本卡软件断源不替代物理拔插验收；不临时改成拔线。
每例失败保留原始记录，恢复独立记结论；收工恢复原 vision 并重新 smoke/UVC。

依据：docs/runbooks/nc-return-checklist-2026-10-12.md、nc-offline-readiness-2026-10-12.md、pi-camera-preview-runbook.md、n03-custom-return-runbook-2026-10-14.md；sim/scripts/{run_pynq_baseline.ps1,pynq_serial_command.ps1,pynq_serial_console.ps1,capture_uvc_raw.py,send_pynq_file.ps1}；src/pynq_host/{m2_onboard.py,vision_regs.py,onboard_smoke.py,ONBOARD.md}；data/logs/2026-10-12-n02-extended/README.md、data/logs/2026-10-20-nc-board/README.md。
未完成：本轮四例实测、逐帧入口未实测（`--save-all` 已在工作区、未提交）、源控制通路确认、600 秒骨架未核对；watch-mock 只走逻辑后端，板端 MMIO 与真实断源未验；[run-sheet.md](run-sheet.md) 全篇未执行，0.1 的 scp 与板端 authorized_keys 未确认；板端 watch 副本指纹只完成 m2_onboard.py/vision_regs.py 两项，onboard_smoke.py 尚未上传；不修改公共索引，由主控统一更新。
