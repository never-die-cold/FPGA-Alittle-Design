# 2026-10-27 重新上板状态检查

- 日期：2026-10-27，主机 Asia/Shanghai，约 22:52；板卡时钟仍为 9/22，不用于判断实际日期。
- 源码：dev/riscv，cfbded8；只读检查，无业务代码、位流或服务状态变更。新增本目录诊断脚本和证据，并补充 plan.md §3.1。
- 硬件：用户确认沿用树莓派 HDMI → PYNQ IN、PYNQ OUT → USB 采集卡，网口、USB 串口均连接。
- 运行状态与剩余任务的事实入口：[plan.md §3.1](../../../plan.md#31-当前状态)。

## 复现命令

在仓库根目录、使用已安装 paramiko/OpenCV 的 Python 执行；每次采集使用新的目录名。

```powershell
python -X utf8 sim/scripts/board_ssh.py --command 'uname -a; cat /proc/sys/kernel/random/boot_id; uptime; ip -4 addr show eth0; systemctl --no-pager --full status bootpy.service fpga-vision-boot.service; ss -ltnp; dmesg' --log data/logs/2026-10-27-reboard-status/board-rerun.log
python -X utf8 sim/scripts/board_ssh.py --script data/logs/2026-10-27-reboard-status/probe-board.sh --log data/logs/2026-10-27-reboard-status/runtime-rerun.log
powershell -NoProfile -File sim/scripts/list_dshow_video.ps1
python -X utf8 sim/scripts/capture_uvc_raw.py --output-dir data/logs/2026-10-27-reboard-status/uvc-rerun --frames 24
curl.exe --noproxy '*' --connect-timeout 3 --max-time 5 -v http://192.168.50.99:8765/v1/status
git diff --check
```

## 原始结果及产物

- `board-status.log`：新 boot_id `43effa49-7325-42a3-849a-a06413fd6809`；eth0 1Gbps，全双工；bootpy 退出 0，视频服务退出 1。该 SSH 汇总命令最终退出 0 不表示各服务成功。
- `board-detail.log`：单调时间日志显示 base 在约 120.9 秒加载、vision 在约 145.1 秒加载，等待 30 秒配置生效后超时。启动 cron 只保留 IP 配置。产品服务无进程、无 8765 监听，原部署目录保留。
- `runtime.log`：当前 PL 路径为 vision_m2/vision.bit，SHA256 `4f0c491a6383d8a11f87cd2de260027f519dbd466942d0b1b6e36198e39d5be5`；FCLK0=100MHz。确认路径及 IP 映射后只读三次 R0/R11/R12，均为 0/1/0，没有重复提交或写寄存器。
- `http-status.log`：curl 原始结果为退出码 7、Connection refused；用于保存输出的 PowerShell 管道整体成功不代表 HTTP 成功。
- `uvc/devices.txt`：USB Video 为 DirectShow 索引 1；主机另枚举 USB Serial Port (COM12)，状态 OK。本次未打开串口，不代表已核验 UART 数据。
- `uvc/metadata.json`：采集 24 帧成功，1280×720 BGR uint8；脚本 PASS 仅证明读取及 PNG 无损保存，不能证明 HDMI 内容正常。`uvc/raw.png` 视觉检查为黑屏；SHA256 `08f1c9deef07be2f994555c18b6471d4c876c89b23eaa5dcdc33f513b955b0fe`。

## 边界

没有启动 EXE、执行推理、切换位流、修改板端服务、运行仿真或重新综合。旧多目标构建的本地日志仍保留 `Could not open 'C' for writing` / `tclapp::load_apps` 错误，没有新修复位流产物。
busy=1/应用编号=0 与黑屏表明视频链路尚未恢复，尚不能区分源端无输出、HDMI 接入/锁定或 PL 视频链问题。启动分区存在 FAT 未正常卸载警告；当前 boot 的 dmesg 未见 mmc timeout、ADMA error 或 I/O error，不认定 SD 卡损坏，未对已挂载分区运行 fsck。
