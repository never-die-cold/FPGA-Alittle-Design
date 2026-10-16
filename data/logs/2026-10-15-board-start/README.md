# 2026-10-15 返板起点：N01 与视频短基线

分支 `dev/model`，完整 HEAD 见 `head.txt`。开工时已有多处未提交改动，
本轮只新增本证据目录及 `report/llm_log/2026-10-15-board-start.md`；
未修改 RTL、驱动或脚本，未提交。
已阅读 `docs/workflow.md`、主计划、核计划、核契约及 N03 返板执行单。

## 已观察事实

- 用户确认接线：树莓派相机 → 树莓派 HDMI OUT → PYNQ HDMI IN →
  PYNQ HDMI OUT → USB 采集卡 → 电脑，树莓派已输出画面。
- COM12 / 115200 / 8N1 / 无流控可用，`id` 返回 `uid=1000(xilinx)`。
- 本轮读取 boot_id：`c291b2c8-0d7b-49e9-9511-4f5c66d2e37b`。
- `run_pynq_baseline.ps1` 退出 0；Python 3.10.4、PYNQ 3.1。
- eth0 为 DOWN；本轮使用串口，未更改网络。
- 原 vision 的 bit/hwh 和两份 Python 文件 SHA 与 10/12 基线一致；
  Python 文件还与本机当前源码 SHA 一致，见 `local-input-sha256.json`。
- 初始 PL 元数据的文件名/时间均为 `None`，IP 列表是 base 视频结构；
  不能据此确认实际配置文件，更不能声称原 vision 正在运行。
- 进程筛查未见匹配的 c01/n03/vision Python、mplayer 或 ffmpeg；
  该筛查不构成排除全部 DMA 使用者的证明。
- `sudo -n true` 退出 1，原始输出 `sudo: a password is required`。
- DirectShow 列出 ASUS FHD webcam、USB Video、OBS Virtual Camera；
  USB Video 唯一，index=1。
- 初始 UVC 成功读取 24 帧，BGR `(720,1280,3)`，PNG 回读像素一致；
  人工目视为黑画面，初始视频内容验收未通过。
- 用户认证后 `sudo -n true` 退出 0，boot_id 保持不变。
- 原 vision `load` 退出 0：`pipe @ 0x40000000 range 0x10000`、`ps7`。
- 原 vision `smoke` 退出 0：`busy=False, applied_config_id=1`，
  输出 `PASS: smoke（视频在位，帧首整组应用已确认）`。
- 恢复后 UVC 再读 24 帧，PNG 回读一致；人工目视为彩色桌面及螺栓、
  螺母和垫圈，已恢复真实相机内容；局部物体裁边，未作正式定标或采集。
- 最终 PL 路径 `/home/xilinx/vision_m2/vision.bit`，IP=`pipe,ps7`，
  boot_id 与初始一致。PL timestamp 原样保留，不用其日期推断构建版本。

## 仓库复现入口与结果

在仓库根目录以 PowerShell 执行；每次复验需使用新的日志文件/目录。

```powershell
.\sim\scripts\pynq_serial_command.ps1 -Port COM12 -Command 'id' -LogPath data/logs/<new-run>/identity.txt
.\sim\scripts\run_pynq_baseline.ps1 -Port COM12 -OutputDirectory data/logs/<new-run>/baseline
& 'C:/Users/ASUS/AppData/Local/Programs/Python/Python312/python.exe' sim/scripts/capture_uvc_raw.py --output-dir data/logs/<new-run>/uvc --frames 24
git diff --check
git diff --cached --check
```

原始串口命令、返回值和主机 UTC 时间保存在 `n01-*.txt` 与 `baseline/*.txt`。
UVC 实测输出在 `uvc-initial-retry-console.txt`，退出码文件为 0；
画面与模式/像素及 PNG SHA 在 `uvc-initial-retry/`。
恢复后输出在 `uvc-after-vision-console.txt`，退出码为 0；
实际画面和元数据在 `uvc-after-vision/`。
原 vision 操作复用仓库 `pynq_serial_command.ps1` 入口，
精确板端命令及退出码保存在 `vision-load.txt`、`vision-smoke.txt`、
`n01-final-active-state.txt`；load/smoke 含明确的板端与主机超时。
diff 两项退出均为 0，未暂存检查有一条既有 CRLF 转 LF 提示。

## 主机环境问题与认证

首次调用本机 Python312 被主机沙箱拒绝启动，进程没有启动；
`uvc-initial.exit.txt` 为空，不能解读为成功退出。
工具授权后使用同一 Python 和仓库入口重试，UVC 采集成功。
捆绑 Python 的备选环境缺少 cv2，未用于采集。
用户终端未将 `pwsh` 加入 PATH，首次认证命令未执行；
已改为 Windows 自带 `powershell.exe`，并打开独立交互认证窗口。
用户另开同一命令时 COM12 拒绝访问；关闭 agent 先前启动的认证窗口
（PID 42656，核对进程名、启动时间），实际打开 COM12 成功并取消
遗留 sudo 提示，回到 shell。该过程的工具输出记录在本次聊天；
不把手工转述冒充串口原始日志。随后只保留用户一个认证入口，用户报告 PASS。
密码由用户在隐藏输入提示中输入，不进入本目录；后续串口入口均已释放。

## 当前边界与下一项

本轮已完成 N01 只读核查、原 vision 恢复与短基线；黑屏在 load 后消失，
未据此证明黑屏的所有可能原因或连续动态视频的正确性。
未下载 C01 候选、未启动自定义 DDR 捕获、未改变相机输出。
下一项为完整 N02 长测/逐例恢复，再按 N03 执行单核对候选兼容条件及取帧。
本轮不签完整 N02/N03、DDR 帧或工业闭环通过。
原 vision 仍缺完整构建源码锚点，不能替代当前未提交 RTL 的板级验收。
未实现/未接入：CNN 存储与 MMIO/DMA 集成、首网硬件输出、
核工业固件与真实硬件 LIVE 后端；完整 N02/N03 和定标/正式采集待验收。
