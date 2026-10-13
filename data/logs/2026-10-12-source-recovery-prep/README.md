# N02：采集卡连接时 Pi 软件重启断源/恢复（2026-10-12）

基线 `dev/model@3e2e1c9`；临时测试，不冻结距离、光照或背景。拓扑沿用本次连接记录：电脑以太网直连 Pi，PYNQ 用 COM12，Pi HDMI 经 PYNQ 输出到 USB Video。采集卡和 HDMI 保持连接。

## 前置与用户操作

- [pi-ssh-probe.txt](pi-ssh-probe.txt)：`ssh -o BatchMode=yes -o StrictHostKeyChecking=yes -o ConnectTimeout=5 edgesight@192.168.50.2 <只读命令>`，主机 SSH 可达，免交互认证失败，退出 255。
- 用户随后确认在自己的 PowerShell 私密登录 Pi，等待监视开始；未把密码交给代理或日志。未修改 SSH/网络配置。
- [board-before.txt](board-before.txt)：PYNQ boot_id=`2d61ca6a-03dc-4628-88e3-1203ac8b0e3c`；原 `/home/xilinx/vision_m2/vision.bit`，IP=`pipe,ps7`；sudo 可用，退出 0。
- 代理启动监视并从日志确认 `0.0s VIDEO_OK cfg=2` 后，提示用户在 **Pi** 执行 `sudo reboot`。用户回复“已执行树莓派 sudo reboot”；未要求拔线或断开采集卡。
- Pi 新 boot_id、服务日志和实际 HDMI 时序未由本轮代理读取；执行动作依用户回报，恢复现象依据下列 PYNQ/UVC 原始记录。

## 仓库入口与原始转换

`sim/scripts/pynq_serial_command.ps1 -Port COM12 -TimeoutSeconds 275` 在板端加载 XRT/PYNQ 环境，运行 `timeout -k 5s 255s python3 -u /home/xilinx/vision_m2/watch_video.py 240`，并记录前后 boot_id。完整命令见 [reboot-watch.txt](reboot-watch.txt)。监视器版本沿用 [前次哈希与源码记录](../2026-10-12-n02-extended/preflight.txt)。

| 相对时间 | 原始状态 |
| ---: | --- |
| 0.0s | VIDEO_OK cfg=2 |
| 98.7s | NO_VIDEO |
| 99.7s | BUSY |
| 108.2s | VIDEO_OK cfg=240 |
| 121.5s | NO_VIDEO |
| 122.5s | VIDEO_OK cfg=273 |
| 240.4s | watch done |

退出 0，前后 boot_id 一致，PYNQ 没有重启。没有重新加载位流或人工启动 Pi 相机服务。保留两次断源转换，不以首次 VIDEO_OK 宣称连续稳定恢复；最后恢复后约 117.9 秒未再记录异常。
这些时间为间歇 commit 探测的相对时间，不是 Pi 重启时长或精确 HDMI 电气断源时长。第二次短断源原因未查明，不能凭推断归因于相机服务或 DRM。

## 恢复画面与结束检查

- `python sim/scripts/capture_uvc_raw.py --output-dir <仓库内新目录> --frames 24`：[uvc-return-console.txt](uvc-return-console.txt) PASS，退出 0，USB Video index=1、1280×720×3 uint8 BGR、PNG 回读像素一致。
- [raw.png](uvc-after-source-return/raw.png) 已目视检查：木纹背景和新摆放的紧固件，有真实非均匀画面；与旧四件软件诊断输入不同，不混用计数或帧身份。PNG SHA256=`06a735c040fbe6bf25311da40e58455b4c64438723515747dd01332b29a69e6e`。
- [board-after-smoke.txt](board-after-smoke.txt) 退出 0：boot_id 和原 bit/hwh 哈希未变，实际运行原 vision；`busy=False, applied_config_id=556`，smoke PASS。结束释放 COM12。

## 本例结论与缺口

本轮确认采集卡连接时，用户发起的 Pi 软件重启产生可观察断源，原 vision 随后自行恢复视频应答；观察窗口内 PYNQ 未重启，真实 UVC 画面恢复。它补充了历史“采集卡 HDMI 断开”条件下的软件重启结果。
不证明物理 HDMI 拔插问题已修复，不代签完整 N02、冷启动、长时间寿命或完整 N03。冷启动、物理拔插、第二次短断源原因仍待验证。
未实现/未接入：安全 custom DDR 所有权、CNN RTL、核工业固件和真实 LIVE 闭环。

仅新增日志/说明，无代码修改、提交或推送。Git 工作区和暂存检查原始输出及退出值见 `diff-check.*`、`staged-diff-check.*`。
