# 相机多轮重启复查：枚举与独占拍照（2026-10-20）

- 日期/执行人：2026-10-20，NC主控；Pi日历Oct06，记录以PC日期为准。
- 版本：dev/riscv@5f8abe2 + 本轮未提交nc_ssh_session.py；当前Pi boot_id=b281bb1c-a8e0-4e7f-9ab7-9c6e9390a00e。
- 命令：0001..0004.request.json，通过用户认证的临时SSH串行执行；原始响应含真实退出码与completion_confirmed。
- 结果：服务最初auto-restart、52次重试、exit255/no cameras available；停止后无rpicam进程，独立枚举仍无相机。独占nopreview拍照exit255、NO_JPEG。
- 产物：8份原始请求/响应；未产生照片；本轮未改代码、服务文件、启动配置或RTL，未commit。
- 边界：当前传感器未枚举，不能证明具体硬件损坏，也不能以争用单独解释；等用户确认CSI接线状态后再判断下一步。

## 与用户提供解释的对照

用户描述PID2575长期占用/dev/video0，管线失败后妨碍其他程序；这可以解释某一时刻的设备争用，但不是本次重启后的现场状态。

- 本次读取MainPID=0、auto-restart，日志为no cameras available，不是Pipeline handler in use。
- 停pi-camera-preview.service后MainPID=0、inactive/dead；ps无rpicam-hello/still。
- /dev/video0不存在；其他video10..31为编解码/ISP节点，不能当作相机传感器存在的证明。
- rpicam-still --list-cameras仍No cameras available；独立拍照同样exit255。
- camera_auto_detect=1；设备树未见camera/imx传感器，I2C未见已绑定传感器，imx708/unicam模块未加载。未进行I2C总线扫描或强制加载overlay。
- get_throttled=0x0；/boot/firmware/config.txt SHA256=ef0e5fbe7691f7c8a6e4dfd6d59b1a122d650d35f60e402e784ea360e1e2ea4e。
- 前一轮同样做过独占拍照：当时IMX708可枚举、配置后frontend timeout、exit124，记录在../2026-10-20-nc-board/pi-ssh/0004.response.json；因此既不能把旧结果全归因于占用，也不能据现有证据断定排线已坏。

服务仅临时停止，enabled设置未变；SSH保持连接以便用户确认后继续，不承诺在助手关闭后自动监控。相机正常、N02完整验收与真实网络输出仍未完成。


## 再次重启更新：a48c8956（当前最新）

用户再次重启并恢复电脑↔Pi网线；新boot_id=a48c8956-92a9-4a9e-beb4-0ec6827af9d4。与上方b281bb1c轮分开保存，详见[本轮原始证据](retry-a48c8956/README.md)。

- 本轮IMX708可枚举，已经不再是“找不到相机”。
- 停预览服务、ps确认无rpicam、fuser确认无人占用后，独立拍照仍exit124、无JPEG、frontend timeout。
- 内核过滤日志未发现本轮Failed to start media pipeline: -22；不能套用上一时刻的占用/管线解释，也不能直接认定硬件损坏。
- 当前服务已临时停止、开机启用未改变；SSH连接暂保留。真实相机出图未完成，未修改代码/启动配置/RTL。

## 2026-10-24 入库归档

原始文件归档为 `evidence.tar.gz`，用途是保留本轮取证并减少跟踪文件数；本地展开文件另存 `sim/build/2026-10-24-merge-review/original-evidence/`，由本目录 `.gitignore` 排除后续展开文件。原始失败结论不变，本次未复跑硬件。

- 包内文件：15；压缩包字节：8039。
- SHA256：`165f628ed8b457cfcebd5cc1ad486554a0c5991fe4c160ff37f02156acc4c3f5`；逐文件路径/字节/SHA256 见 `ARCHIVE-MANIFEST.json`。
- 来源：上述 2026-10-20 现场原始文件；2026-10-24 归档时逐文件与工作区字节比较一致。
- 从仓库根目录恢复后，原文所有相对路径仍可使用：

```powershell
python -m tarfile -e data/logs/2026-10-20-nc-camera-recheck/evidence.tar.gz data/logs/2026-10-20-nc-camera-recheck
```
