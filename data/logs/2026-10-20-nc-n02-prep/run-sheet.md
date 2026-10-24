# N02 上板执行顺序单（草稿，未执行）

- 状态：离板草稿。本轮未打开 COM12、UVC、JTAG 或任何服务，下面每条命令都**未经实测**。
- 配套：[README.md](README.md) 的操作卡与本单同一目录；操作卡讲原则，本单把四例拆成按顺序可敲的步骤和要留下的文件。
- 用法：每例先建 `data/logs/2026-10-20-n02-<case>/`，下列日志全部落在该目录，命令里的 `<case>` 同步替换。

## 0. 一次性准备（做完记到 case-00）

| 步 | 动作 | 入口 | 判据 |
| --- | --- | --- | --- |
| 0.1 | 上传 watch 脚本 | `scp src/pynq_host/onboard_smoke.py xilinx@192.168.50.99:/home/xilinx/vision_m2/` | 板端 `sha256sum` 等于 `1d27c8c7…95c8`；只新增该文件，不覆盖已核对一致的 m2_onboard.py / vision_regs.py |
| 0.2 | 确认源 | 在 Pi 上 `systemctl is-active pi-camera-preview.service` | 记录 active/inactive 与实际出图来源；断源用例只能按这里确认的那一路做 |
| 0.3 | 释放 UVC | 关闭 EXE 与其它预览 | `sim/scripts/list_dshow_video.ps1` 仅剩一个 USB Video |

`deploy_vision_onboard.sh` 在本工作区跑不通：`:21-25` 要求 `sim/build/hdmi-project/vision.bit`（本工作区已确认不存在）；`make_board_pkg.sh:22` 打的包里也没有 onboard_smoke.py。所以 0.1 只能手工 scp，或用 `send_pynq_file.ps1` 传进 `c01-<hex>/` 再置 `PYTHONPATH=/home/xilinx/vision_m2`。

## 1. 每例开场（三次只读，各自新文件）

1. boot：`sim/scripts/pynq_serial_command.ps1 -Port COM12 -Command 'cat /proc/sys/kernel/random/boot_id' -LogPath data/logs/2026-10-20-n02-<case>/boot-before.txt`
2. 基线：`sim/scripts/run_pynq_baseline.ps1 -Port COM12 -OutputDirectory data/logs/2026-10-20-n02-<case>/baseline`（八项里已含 `PL.bitfile_name`/`timestamp`/`ip_dict`，不必另发 PL 命令）
3. 采集设备：`sim/scripts/list_dshow_video.ps1`，输出存 `devices-<n>.txt`

板端命令都要单行传入，外层用双引号、内层保留单引号，例如
`-Command "sudo bash -c 'source /etc/profile.d/xrt_setup.sh && source /etc/profile.d/pynq_venv.sh && python3 /home/xilinx/vision_m2/m2_onboard.py smoke'"`。

## 2. 四例

### 2.1 冷启动

1. NC 正常停服务/停 DMA，记录关机前 boot_id、PL 路径与画面。
2. 安全断电→上电；重新登录后重复第 1 节，文件名用 `boot-after.txt`、`baseline-after/`。
3. 加载：`m2_onboard.py load`，等 5 秒。
4. 冒烟：`m2_onboard.py smoke`（NOVIDEO/退出 3 不算通过）。
5. 采集：`python sim/scripts/capture_uvc_raw.py --output-dir data/logs/2026-10-20-n02-coldboot/uvc-1 --frames 24 --save-all`（不带 `--save-all` 只会留最后一帧，不能签逐帧证据）。

判据：`boot-after ≠ 9d7a5170-…`、bit/hwh 哈希等于预期两串、load/smoke 各 exit 0、UVC PASS 且画面已目视。手动 load 不能记成自动恢复。

### 2.2 在流 600 秒

1. 前置：本窗口内已有 load/smoke PASS，之后不再改动配置。
2. 按 README 骨架起单进程 watch 600 s，日志写板端 `/home/xilinx/vision_m2/watch-600.log`（脚本同目录，收工可删）。
3. 期间每 60–120 s 用短包装器 `tail -n 5` + `pgrep -af onboard_smoke` 只读确认，**不重启第二个 watch**。
4. 结束后取回整份日志，另记 `wc -c`、起始/结束 UTC、`grep -c EVENT`。

判据：单进程连续 600 s（不是多段相加）、`saw_stream=True saw_stall=False saw_busy=False end_stream=STREAM`、前后 boot_id 相同、旁路 UVC 画面正常。

### 2.3 软件断源恢复

1. 按 0.2 确认的源做动作；确认 watch 已进入 STREAM（先看事件行）。
2. 起有界 watch（如 `watch 150`，包在 `timeout -k 5s 200s` 内，包装器 `-TimeoutSeconds 280`）。
3. 在 Pi 停源服务，记录 UTC；等 watch 打印 STALL/BUSY；再启源服务，记录 UTC。
4. 结束跑 smoke 与 UVC，重读 boot_id。

判据：同一份日志里 STREAM→STALL/BUSY→STREAM、恢复后 smoke 与画面正常、PYNQ boot_id 不变。没观测到断流就不签这一例。

### 2.4 overlay 重载

1. 停 watch/服务/DMA，记录前值（boot_id、PL 路径、画面）。
2. `m2_onboard.py load` → 等 5 s → `smoke`，记各自退出码与耗时。
3. UVC 采一次，核对画面与哈希；重读 boot_id。

判据：boot_id 不变、load/smoke exit 0、画面恢复、恢复耗时已记。

## 3. 每例要填的记录（一例一表）

| 字段 | 内容 |
| --- | --- |
| case_id / 目录 | 如 `n02-2.3`，目录 `data/logs/2026-10-20-n02-srcut/` |
| 版本 | 仓库 commit、板端脚本 SHA（m2/vision_regs/onboard_smoke）、bit/hwh SHA |
| boot_id | before / after，以及是否相等 |
| PL | `bitfile_name`、`timestamp`、`ip_dict` 段名与基址 |
| 源 | Pi service 状态或手动 rpicam、分辨率、动作 UTC |
| 观测 | 事件行、`WATCH-SUMMARY` 原文、`wc -c`、读数次数 |
| 画面 | 每次 UVC 目录、`raw.png` 与 `pixels_sha256`、目视描述 |
| 恢复 | 退出码、恢复耗时、结束画面 |
| 结论 | PASS/FAIL/未测 + 执行人；不以只贴 PASS 代替内容检查 |

## 4. 立即停止的条件

- 包装器退出 124：远端完成未知，先停手，不另开采集。
- 出现 UNSAFE-STOP、板端无响应、boot_id 意外变化：保留现场，NC 按复位流程处理。
- 连续两次 NOVIDEO：先查源分辨率/线缆，不靠反复 load 碰运气。

## 5. 观察技巧（不改证据口径）

`pynq_serial_command.ps1` 在循环里就把收到的字节写入 `-LogPath`（`:40-44`），但控制台只在结束时打印汇总（`:62`）。所以长任务运行时，另开一个 PowerShell 用 `Get-Content <本机日志> -Wait -Tail 20` 看事件即可；不要为了"看实时"再发第二条串口命令——COM12 同一时刻只能被一个程序占用。

本单未执行；四例判定一律以主控实测原始日志为准。
