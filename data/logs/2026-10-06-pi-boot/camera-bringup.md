# Camera Module 3 → Pi HDMI → USB capture bring-up

日期：2026-10-06。目标为相机直连电脑采集；PYNQ 接入另验。

## 初始诊断（后续进展见末尾）

- 用户确认相机 CSI 排线已接好，SD 卡已装回启动，能 SSH 登录。
- 用户终端 `/etc/os-release`：Raspbian GNU/Linux 13 (trixie)，13.6。
- 用户运行 `rpicam-hello --list-cameras` 的原始输出：

```text
Could not open any dmaHeap device
No cameras available!
```

这只能确认当前账号下枚举失败；权限、设备节点、驱动及排线原因未确定。
尚未验证相机预览、HDMI 相机输出或真实相机采集闭环。

## 本机只读复测

Windows PnP 显示 USB Video（VID_345F/PID_2109）状态 OK。
同时存在 ASUS IR camera 和 ASUS FHD webcam；DirectShow 索引不能仅按历史认定。

仓库现有入口（项目根目录 PowerShell）：

```powershell
sim/build/vision-client/dist/vision_preview/vision_preview.exe --source 1 --frames 12 --headless --save data/logs/2026-10-06-pi-boot/camera-check-preview.png
sim/build/vision-client/dist/vision_preview/vision_preview.exe --source 0 --frames 12 --headless --save data/logs/2026-10-06-pi-boot/camera-check-source0.png
```

索引 1 返回退出码 1，原始错误 `RuntimeError: UVC frame unavailable`。
索引 0 返回退出码 0，保存 640×480 黑色画面（带程序横幅）。
索引 0 的设备身份未确定，不能据此声称采集卡收到 Pi 信号。
SSH 探测在连接阶段返回 `port 22: Permission denied`；用户已能登录，
不能将工具执行环境的连接拒绝当成树莓派登录故障。

## 下一诊断入口（树莓派 SSH）

```bash
id
ls -l /dev/dma_heap/ /dev/video* /dev/media*
sudo rpicam-hello --list-cameras
grep -nE '^[[:space:]]*(\[|camera_auto_detect|dtoverlay|start_x|gpu_mem)' /boot/firmware/config.txt
sudo dmesg | grep -iE 'imx708|unicam|csi|camera|dma.heap' | tail -n 50
```

以下补记用户回传结果；本轮未改树莓派系统配置、未改代码、未提交。
不涉及 RTL，未运行 RTL 回归，不将本次设备检查称为 RTL PASS。

