# 上板 N01：现场版本与连接盘点

日期：2026-10-10（Asia/Shanghai）；本地基线：dev/model @ c292038。
状态：盘点、现有视频位流加载/烟测与归档 XSA 字节对应已完成；PYNQ 网口未直连电脑、构建时源码快照仍未闭环，N02/N03继续。
用户负责全部实机工作，本轮通过用户电脑 COM12 操作 PYNQ；仅在加载后核对 `pipe @ 0x40000000` 才访问该已知寄存器段。

## 已取得的现场事实

| 项 | 实测值/证据 |
| --- | --- |
| 串口 | COM12，115200、8N1、无流控；收到 xilinx@pynq shell；system.txt |
| 系统 | Linux 6.6.10-xilinx-v2024.1，armv7l；baseline/system.txt |
| 用户 | xilinx，属于 sudo/video/render 组；baseline/identity.txt |
| 镜像 | PynqLinux 3.0，基于 Ubuntu 22.04；baseline/os.txt |
| Python/PYNQ包 | Python 3.10.4、PYNQ 3.1；environment-user.txt |
| 板卡网络 | eth0 UP，169.254.87.99/16、192.168.2.99/24；baseline/network.txt |
| 电脑设备 | USB Serial Port COM12、USB Video VID_345F/PID_2109 均枚举OK；host-devices.json |
| 电脑网络 | 初查有线断开；后查以太网上线且为192.168.50.1/24；host-adapters.json记录后查枚举 |
| 已加载位流元数据 | PL.bitfile_name=None、PL.timestamp=None；IP表为base类条目，非预期vision；loaded-user.txt |
| 认证 | 用户在应用内终端完成隐藏输入；sudo-check.txt 的 `sudo -n true` 退出0；不保存密码 |
| 板端服务 | jupyter.service active/running，监听0.0.0.0:9090；network-services.txt |

最后一项只是 PYNQ 元数据查询，不能证明 FPGA 已加载 base.bit，也不能证明自定义 vision 正在运行。
USB Video 枚举存在不能证明 HDMI 画面、720p模式或 PS 取图成功。
本地 Python 的 pyserial 不可用，串口入口改用 Windows 内置 System.IO.Ports；无需安装依赖。

## 位流/脚本指纹

板端原始 SHA256：baseline/artifacts.txt；本地对照：local-sha256.csv。

- 板端 vision.bit：`4f0c491a6383d8a11f87cd2de260027f519dbd466942d0b1b6e36198e39d5be5`。
- 板端 vision.hwh：`c0adfd3656c2fdb0468de356dc8232857580286d48977c41d6ee61edc3b7b5a5`。
- 当前 `dev/model` 工作树 `hdmi-project` 的 bit/hwh：`38f24077...` / `66f8544e...`，与板端不同；这是当前目录的旧构建产物，不能代表其他工作树。
- 当前工作树 `board_pkg_diagnostic` 的 bit/hwh：`e90ddde2...` / `acdec618...`，也与板端不同。
- 另一工作树 10 月 3 日修复后 `vision.xsa` 中的 bit/hwh 与板端 **逐字节 SHA256 完全相等**；已将 499890 字节 XSA 归档至 `data/evidence/2026-10-10-onboard-bit-provenance/`，其中有可复现命令和完整哈希。
- 板端 m2_onboard.py、vision_regs.py 与本地当前文件 SHA256 一致。

因此板端部署文件对应 10 月 3 日修复后 XSA 的事实已闭环；构建时完整源码快照仍缺摘要，且字节对应不能替代本次热插拔验收。此次异常重启不能归因于“仍加载修复前位流”。

## 复现入口与原始失败

```powershell
# 只读盘点：必须使用新的仓库内输出目录。
.\sim\scripts\run_pynq_baseline.ps1 -Port COM12 -OutputDirectory "$PWD\data\logs\<new-run>"

# 用户在应用内PowerShell交互认证；密码不写入命令、聊天或日志。
powershell -NoProfile -ExecutionPolicy Bypass -File .\sim\scripts\pynq_serial_auth.ps1
```

