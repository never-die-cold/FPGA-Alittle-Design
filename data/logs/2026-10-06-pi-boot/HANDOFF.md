# 树莓派诊断上下文交接

日期：2026-10-06（Asia/Shanghai）。最新状态以本节和 camera-bringup.md 收口记录为准。

## 最新状态：相机直连与重启自动预览已通过

- 用户能以 edgesight SSH 登录；id 已确认 sudo、video 附加组生效。
- 实机 Raspbian GNU/Linux 13 (trixie)，相机 IMX708，程序 /usr/bin/rpicam-hello。
- 默认 multi-user.target，display-manager inactive；普通账号无需 sudo 的预览正常。
- KMS HDMI-A-1 实际 1280×720@60、74.250 MHz；cmdline 使用 video= 参数，
  不能以 config.txt 的旧 hdmi_group/hdmi_mode 代替 KMS 实测。
- pi-camera-preview.service 以 edgesight/video 运行，语法退出码 0，已 enabled。
- 重启后 active/running、NRestarts=0，CM3/DRM 配置完成；用户确认画面自动恢复。
- 服务源文件 sim/scripts/pi-camera-preview.service，复现入口 docs/pi-camera-preview-runbook.md。
- 完整原始输出见 service-first-start.txt、service-manual-check.txt、service-after-reboot.txt。
- 理解题 2/2 通过，完整记录 report/llm_log/2026-10-06-pi-camera-service.md；未提交。
- 待验证：长时间、断电再上电、真实相机经 PYNQ；待处理 sudo 主机名解析、Pi 时钟。

以下为历史启动、网络和改密排查；当时的「尚待装回/登录」已由后续实机操作更新。

## 用户目标与当前结论

用户正在开展 FPGA-Alittle-Design 项目的树莓派相关工作，最初怀疑烧卡后树莓派没有启动，因为无法 SSH 且 ACT 绿灯熄灭。

当前已确认：

1. 树莓派已经启动到 Linux 登录界面。
2. 电脑与树莓派的 IPv6 网线直连已通。
3. 树莓派的 SSH 服务正在监听，并返回 OpenSSH 横幅。
4. 在建议关闭代理 TUN 后，同一地址的 Ping 从连接失败变为 3/3 成功，TCP 22 也成功。

尚未确认：edgesight 用户密码认证成功；IPv4 地址配置；树莓派互联网连接；重新开启 TUN 后的局域网兼容性。
不要把 SSH 端口可达写成已完成账号登录。

## 硬件和接线

- 树莓派 4B，官方外接电源。
- 用户观察：PWR 红灯常亮；ACT 上电闪过几下，之后熄灭。
- 树莓派网口与电脑 Realtek 有线网口直接连接。
- 树莓派 micro-HDMI → USB HDMI 采集卡 → 电脑。
- 采集卡：USB Video，VID_345F/PID_2109，Windows DirectShow 索引 1；本次抓到的确实是树莓派登录画面。
- microSD 已从读卡器装回树莓派，并且树莓派已上电。

## SSH 连接参数

```powershell
ssh -6 "edgesight@fe80::fa0b:cce2:4ca9:96ba%10"
```

- 树莓派 hostname：edgesight-pi（配置与屏幕一致）。
- 用户名 edgesight 来自启动分区 user-data；密码未知，交接中不包含密码或密码哈希。
- 地址 fe80::fa0b:cce2:4ca9:96ba 来自 HDMI 屏幕。
- %10 是当前电脑有线网口的接口索引，只适用于这台电脑当前的网卡编号。
- 树莓派 MAC：D8-3A-DD-F2-9A-D4。
- 当前电脑有线 IPv4：169.254.87.3/16（自动地址，不是树莓派地址）。
- 当前电脑有线 IPv6：fe80::a797:c75:65f2:90b1%10。

原始复测结果：

```text
用户 Ping：发送 3，接收 3，0% 丢包，0–1 ms。
SSH banner: SSH-2.0-OpenSSH_10.0p2 Raspbian-7+deb13u4
Windows IPv6 邻居表：Reachable
```

## 已排查事项

读卡器阶段仅进行只读检查：

- 约 32 GB 的 USB/MBR 卡，第一分区 F: bootfs/FAT32，第二分区 Linux 类型 0x83。
- 主要 Pi 4 启动文件存在。
- cmdline.txt 的 root=PARTUUID=22b1b901-02 与磁盘签名匹配。
- FAT32 有 Dirty 标记，但只读 chkdsk 报告：Windows has scanned the file system and found no problems。
- 未修复文件系统、未重刷卡、未改启动文件。
- user-data 有 #cloud-config 头、无 UTF-8 BOM，配置 hostname=edgesight-pi、用户 edgesight、ssh_pwauth=true、有效格式的 SHA512 密码哈希，以及 systemctl enable --now ssh。
- network-config 全为注释；启动分区没有固定 IP 或 Wi-Fi 配置。运行中的 Linux 网络配置未读取。
- ssh/ssh.txt 文件不存在；不能单凭这一点认定 SSH 未开启。
- userconf.txt 另有 pi 用户配置，不能据此确定运行中的 pi 账户存在。
- 原始 HDMI 画面显示：Raspbian GNU/Linux 13 edgesight-pi tty1，以及 edgesight-pi login:。
- 屏幕有多次登录提示和地址提示，部分地址提示为空；并未证明连续重启。

网络故障排查：

