# 2026-10-12 板卡连接与原 vision 短基线

- 工作分支：`dev/model`；HEAD：`3e2e1c9`。本步仅保存日志和说明，没有修改 RTL、提交或推送。
- 用户已返回，并在自己打开的 PowerShell 中完成隐藏密码认证；密码未进入聊天或本目录。
- 控制连接：PYNQ `COM12`，115200、8N1、无流控。每次串口入口结束均释放端口。
- 用户确认电脑以太网直连树莓派；电脑地址 `192.168.50.1/24`，PYNQ eth0 为 DOWN，SSH 尚未接通。未修改网络配置。
- 视频接线按用户已确认的拓扑：相机 → 树莓派 → PYNQ HDMI IN → PYNQ HDMI OUT → USB Video → 电脑。

## 仓库入口与原始结果

串口命令统一使用 `sim/scripts/pynq_serial_command.ps1 -Port COM12 -Command <板端命令>`；完整命令、主机 UTC 时间和板端返回值保存在对应 `.txt` 中。

| 检查 | 入口/原始证据 | 结果 |
| --- | --- | --- |
| 登录与身份 | [identity-network.txt](identity-network.txt) | hostname=pynq，用户 xilinx；退出 0 |
| 初次 sudo | [sudo-preflight.txt](sudo-preflight.txt) | 需要密码；退出 1，保留初次结果 |
| 用户认证后 sudo | [sudo-after-user.txt](sudo-after-user.txt) | `sudo -n true` 退出 0 |
| 板端基线 | `sim/scripts/run_pynq_baseline.ps1 -Port COM12 -OutputDirectory data/logs/2026-10-12-board-connect/baseline`；[输出](baseline-console.txt) | 退出 0；Ubuntu 22.04、Python 3.10.4、PYNQ 3.1 |
| 初始 PL/进程 | [privileged-state.txt](privileged-state.txt) | PL 路径/时间为 None，不能据此判定实际配置；整体退出 1 来自末尾 grep 未找到诊断进程 |
| 恢复原 vision | 板端 `m2_onboard.py load`；[vision-load.txt](vision-load.txt) | PASS；pipe 地址 0x40000000、范围 0x10000；退出 0 |
| 视频帧首应答 | 板端 `m2_onboard.py smoke`；[vision-smoke.txt](vision-smoke.txt) | `busy=False, applied_config_id=1`；PASS；退出 0 |
| 电脑 UVC 短采集 | `python sim/scripts/capture_uvc_raw.py --output-dir data/logs/2026-10-12-board-connect/uvc-baseline --frames 24`；[输出](uvc-console.txt) | USB Video index=1，24 帧，BGR=(720,1280,3)，PNG 回读一致；退出 0 |
| 结束状态 | [final-active-state.txt](final-active-state.txt) | `/home/xilinx/vision_m2/vision.bit`，IP=`pipe,ps7`；退出 0 |

板端 Python 命令以 `sudo -n bash -c` 加载 XRT/PYNQ 环境；load/smoke 的实际超时和完整路径见原始记录。串口认证前置条件由 `sim/scripts/pynq_serial_auth.ps1` 在本机私密输入完成。

## 身份与画面

- 开始和结束 boot_id 均为 `2d61ca6a-03dc-4628-88e3-1203ac8b0e3c`，本步没有重启板卡。
- 原 vision.bit SHA256：`4f0c491a6383d8a11f87cd2de260027f519dbd466942d0b1b6e36198e39d5be5`。
- 原 vision.hwh SHA256：`c0adfd3656c2fdb0468de356dc8232857580286d48977c41d6ee61edc3b7b5a5`。
- 板端文件哈希与环境详见 [baseline/artifacts.txt](baseline/artifacts.txt) 和 [baseline/environment.txt](baseline/environment.txt)。上述旧构建仍缺完整源码锚点，不能充当本次新构建验收。
- [raw.png](uvc-baseline/raw.png) 已目视检查：真实天花板与两条明亮灯具，非均匀黑帧；不是紧固件数据集或正式标定样本。
- PNG SHA256：`aa7d548ccabbe11c7ecf3ff769715ab1dde2b424673af3834feef77067c89c78`；设备模式与采集参数见 [metadata.json](uvc-baseline/metadata.json)。UVC 报告帧率/读取速率不代表树莓派相机或 HDMI 输入实测帧率。

## 本步边界

本次确认串口、sudo、原 vision 加载、一次帧首应答和短 UVC 采集可用；没有加载 C01 候选或启动自定义 DDR 采集。N02/N03 长时、冷启动和重连验收未完成；N04/N05 实物标定和正式数据采集未完成。安全 DDR 所有权、CNN RTL、核内工业固件及工业 LIVE 闭环仍未实现/未接入。本目录不能替代这些验收。

`git diff --check` 与 `git diff --cached --check` 的原始输出、退出值分别保存为 `diff-check.*` 与 `staged-diff-check.*`。
