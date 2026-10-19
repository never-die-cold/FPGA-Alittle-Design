# Pi 相机预览服务：手动与开机复验

适用：项目专用卡、Pi 4B/CM3、Trixie、multi-user.target、无显示管理器。
前置：HDMI 实际 720p60；edgesight 在 video 组，不带 sudo 的预览正常。
来源文件为 sim/scripts/pi-camera-preview.service；第 1 步不执行 enable。

1. 在 Pi SSH 按 Ctrl+C 停止已有预览，再创建持久项目目录：
```bash
mkdir -p ~/FPGA-Alittle-Design/sim/scripts
```
2. 在电脑另外打开 PowerShell，复制仓库原文件（地址须与实际 SSH 地址一致）：
```powershell
scp "E:/Projects/FPGA-Alittle-Design/sim/scripts/pi-camera-preview.service" "edgesight@[fe80::fa0b:cce2:4ca9:96ba%10]:/home/edgesight/FPGA-Alittle-Design/sim/scripts/pi-camera-preview.service"
```
该 IPv6 地址及 %10 为本机既有连接参数；地址改变时按实际 SSH 连接替换。
3. 回 Pi SSH，核对 SHA256，检查语法；echo 必须紧接 verify 执行：
```bash
sha256sum ~/FPGA-Alittle-Design/sim/scripts/pi-camera-preview.service
systemd-analyze verify ~/FPGA-Alittle-Design/sim/scripts/pi-camera-preview.service
echo "verify_exit=$?"
```
SHA256 与电脑 Get-FileHash 结果一致，verify 无诊断且退出码为 0 才继续。
若有诊断，保存完整输出供分析；不能把程序存在等同于服务运行通过。
4. 安装服务（-b 保存已有目标的备份）、重新载入并手动启动：
```bash
sudo install -m 0644 -b ~/FPGA-Alittle-Design/sim/scripts/pi-camera-preview.service /etc/systemd/system/pi-camera-preview.service
sudo systemctl daemon-reload
sudo systemctl start pi-camera-preview.service
systemctl status pi-camera-preview.service --no-pager -l
systemctl show pi-camera-preview.service -p User -p ActiveState -p SubState -p NRestarts -p ExecMainStatus
sudo journalctl -u pi-camera-preview.service -b -n 30 --no-pager
```
观察电脑 USB Video 的相机实时画面；30 秒后再次运行 show 命令。
第一步判据：active/running、User=edgesight、重启计数未持续增长、画面正常。
关闭 SSH 后相机应继续工作；重新登录仍可查看上述状态与日志。
2026-10-06 已取得 verify_exit=0、active/running、NRestarts=0 及用户画面正常确认；
原始输出见 data/logs/2026-10-06-pi-boot/service-manual-check.txt。

停止服务并改回手动预览：
```bash
sudo systemctl stop pi-camera-preview.service
rpicam-hello --timeout 0 --fullscreen --viewfinder-width 1280 --viewfinder-height 720
```
服务运行时不要再启动第二个相机进程。SIGINT 用于正常停止并释放相机/显示资源。
异常退出后每 5 秒重试；StartLimitIntervalSec=0 关闭启动频率限制，不保证画面正常。
User/SupplementaryGroups 设置运行账号和设备权限；Type=exec 检查程序执行成功，
仍须以相机日志和采集画面判断初始化成功。日志输出到 journal。
WantedBy 仅声明 enable 时加入的启动目标；安装文件和 start 不等于已配置开机启动。
第 1 步实测与理解确认已完成，可执行第 2 步。

## 第 2 步：启用开机启动并重启复验