- 原先 hostname 查询失败；raspberrypi.local 与实际 hostname 不一致。
- 用户独立 PowerShell 的 IPv6 SSH 曾报连接阶段 Permission denied，并非密码认证失败。
- 电脑 tun0/sing-tun Tunnel 当时为 Up；用户确认开启了代理 TUN 模式，软件名称未提供。
- Codex 防火墙阻断规则仅对应 CodexSandboxOffline 用户 SID，不应直接归因于它阻断 ASUS 用户的正常 PowerShell。
- 用户 PowerShell 父进程为 explorer.exe。
- 精确 WFP 查询需要 Windows 管理员权限，本次未取得匹配过滤器，未修改安全规则。
- 在关闭代理 TUN 的排除测试后，用户 Ping 成功，agent 读取 SSH 横幅成功。
- 后续若启用代理，应单独验证局域网兼容性，不要关闭 Codex 沙箱保护规则。

## 证据与复现入口

本文件目录：E:\Projects\FPGA-Alittle-Design\data\logs\2026-10-06-pi-boot\

- README.md：诊断过程、证据边界、网络复测结果。
- hdmi-raw.png：1920×1080 的实际树莓派登录画面。
- hdmi-raw.log：原始抓帧成功输出。
- hdmi-preview.png：现有预览程序抓帧，带程序横幅。

仓库已有抓帧入口（需要已有构建产物；设备索引现场确认）：

```powershell
sim/build/vision-client/dist/vision_preview/vision_preview.exe --source 1 --frames 12 --headless --save data/logs/2026-10-06-pi-boot/hdmi-preview.png
```

源码：src/vision_client/preview.py。构建说明：src/vision_client/README.md。
仓库内已有 OpenCV 依赖：sim/build/vision-client-deps/，无需重复安装。

## 项目范围与纪律

- 工作目录 E:\Projects\FPGA-Alittle-Design。
- 当前分支 main，HEAD 01b3750；原工作区干净，本会话仅新增上述诊断目录，没有 commit。
- 接手前遵守根 AGENTS.md，阅读 docs/workflow.md，检查 git 分支、最近提交和工作区状态；写代码前核对计划与接口契约。
- 代码实现遵守 skill/gufa-programming/SKILL.md，小步 ≤100 行、理解题和用户回答门槛；未获用户理解确认不得提交代码。
- 本会话没有 RTL 或软件源码改动；git diff --check 无输出。实机状态依据采集画面和网络原始结果，不是 RTL 回归验收。
- Pi 角色和边界见 docs/pi-dev-roles.md、board/hardware.md：开发联调/跑分/mock/回放及相机 HDMI 源；不把 Pi 计算结果用于产品识别验收，不在 Pi 侧存数据集图像。
- Pi 角色文档的系统目标为 Lite 32-bit Bookworm；本次实际画面为 GNU/Linux 13，若后续工作涉及系统版本口径，应先核对实际 OS/架构并说明差异。

## 下一步

先让用户将已准备的 SD 卡装回断电的树莓派并上电；改密脚本成功后会自动重启，再完成实际 SSH 登录并只读核对 uname、/etc/os-release、hostname、网络地址和 SSH 状态。不要再次烧卡。
若需要密码，让用户在自己的终端输入；不要索要或保存明文密码。
登录后根据用户当时选择推进项目的树莓派工作，不要擅自将跑分、mock、回放全部作为本次任务。

## 密码来源补充

用户说明账号密码由 AI 设置。随后只读查询 ZCode 的本地会话记录，找到会话「SD卡烧录后通过读卡器配置SSH」（sess_629a5b80-32fa-40d2-977b-7c8ebf69bad0）。
2026-10-05 的原始工具命令及结果确认：ZCode 为 userconf.txt 中的 pi 用户生成了 14 位随机密码；明文已在本次聊天告知用户，未写入仓库。
该记录不包含 edgesight 用户的明文密码。pi 账户在实际系统中是否已创建、密码是否仍有效，尚未验证。
可由用户尝试 pi@同一IPv6地址；登录成功后再确认账户情况，按用户需要设置 edgesight 密码。

## 密码重设准备（最新）

用户要求密码等于用户名；目标为 pi/pi 和 edgesight/edgesight。
已确认 F: bootfs 的镜像标识和 root PARTUUID=22b1b901-02，与先前卡片一致。
原 cmdline.txt、user-data、userconf.txt 已备份至 F:/pi-password-reset-backup/。
已更新 user-data/userconf.txt 的密码哈希，部署 pi-password-reset.sh 和两账户哈希文件，并在 cmdline.txt 附加 systemd.run 的一次性启动参数。
脚本将在 Linux 中确保两个账号存在，以 chpasswd -e 写入密码，恢复原 cmdline.txt；成功后删除脚本和待应用哈希文件，自动重启。执行日志在启动分区 pi-password-reset.log。
语法、部署回读、两个哈希与对应用户名的一致性均检查通过；运行中账号改密和 SSH 密码登录尚未验证。
源文件：sim/scripts/pi_password_reset_once.sh、sim/scripts/prepare_pi_password_reset.py（共 90 行有效代码）；准备日志：password-reset-preparation.log。
此安装入口防止覆盖已有备份；不要直接重复运行它。失败时先读取卡上的 pi-password-reset.log，再决定修复。
本步未提交；古法编程理解题待用户回答，新代码步骤需遵守该门槛。
