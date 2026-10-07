# Raspberry Pi 4B 启动诊断（2026-10-06）

## 最新收口状态

CM3 → Pi HDMI → USB 采集卡 → 电脑已实测出图，标准 720p60。
edgesight/video 权限生效；pi-camera-preview.service 已安装并 enabled，
重启后 active/running、NRestarts=0，用户确认未手动启动时画面自动恢复。
完整过程见 [相机链路记录](camera-bringup.md)，原始重启结果见
[service-after-reboot.txt](service-after-reboot.txt)，复现见
[服务操作说明](../../../docs/pi-camera-preview-runbook.md)。
长时间、断电再上电和真实相机经 PYNQ 路径尚未验证；未提交。
以下为历史启动、网络与改密诊断，部分待确认项已由后续相机记录更新。

## 实机观察

- 用户确认：官方电源；PWR 红灯常亮；ACT 上电闪过，之后熄灭。
- HDMI0 经 USB Video 采集卡进入电脑；设备 VID_345F/PID_2109，DSHOW 索引 1。
- `hdmi-raw.png` 显示 `Raspbian GNU/Linux 13 edgesight-pi tty1` 和 `edgesight-pi login:`。
- 屏幕重复显示地址 `fe80::fa0b:cce2:4ca9:96ba`，部分提示地址为空；未显示 IPv4。
- 结论：本次实机已进入 Linux 登录界面；不能用 ACT 熄灭认定未启动。

## 仓库内抓帧入口

在项目根目录运行已有构建产物（设备索引需现场确认）：

```powershell
sim/build/vision-client/dist/vision_preview/vision_preview.exe --source 1 --frames 12 --headless --save data/logs/2026-10-06-pi-boot/hdmi-preview.png
```

构建入口见 `src/vision_client/README.md`；对应源码 `src/vision_client/preview.py`。
`hdmi-preview.png` 带现有程序横幅；`hdmi-raw.png` 是同一采集设备的 1920×1080 原始帧。
原始抓帧输出（`hdmi-raw.log`）：`Captured USB Video index 1: (1080, 1920, 3)`。

## 网络诊断边界

- 电脑直连网口：Up / 1 Gbps，IPv4 `169.254.87.3/16`，接口索引 10。
- 当前 Codex 执行环境存在 `codex_sandbox_offline_block_outbound` 出站阻断规则。
- IPv6 TCP 探测返回套接字访问权限拒绝；这不是树莓派 SSH 服务失败的证据。
- 未确认：树莓派 SSH 服务、用户登录、IPv4 地址分配和直连网络稳定性。
- 未修改：SD 卡、树莓派配置、电脑网络或防火墙规则；未提交代码。

## 用户终端复测与排查更新

- 用户独立 PowerShell 执行 IPv6 SSH，同样返回连接阶段 `Permission denied`。
- 核对后，Codex 出站阻断规则的 LocalUser 仅为 CodexSandboxOffline；不能据此解释 ASUS 用户的报错。
- ASUS PowerShell 的父进程为 explorer.exe；不是当前工具终端。
- `tun0`（sing-tun Tunnel）处于 Up；用户确认代理软件开启了 TUN 模式。
- TUN 影响直连 IPv6 是待检验假设；下一步暂时关闭该代理的 TUN，用户在原终端复测 ping / SSH。
- 精确 WFP 过滤查询被 Windows 管理员权限要求拦住，未读取到匹配过滤器；未关闭任何过滤规则。

## 关闭 TUN 后的复测

- 用户在独立 PowerShell 对同一 IPv6 地址 ping：发送 3，接收 3，0% 丢包，0–1 ms。
- 随后直连 TCP 22 成功，读取到 `SSH-2.0-OpenSSH_10.0p2 Raspbian-7+deb13u4`。
- Windows 邻居表：`fe80::fa0b:cce2:4ca9:96ba`，MAC `D8-3A-DD-F2-9A-D4`，`Reachable`。
- 当前确认：系统已启动、IPv6 直连可达、SSH 服务正在监听。
- 当前待确认：`edgesight` 用户认证；树莓派 IPv4/互联网配置；开启 TUN 时的局域网兼容配置。
- 后续登录命令：`ssh -6 "edgesight@fe80::fa0b:cce2:4ca9:96ba%10"`。

## 用户指定密码重设（准备完成，实际执行待上电）

用户明确要求 pi/edgesight 的密码等于各自用户名。已对 F: 项目卡部署一次性开机步骤，无格式化或重刷。
卡上改动：更新 user-data、userconf.txt、cmdline.txt；新增 pi-password-reset.sh、pi-password-reset.hashes；原三个配置文件备份于 pi-password-reset-backup/。
开机脚本在 Linux 中创建缺失账号并用 chpasswd -e 写入密码；恢复原启动参数后成功重启一次。启动分区 pi-password-reset.log 记录结果。
systemd 启动机制依据：[Debian trixie systemd-run-generator 手册](https://manpages.debian.org/trixie/systemd/systemd-run-generator.8.en.html)。

准备入口（仅限已核验的本项目卡；已有备份时拒绝重复覆盖）：

```powershell
& 'C:/Users/ASUS/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B sim/scripts/prepare_pi_password_reset.py F:/
```

验证结果见 password-reset-preparation.log：两账户哈希对应用户名；账号配置、部署脚本、启动参数和备份回读 PASS；部署的 Bash 脚本语法退出码 0；git diff --check 无输出。
尚未执行：树莓派上电运行改密步骤，以及两个账号的实际密码登录。准备完成不能写成密码已经在运行系统中生效。