首次基线 environment 步使用 sudo -n，返回 password required、退出1；保留 baseline/environment.txt 和 baseline.exit.txt。
随后用普通用户执行同一个 env 查询，退出0并记录 environment-user.txt；只读盘点入口已移除不必要的 sudo。
首次loaded查询保存完整原始IP字典；后续入口只显示IP名以减少串口输出，不覆盖原记录。
SSH对历史169.254.87.99的短时连接失败；当前电脑与板端IPv4网段不同。用户确认电脑网线直连树莓派，PYNQ网口无到电脑的可用路由，故Jupyter仅确认服务运行，未验证浏览器访问。

用户首次在 Windows PowerShell 5.1 执行认证入口时，`Add-Type -AssemblyName System.IO.Ports` 报 `ASSEMBLY_NOT_FOUND`，未进入串口认证。
原因是 .NET Framework 已包含 SerialPort 类型，而 PowerShell 7 使用独立程序集；两个串口入口现改为仅在类型不存在时加载程序集。
修复后使用 `C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe` 执行仓库串口入口和 `uname -a`，实机退出0；原始记录为 system-winps51.txt。
该结果验证 Windows PowerShell 5.1 的串口类型与命令传输兼容性；随后用户完成隐藏输入认证，`sudo-check.txt` 证明后续无交互调用可用。

## 本轮已执行的实机功能

- `baseline-ps51/` 八项只读查询均取得远端退出0，入口最终打印 `PASS: baseline queries complete`；其中 `PL` 初始元数据没有自定义位流。
- `sudo-check.txt` 证明串口提权缓存可用。`fpga-preload.txt` 中 FPGA 管理器为 `operating`；固件节点读取被拒，且该步的 `|| true` 吞掉子项错误，所以不能据此证明此前配置身份。
- `load-board-bit.txt`：板端指纹为上表的 `vision.bit/hwh` 加载成功，`pipe @ 0x40000000 range 0x10000`，远端退出0。
- `smoke-board-bit.txt`：R11空闲，R12由0到1，帧首提交确认，远端退出0。
- `watch-video-source.txt` 保存板端既有 `watch_video.py` 全文和 SHA256 `6aa40e67...`；`watch-60s.txt` 记录 `0.0s VIDEO_OK cfg=2`、`60.4s watch done`，无 `NO_VIDEO/BUSY` 行，远端退出0。这是60秒持续提交观察，不等于长时间寿命试验或断线恢复。
- `reload-board-bit.txt`、`smoke-after-reload.txt`：同一文件重载与帧首提交再次退出0。`loaded-after-reload.txt` 中 `PL.bitfile_name=/home/xilinx/vision_m2/vision.bit`、IP名 `pipe/ps7`；对应源码构建版本仍缺哈希闭环。
- Windows PowerShell 5.1 运行 `sim/scripts/list_dshow_video.ps1`：`0 ASUS FHD webcam`、`1 USB Video`、`2 OBS Virtual Camera`。`capture_uvc_raw.py` 只打开索引1；第一次先设FourCC后设尺寸，驱动回报 `YUY2`，第二次最后设FourCC，驱动回报 `MJPG`。
- `uvc-capture-2/`：24帧均可读，实际 BGR数组 `720×1280×3 uint8`，驱动报告 MJPG/30，读取循环0.921秒（26.06次/秒，含首帧162.744毫秒；非长期精确帧率）。`raw.png` 无叠框，解码像素与保存前逐像素一致，PNG SHA256 `7f00c900234214eda58be3586cca4b106a13b39148eab0104d25f0018fdb898b`。
- `uvc-after-reload/`：重载后USB采集卡再读24帧成功，PNG SHA256 `f39d0c3799cb9f42a1e35c4cb4bdf9a246c1f9dd114d91b6bab893814023022f`；两张画面均呈相机拍摄的室内天花板，工位尚未对准紧固件。

以上UVC画面来自采集卡，未与板端一次 `capture_id` 绑定，不能算PS端原分辨率取帧或真实检查结果。

## 尚待执行