保持 HDMI 与采集卡连接。Pi SSH 逐条执行，is-enabled 应显示 enabled 才重启：
```bash
sudo systemctl enable pi-camera-preview.service
systemctl is-enabled pi-camera-preview.service
sudo reboot
```
SSH 断开是重启的预期结果。等系统启动，先观察电脑是否自动出现相机实时画面。
重新 SSH 登录后不执行 start 或手动 rpicam-hello；仅查询：
```bash
systemctl show pi-camera-preview.service -p UnitFileState -p User -p ActiveState -p SubState -p NRestarts -p ExecMainStatus
sudo kmsprint
sudo journalctl -u pi-camera-preview.service -b -n 30 --no-pager
```
判据：UnitFileState=enabled、User=edgesight、active/running，重启计数不持续增长；
本次 boot 日志已创建 DRM 预览；实际 HDMI 为 1280×720@60/74.250 MHz，电脑画面正常。
如失败，先保留以上原始输出供分析；手动 start 后的画面不能代替此次开机验收。
2026-10-06 已回传重启后 enabled、active/running、User=edgesight、NRestarts=0，
新 boot 日志约 12 秒完成 CM3/DRM 配置；HDMI 实际仍为标准 720p60。
原始证据：data/logs/2026-10-06-pi-boot/service-after-reboot.txt。
用户随后确认「自动回复了」（上下文为重启后画面自动恢复）：未手动启动相机时，
电脑端实时画面自动恢复正常。直连采集链路及本次重启自动预览验收通过。
尚未验证长时间运行、断电再上电和真实相机经 PYNQ 的路径。
停用开机启动并停止当前服务可用 `sudo systemctl disable --now pi-camera-preview.service`。

依据：[Debian 服务手册](https://manpages.debian.org/trixie/systemd/systemd.service.5.en.html)、
[语法验证手册](https://manpages.debian.org/trixie/systemd/systemd-analyze.1.en.html)。
启动启用依据：[systemctl 手册](https://manpages.debian.org/trixie/systemd/systemctl.1.en.html)。

## 接入 PYNQ：加载已有视频程序

接线：树莓派 HDMI → PYNQ HDMI IN → HDMI OUT → USB 采集卡 → 电脑。
串口也可控制 PYNQ，不需要把树莓派的网线移走；本次为 COM12、115200、8N1、无流控。
同一串口同一时刻由一个程序占用。以下命令在 PYNQ 执行，不在树莓派执行。

本板已有部署目录 `/home/xilinx/vision_m2`，内含 `vision.bit`、同名 hwh 和 `m2_onboard.py`。
先按本板现有环境脚本初始化 root 子进程，再加载：

```bash
sudo bash -c 'source /etc/profile.d/xrt_setup.sh && source /etc/profile.d/pynq_venv.sh && python3 /home/xilinx/vision_m2/m2_onboard.py load'
```

应有 `pipe @ 0x40000000` 和 `PASS: load`；若失败先保留输出，不继续访问视觉寄存器。
等待至少 3 秒，再检查视频帧首提交确认：

```bash
sudo bash -c 'source /etc/profile.d/xrt_setup.sh && source /etc/profile.d/pynq_venv.sh && python3 /home/xilinx/vision_m2/m2_onboard.py smoke'
```

2026-10-06 实测 `PASS: load`、`PASS: smoke`，配置确认号从 0 变为 1。
2026-10-07 用户报告纯黑，串口也无响应；仅重启 PYNQ 后恢复 shell，再装载同一 bit，smoke PASS。
关闭其他占用采集卡的软件后，项目抓帧取得真实相机画面；独占采集 MJPG/1280×720/30fps，
连续 24 帧成功，证据见 `data/logs/2026-10-07-pi-pynq/README.md`。
输入与输出抓帧链路本轮已通；项目实时窗口已打开，用户随后回复「ok」接受当前预览结果。
板端 bit 哈希与本地现存构建不同；实测版本与原始输出见
`data/logs/2026-10-06-pi-pynq/README.md`。断连、冷上电、长时间运行尚未复验。
PYNQ 断电后 bit 配置丢失；本节只完成手动装载，未配置 PYNQ 开机自动装载。

电脑端同一时刻只运行一个使用 USB Video 的采集程序，重载后可关闭再打开原采集软件。
本次 DirectShow 枚举确认 USB Video 为索引 1；索引可能随设备变化，需重新确认。
项目既有预览程序可用 `vision_preview.exe --source 1`，按 Q 或 Esc 退出并释放设备。
预览横幅 VIDEO ONLY / UNASSOCIATED 表示当前视频没有关联板端识别结果，不能当作检测通过。

第一次仅指定 Python 路径加载时报 `No Devices Found`，初始化 XRT/PYNQ 环境后成功。
本板 XRT 脚本设置 `XILINX_XRT=/usr`，不要直接套用其他板卡的安装路径。
从串口以 root 初始化环境也见 [Xilinx 的 PYNQ 使用说明](https://github.com/Xilinx/DPU-PYNQ/blob/master/README.md)。