依据：[官方相机软件文档](https://www.raspberrypi.com/documentation/computers/camera_software.html)、
[官方 DMA heap 打开逻辑](https://github.com/raspberrypi/rpicam-apps/blob/main/core/dma_heaps.cpp)。

## 实机进展：直连相机画面已出现

用户回传 `id`：`uid=1000(edgesight) gid=1000(edgesight) groups=1000(edgesight),27(sudo)`。
DMA heap 字符设备权限为 `crw-rw---- root video`，账号不在 video 组。
`vidbuf_cached -> linux,cma` 存在；sudo 枚举成功，普通账号的权限缺口已定位。

`sudo rpicam-hello --list-cameras` 原始关键输出：

```text
sudo: unable to resolve host edgesight-pi: Temporary failure in name resolution
Available cameras
-----------------
0 : imx708 [4608x2592 10-bit RGGB] (/base/soc/i2c0mux/i2c@1/imx708@1a)
```

相机预览复现入口（树莓派 SSH，电脑采集软件选择 USB Video）：

```bash
sudo rpicam-hello --timeout 0 --fullscreen --viewfinder-width 1280 --viewfinder-height 720
```

用户在上述指导后确认「有了有了」：电脑端已出现相机画面。
结论依据用户实机观察，agent 尚未取得相机画面截图或连续录像；不是自动化 PASS。
按 Ctrl+C 停止预览；尚未配置开机自动运行。
待验证：HDMI 实际输出分辨率/刷新率、长时间稳定性、真实相机经 PYNQ 的链路。
待处理：普通账号 video 组权限、sudo 主机名解析警告。
预览尺寸 1280×720 不等于 HDMI 输出已经锁定 720p60。

## 720p60 配置前核对

用户回传的完整原始输出已保存到 `display-config-before.txt`。
`kmsprint -m` 显示 HDMI-A-1 connected，支持 1280×720@60.00，
像素时钟 74.250 MHz，水平 1280/110/40/220、垂直 720/5/5/20。
该输出是支持模式列表，不用首行 P|D 推断当前实际扫描输出。
config.txt 使用 `dtoverlay=vc4-kms-v3d`、`disable_fw_kms_setup=1`；
末尾已有旧式 hdmi_group=1 / hdmi_mode=4，但 cmdline.txt 无 video= 参数。
拟在保留原有 root PARTUUID 等参数、整行不拆开的前提下追加
`video=HDMI-A-1:1280x720@60D`，原文件先备份。
改动尚待用户在树莓派执行；重启后用 `sudo kmsprint` 核对实际模式。
配置写入和重启复验未完成，不将其计为已锁定 720p60。

## 720p60 实际运行模式确认

上述待验证项已有后续输出：用户按配置指导回传 `sudo kmsprint`，
原始结果保存在 `display-mode-after.txt`。
HDMI-A-1 connected，实际 CRTC 为 `1280x720@60.00 74.250`；
水平 1280/110/40/220、垂直 720/5/5/20，符合标准 720p60。
HDMI-A-2 disconnected。结论：本次实际 HDMI 输出模式已确认。
sudo 主机名解析警告仍存在，但未阻止显示模式查询。
尚待复测：在该输出模式下重新启动相机，确认电脑采集画面和长时间稳定性。
未实现/未接入：开机自动预览、真实相机经 PYNQ 的链路。

## 720p60 相机复测异常

用户随后提供异常截图，已复制保存为 `camera-720p-corruption.png`，
不以剪贴板临时路径作为仓库证据。
可见上半部分黑屏、下半部分灰色重复花纹，尚无正常可辨识相机图像。
不能以 HDMI 时序正确代替相机画面正常或稳定性验收。
待对照：Ctrl+C 停止相机预览后，关闭并重新打开电脑 USB Video 采集窗口，
观察 Linux 终端/登录画面是否恢复正常；同时确认实际采集软件名称。
具体原因未确定，本轮未调整系统配置或相机参数。

## 720p60 相机画面恢复与权限步骤

用户在停止预览、重开采集窗口的对照指导后表示「这里可以正常显示了」，
进一步指导重新启动相机并区分终端文字/实时画面后，用户确认「正常，可以继续」。
当前结论：用户确认 720p60 下相机画面正常；无新的截图或长时间录像。
此前花屏根因未确定，不将重新打开窗口写成已经证明根因或彻底修复。
下一步只补已知的 video 组权限：`sudo usermod -aG video edgesight`。
`-a` 保留现有附加组（含 sudo）；退出 SSH 并重新登录后执行 `id`，
再运行不带 sudo 的相同相机预览命令验证。
账号组修改及普通账号预览尚待用户执行，不计为已完成。
若出现其他设备访问错误，根据实际设备节点和组信息进一步诊断。
开机自动预览、真实相机经 PYNQ 的链路仍未实现/未接入。

## 权限会话更新与自动启动准备

用户执行 usermod 后，在旧 SSH 会话里的 id 仍只有 edgesight、sudo，
普通账号预览报 DMA heap、/dev/media0–4 权限拒绝及 DRM preview 不可用。
指导退出并重新 SSH 登录后，用户回复「完成」。
仅记录操作完成的口头反馈；新会话 id 和不带 sudo 的画面结果尚待回传。
自动启动准备分两步：
1. 待确认后创建 sim/scripts/pi-camera-preview.service（约 20 行）；
   普通账号运行现有预览命令，Pi 上 systemd-analyze verify 并手动启动实测。
2. 第一步理解确认后启用开机启动，重启核对服务、720p60 和电脑相机画面。
当前请求 id、相机程序绝对路径、默认启动目标及 display-manager 状态，
以核对用户权限、ExecStart 路径及桌面占用 DRM 的可能性。
本轮仅更新记录；服务配置尚未实现，未安装或启用自动启动。

## 自动启动环境核对输出

用户回传原始结果：

```text
uid=1000(edgesight) gid=1000(edgesight) groups=1000(edgesight),27(sudo),44(video)
/usr/bin/rpicam-hello
multi-user.target
inactive
```

分别对应 id、command -v rpicam-hello、systemctl get-default、
systemctl is-active display-manager。新会话 video 组已生效，sudo 组保留。
程序绝对路径已确认，显示管理器当前 inactive，默认启动目标为 multi-user。
本次回传未明确回答不带 sudo 的预览画面结果，也未回答两步方案确认问题。
自动启动服务仍未实现；等待既有方案确认，不将未答复视为同意。

## 服务第 1 步：已创建，待实机复验

用户明确回复「正常，按方案继续」，确认普通账号预览和两步方案。
创建 sim/scripts/pi-camera-preview.service（18 行）及 docs/pi-camera-preview-runbook.md。
以 edgesight/video 运行既有命令，异常 5 秒重试，SIGINT 停止，日志进 journal。
Windows 未列出可用 WSL，不能本机执行 systemd-analyze verify。
安装、语法、运行状态、电脑画面和 SSH 断开后继续运行均待 Pi 实测回传。
本步未 enable，开机启动尚未接入/验证；未提交，理解题待回答。

## 服务首次安装与启动输出

用户回传结果已保存到 service-first-start.txt：systemd-analyze verify 退出码 0，
安装、daemon-reload、start 后服务 active/running，Main PID 1152，实际 argv 与源配置一致。
该状态采于启动后 33ms，不能代替相机初始化、持续运行和电脑画面验证。
Loaded 显示 disabled（preset: enabled 是预置策略，不等于已启用）。
待核对 User、NRestarts、ExecMainStatus、初始化日志及持续相机画面。
开机 enable 和重启复验仍未执行，理解题仍待回答，不提交。

## 服务手动运行状态核对

用户回传状态及日志已保存到 service-manual-check.txt：User=edgesight、
ActiveState=active、SubState=running、NRestarts=0、ExecMainStatus=0。
日志确认 IMX708 注册、DRM 预览窗口创建，预览配置 1280×720 YUV420，
传感器 RAW 模式为 1536×864（与预览/HDMI 输出尺寸口径不同）。
状态和初始化配置检查通过；此次回传未明确确认电脑画面，不替代视觉实测。
画面确认及理解题仍待回复；第 2 步 enable/重启复验未执行。

## 第 1 步收口，第 2 步待实机执行

用户明确确认服务下画面正常，并回答相机占用及 start/enable 区别，两题通过。
完整答案和判定见 report/llm_log/2026-10-06-pi-camera-service.md。
手动服务复验已完成；后续入口见 docs/pi-camera-preview-runbook.md 第 2 步。
计划执行 enable → reboot → 不手动 start，仅查询新 boot 状态、HDMI 和日志并观察画面。
启用结果、重启后自动运行和画面尚待回传，不将其记为开机已验证；未提交。

## 重启后的服务与 HDMI 复验

回传原始输出保存到 service-after-reboot.txt：enabled、active/running、
User=edgesight、NRestarts=0、ExecMainStatus=0，rpicam PID 642。
本次 boot 日志在约 12 秒时注册 CM3、创建 DRM 预览并配置 1280×720 YUV420。
kmsprint 为标准 720p60/74.250 MHz，同时显示 1280×720 YU12 相机平面。
后台自启与 HDMI 配置检查通过；电脑端重启后自动画面仍待用户确认。
真实相机经 PYNQ 尚未接通；未提交。

## 收口：直连链路及重启自动预览通过

针对「本次重启后，没有手动启动相机，电脑端是否自动恢复正常实时画面」，
用户原文回复「自动回复了」，结合上下文确认画面自动恢复。
结论：CM3 → Pi HDMI → USB 采集卡 → 电脑已通，HDMI 标准 720p60，
普通账号预览及 systemd 手动启动通过，enabled 后本次重启自动预览通过。
证据由仓库服务文件、操作入口、用户回传原始终端输出和画面确认组成。
未取得本次正常画面录像；不声称长时间或冷上电稳定性已测。
未接入：真实相机经 PYNQ 路径；待处理：sudo 主机名警告及 Pi 时钟校准。
本轮仅文档收尾，未改服务文件或实机配置；未提交。