- [x] 串口sudo认证、当前板端 vision 位流加载/帧首烟测、60秒观察、重载复验。
- [x] Windows USB Video 设备名/索引、MJPG请求与驱动回报、24帧UVC抓图及无损PNG。
- [ ] 位流源码/构建/部署对应；没有以哈希证明板端Sept21位流与当前本地构建相同。
- [ ] N02冷启动已完成一次、静态输入已观察240秒、Pi软件重启断源/恢复已在采集卡断开条件下通过；物理HDMI IN拔插仍失败，长时间寿命未验收。
- [ ] N03原分辨率PS端BGR完整帧取图与同一capture关联；当前自定义bit无此路径。
- [ ] 电脑与PYNQ网口、Jupyter浏览器访问；当前电脑以太网直连树莓派。
- [ ] CNN/核集成/LIVE闭环未实现；正式数据、权重和精度仍未验收。

新串口执行器的成功标准是本次命令唯一标记及远端退出码，不只看PASS文本。
超时保留现场并返回124，不自动发Ctrl+C；日志已存在时拒绝覆盖。

## N02：HDMI IN断源/重连失败现场

用户确认可操作线材后，运行板端现有 `watch_video.py 180`，再由用户只拔HDMI IN约10秒后插回。
`watch-unplug-180s.txt` 原始串口输出：`0.0s VIDEO_OK cfg=2` → `72.1s NO_VIDEO` → `73.1s BUSY` → 完整U-Boot/Linux启动日志。
原Shell的唯一完成标记没有出现，串口执行器超时退出124；绝不能把监视脚本在新Shell后的串口提示当作通过。
重连后的 `uvc-after-replug/raw.png` 和延迟复测 `uvc-after-replug-delay/raw.png` 哈希同为 `08f1c9de...`，画面近乎恒定黑色（像素6–8），因此输出画面未恢复。
`after-unplug-boot.txt` 显示重启后uptime约2分钟、boot_id改变且 `last -x` 把上次串口会话标为 `crash`；板卡时钟回退至9月21日，不能用其墙上时间推断事件先后。
`loaded-after-boot.txt` 显示 `PL.bitfile_name=None`；`sudo-after-reboot.txt` 返回 `sudo: a password is required`。
`previous-boot-journal.txt` 的 `journalctl -b -1` 只看到较早DHCP记录，未提供本次重启的直接原因；目前不能判定由拔线、电源扰动、watchdog或内核/RTL故障中的哪一个触发。
用户回忆拔插期间电源灯一直亮，未碰电源线/复位键。`restart-clues.txt` 只显示板卡注册了10秒超时的watchdog，未留下其触发记录或pstore崩溃档案；不能因此断言watchdog就是重启原因。

用户再次在终端隐藏输入认证，`sudo-restored.txt` 退出0；`sha-after-boot.txt` 证实bit/hwh哈希不变。
`load-after-boot.txt` 与 `smoke-after-boot.txt` 依次退出0，帧首提交再次由R12确认。
`uvc-recovered/raw.png` 重新出现室内实景，PNG SHA256 `e60f41f311ffc2f388c3be64c04c1d5c945eb681d961688d45f984174a763e13`。
`watch-after-recovery-60s.txt` 再次记录 `0.0s VIDEO_OK cfg=2`、`60.4s watch done`，期间无 `NO_VIDEO/BUSY`，远端退出0；只证明恢复后短时稳定。
因此**同一位流重载可恢复板端寄存器/帧首与USB可视画面**；断源自动恢复未通过，不能把人工重载后的恢复算作热插拔通过。

### 关机后指示灯亮：人工隔离观察

用户另报告：J9 置 REG，SW1 置 OFF 且拔掉12V适配器后，DONE 与红色 CR8 指示灯仍持续亮超过30秒；当时 HDMI IN 接树莓派，HDMI OUT 接 USB 采集卡，COM12 Micro-USB 接电脑。用户随后拔掉 COM12 Micro-USB，报告两灯仍亮；拔掉采集卡的电脑端 USB 后，也曾报告两灯仍亮。最后用户从 PYNQ HDMI OUT 拔下通往采集卡的 HDMI 线，报告两灯熄灭；**最后一步时采集卡 USB 接电脑**。这是用户人工观察，不是电压测量；几次操作的接线条件并非完全相同，不能合并为一次受控实验。

