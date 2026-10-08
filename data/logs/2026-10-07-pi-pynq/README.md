# 相机经 PYNQ 黑屏诊断与恢复（2026-10-07）

## 当前边界

- 前一轮已加载板端 vision.bit，smoke 配置号 0→1；用户确认电脑仍无画面。
- 本轮分支 main、HEAD 0669960；工作区原有未提交内容保留，不改 RTL 或板端文件。
- 不把前一天输入在流的证据视为本轮板卡仍运行或 HDMI OUT 正常的证明。
- 最终本轮实测：PYNQ 重启/重载后 smoke PASS，USB Video 独占采集得到真实相机画面，
  MJPG/1280×720/30fps 连续 24 帧成功；实时预览已打开，用户随后回复「ok」接受当前结果。

## 实测证据

- Windows 枚举：USB Video（VID_345F/PID_2109）和 USB Serial Port COM12 均 Status=OK。
- COM12 以 115200、8N1、无流控打开成功；连续回车未收到 UART 文本。
  见 serial-status.txt；本轮未向板卡发送装载或寄存器访问命令。
- 首次调用仓库已有 EXE：`sim/build/vision-client/dist/vision_preview/vision_preview.exe --source 1 --frames 12 --headless --save data/logs/2026-10-07-pi-pynq/capture-source1.png`。
- capture-source1.png 为 640×480 黑帧，上方文字为客户端自己绘制，不能证明 HDMI 有效。
- 索引 1 依据历史采集配置；本轮尚未完成 DirectShow 索引与设备名称的重新绑定确认。
- 独立 Python 使用现有打包 OpenCV 4.12.0 进行 MJPG/1280×720/30fps 协商：设备未打开，设置均失败，received=0。
  原输出见 capture-720p.txt；这是采集失败，不能描述为已验证 720p 黑帧。
- 同一 EXE 复查亦返回 `RuntimeError: UVC frame unavailable`，capture_exit=1。
  退出码见 capture-source1-recheck.txt；复查未生成新图像。

## 恢复过程与本轮结论

- 用户已确认采集窗口纯黑、PYNQ POWER 灯亮、采集卡接 HDMI OUT。
- 再次尝试串口 DTR/RTS 有效、无流控，发送 Ctrl+C 与回车；5 秒内 `uart_received_chars=0`。
  见 serial-interrupt.txt。不能据此证明内核挂死，仍需重启后的串口观测。
- 用户随后完成 PYNQ 重新上电；serial-after-power-cycle.txt 返回 shell，serial-reload.txt 显示 uptime 2 分钟。
- 初始化板上 XRT/PYNQ 环境并重载既有 bit：`pipe @ 0x40000000`、`PASS: load`。
- serial-smoke-after-reload.txt：R12 配置号 0→1，`PASS: smoke`，中文记录完整。
- dshow-device-map.txt：当前 DirectShow 索引 1 对应 VID_345F/PID_2109 的 USB Video，
  索引 0 为内置摄像头，索引 2 为软件设备；本轮未抓取其他摄像头。
- 重载后用户确认 USB Video 仍纯黑；此时本工具尝试抓帧仍失败，见 capture-after-reload.txt。
- 用户关闭其他采集软件后，同一 EXE 的同一设备抓帧成功，capture-exclusive-exit.txt 中 exit=0。
  capture-exclusive.png 显示天花板与灯，客户端上方横幅仅表示视频未关联识别结果。
- 独占 720p 采集：capture-exclusive-720p.txt 中 opened=True，四项设置均 True，
  actual=1280×720、约 30fps，received=24；首尾 PNG 为未叠加文字的实际相机图像。
- 720p 图像与成功的板端 smoke 证明本轮相机经 PYNQ 到电脑的抓帧链路已通。
  USB 采集格式的 30fps 不等于重新测量了树莓派 HDMI 时序；后者上一轮为 720p60。
- 已启动 `vision_preview.exe --source 1`：PID 20368、running=True、窗口 M2 vision preview。
  见 preview-start.txt；展示实际相机图像后，用户回复「ok」。未另行记录移动物体动作的细节。
- 重启恢复串口、释放采集软件后抓帧成功；不能将原始黑屏的所有原因只归结为其中一项。
- PYNQ 开机自动加载未实现，长时间与断连恢复待验；本轮未改 RTL 或更换 bit 文件。
