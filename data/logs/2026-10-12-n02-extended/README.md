# N02 原 vision 分段观察与重载（2026-10-12）

基线 `dev/model@3e2e1c9`，保留原有工作区和暂存改动。本步无 RTL/脚本源码修改、提交或推送；用户授权继续板端检查。

## 配置与边界

- 拓扑沿用 [本次连接记录](../2026-10-12-board-connect/README.md)：电脑以太网连树莓派，PYNQ 控制用 COM12；USB Video 采集卡保持连接。
- boot_id：`2d61ca6a-03dc-4628-88e3-1203ac8b0e3c`；本轮各段与重载前后均一致。
- 原 vision.bit SHA256：`4f0c491a6383d8a11f87cd2de260027f519dbd466942d0b1b6e36198e39d5be5`。
- 原 vision.hwh SHA256：`c0adfd3656c2fdb0468de356dc8232857580286d48977c41d6ee61edc3b7b5a5`。
- watch_video.py SHA256：`6aa40e6762d8304299397ad6e0d6f52dee5fbe12abfa5fb7c3790826e22585ef`；原文、板端依赖哈希和 sudo 预检见 [preflight.txt](preflight.txt)，主机入口哈希见 [host-script-hashes.txt](host-script-hashes.txt)。

## 可复现入口与原始结果

板端命令均通过 `sim/scripts/pynq_serial_command.ps1 -Port COM12 -Command <命令> -LogPath <仓库内新日志> -TimeoutSeconds 275` 执行，加载 XRT/PYNQ 环境后运行 `timeout -k 5s 255s python3 -u /home/xilinx/vision_m2/watch_video.py 240`。完整命令和 UTC 时间保存在每段日志中。

| 原始证据 | 时长 | 初始配置号 | 结果 |
| --- | ---: | ---: | --- |
| [watch-01.txt](watch-01.txt) | 240.1s | 2 | VIDEO_OK；退出 0 |
| [watch-02.txt](watch-02.txt) | 240.1s | 578 | VIDEO_OK；退出 0，前后 boot_id 相同 |
| [watch-03.txt](watch-03.txt) | 240.1s | 1154 | VIDEO_OK；退出 0，前后 boot_id 相同 |

三段相邻执行，探测时间累计 720.3 秒，段间有脚本启动间隔，不能表述为无间断逐帧检查。监视器每次 commit 超时 0.6 秒、间隔休眠 0.4 秒，仅在状态转换时打印；三段均未记录 NO_VIDEO/BUSY。其退出 0 本身不证明状态正常，已另核对状态行和完成时长，见 [watch-audit.txt](watch-audit.txt)。

每段前期/后期均运行 `python sim/scripts/capture_uvc_raw.py --output-dir <仓库内新目录> --frames 24`。`uvc-01`、`uvc-01-later`、`uvc-02`、`uvc-02-later`、`uvc-03`、`uvc-03-later` 六次均 PASS：USB Video index=1，24 帧，1280×720×3 uint8 BGR，每次保存一张 PNG 并验证回读像素一致。各自 console、exit、metadata.json 和 raw.png 保留在本目录；没有保存全部 144 张读入帧。

六张 PNG 均已目视核对，包含灯具、木纹/蓝色平面和镜头移动近景。输入场景发生变化，未核对 Pi 源帧率/曝光，也未做色卡、动态图案与无混帧对拍。UVC 模式报告帧率不能作为 HDMI IN 或相机实测帧率。

## Overlay 重载与结束状态

- [reload-smoke.txt](reload-smoke.txt)：运行原 `m2_onboard.py load`，等待 5 秒后 `smoke`；load/smoke 均 PASS，`pipe @ 0x40000000`，`busy=False, applied_config_id=1`，退出 0，boot_id 不变。
- [重载后画面](uvc-after-reload/raw.png)：再读 24 帧，PNG 回读一致，已目视为木桌上的紧固件；[console](uvc-after-reload-console.txt) 退出 0。没有尺标/确认距离，不能作正式定标样本。
- [final-state.txt](final-state.txt)：位流哈希未变，实际路径 `/home/xilinx/vision_m2/vision.bit`，IP 为 `pipe,ps7`，退出 0；串口已释放。后续 N03 base 单独记录，不混用此结束状态。

## 判定与待办

本轮分段视频应答观察、间隔 UVC 采集和一次 Overlay 重载复验通过。仅为有界检查，不签长时间寿命验收或完整 N02。
冷启动、软件断源恢复、物理拔插及既往异常重启复验本轮未测；N03 完整颜色/动态无混帧/长期共存、N04/N05 定标和正式数据仍未完成。安全 custom DDR、CNN、核工业固件和真实 LIVE 闭环仍未实现/未接入。旧 vision 构建仍缺完整源码锚点。

Git 工作区/暂存差异检查原始输出和退出值保存为 `diff-check.*`、`staged-diff-check.*`。