因此目前只确认在最后所述接线条件下，断开 HDMI OUT—采集卡连接后两灯熄灭；无法断定是采集卡 USB、HDMI IN、HDMI OUT 端口还是其他路径向板卡供电。厂家[参考手册](https://www.paltek.co.jp/dcms_media/other/pynqz2_user_manual_v1_0.pdf)说明 J9 选 USB/REG；[原理图](https://dpoauwgwqsy2x.cloudfront.net/Download/TUL_PYNQ_Schematic_R12.pdf)显示 CR8 接在 VCC3V3 与 PG_ALL 控制路径上，HDMI IN 的 5V 接在热插拔/DDC 电路。仅凭 LED 不能确认主电源轨电压、电流或板卡可正常运行。排查期间保持 HDMI OUT 至采集卡断开，暂不重复带电热插拔验收。

用户随后保持 HDMI OUT—采集卡 HDMI 断开、HDMI IN 接树莓派，接回12V与COM12 Micro-USB并将SW1置ON。受限终端两次打开COM12失败（`coldboot-no-capture-system*.txt`），`mode COM12` 报设备不可用；在系统终端使用同一仓库串口脚本成功，故前两次失败不计为板卡故障。`coldboot-no-capture-system-host.txt` 记录新 boot_id `46548310-bd10-4806-8c89-f92c2b7ce209`、远端退出0。PYNQ 位流元数据初始为 `None`（`coldboot-no-capture-loaded.txt`）；`sudo -n` 退出0。加载同一板端 `vision.bit`（`coldboot-no-capture-load.txt`）与帧首烟测（`coldboot-no-capture-smoke.txt`）均退出0。

`coldboot-no-capture-watch-60s.txt` 记录 `0.0s VIDEO_OK cfg=2`、`60.4s watch done`，没有 `NO_VIDEO/BUSY` 或重启输出，远端与串口执行器均退出0。结束后 `coldboot-no-capture-after-watch.txt` 的 boot_id 未变。`no-capture-watch-240s.txt` 又记录 `0.0s VIDEO_OK cfg=147`、`240.4s watch done`，无其它状态行，远端退出0。这是采集卡 HDMI 断开时的静态输入观察，不等于长时间寿命验收。

### Pi 软件重启断源/恢复：采集卡 HDMI 断开

电脑直连 Pi 的旧 IPv6 地址不可达、`edgesight-pi.local` 未解析；IPv4 `192.168.50.2` 的邻居 MAC 为此前记录的 Pi `D8-3A-DD-F2-9A-D4`。`pi-ssh-ipv4-probe.txt` 表明主机可达但没有免交互凭据；用户在自己的终端输入密码登录，未向聊天发送密码。
为同步确认监视已启动，`sim/scripts/pynq_serial_command.ps1` 只将日志文件打开方式改为允许并发只读；PowerShell 解析通过，实机运行中 `Get-Content` 读到 `0.0s VIDEO_OK cfg=724`。用户随后在 Pi SSH 终端执行 `sudo reboot`，不拔线、不连接采集卡 HDMI。`pi-reboot-no-capture-watch-180s.txt` 原始状态为 `0.0s VIDEO_OK cfg=724` → `39.2s NO_VIDEO` → `40.2s BUSY` → `51.8s VIDEO_OK cfg=819` → `180.2s watch done`；远端与串口执行器均退出0。`pi-reboot-no-capture-after.txt` boot_id 仍为 `46548310-bd10-4806-8c89-f92c2b7ce209`，FPGA 管理器为 `operating`。

因此仅能判定**采集卡 HDMI 断开、Pi 正常软件重启**时，输入监视恢复且 PYNQ 未重启。上次失败同时包含物理 HDMI IN 拔插和采集卡 HDMI 接入两个不同变量；本次不能证明其中哪个导致异常，也不能代替采集卡画面与完整 N02 验收。
