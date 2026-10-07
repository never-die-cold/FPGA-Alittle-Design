# Pi → PYNQ HDMI 四视图

源：Camera Module 3 → 树莓派相机预览 → HDMI IN；HDMI OUT → 采集卡 USB Video。
新诊断 bit 限定 **1280×720@60、总时序 1650×750**；电脑 USB 采集可以协商 30fps。

## 使用

诊断包单独放在 `/home/xilinx/vision_diag`，原 `/home/xilinx/vision_m2` 留作回退。
在 PYNQ 串口 shell 执行，环境脚本必须在 sudo 的 shell 内加载：

```bash
sudo bash -c 'source /etc/profile.d/xrt_setup.sh && source /etc/profile.d/pynq_venv.sh && python3 /home/xilinx/vision_diag/m2_onboard.py load'
```

等 3 秒，让 HDMI 接收重新锁定。然后按需切换（替换最后的模式参数）：

```bash
sudo bash -c 'source /etc/profile.d/xrt_setup.sh && source /etc/profile.d/pynq_venv.sh && python3 /home/xilinx/vision_diag/display_view.py --view color'
sudo bash -c 'source /etc/profile.d/xrt_setup.sh && source /etc/profile.d/pynq_venv.sh && python3 /home/xilinx/vision_diag/display_view.py --view gray'
sudo bash -c 'source /etc/profile.d/xrt_setup.sh && source /etc/profile.d/pynq_venv.sh && python3 /home/xilinx/vision_diag/display_view.py --view gauss'
sudo bash -c 'source /etc/profile.d/xrt_setup.sh && source /etc/profile.d/pynq_venv.sh && python3 /home/xilinx/vision_diag/display_view.py --view edge'
```

| 模式 | 电脑画面 | R0 改动 |
|:---|:---|:---|
| color | 树莓派输出的彩色像素 | 只清 bit4，保留分析开关 |
| gray | FPGA 定点 RGB 转灰度 | bit4=1，bit0/bit3=0 |
| gauss | FPGA 3×3 高斯平滑 | bit4/bit0=1，bit3=0 |
| edge | 高斯后接 Sobel 边缘 | bit4/bit0/bit3=1 |

命令保留 bit1 快照和 bit2 OSD；如果原先启用了 OSD，处理图上仍会出现已配置框。
每次写暂存 R0，再 R11 提交、等 R12 确认。`--status` 返回的是暂存 R0 与确认编号，
不能独立证明采集卡画面正常。无输入视频时提交会超时。

切换无需重载 bit。`m2_onboard.py smoke` 和旧 demo 会用旧预设覆盖 R0，回到彩色显示；
旧预设只选择分析拓扑，要显示处理结果请用 `display_view.py`。

## 与原图的区别

灰度公式 `(77R+150G+29B)>>8`；高斯核 `[1 2 1;2 4 2;1 2 1]/16`；
Sobel 输出 `min(255, |Gx|+|Gy|)`。边界复制像素。后三种图均由 FPGA 产生。
缩放到 224×224 的快照仍是独立分支，这些 HDMI 画面都是 1280×720。

新显示适配把完整 RGB/VS/HS/DE 和显示选择一起延迟 **4968 像素时钟**，
约 **66.91µs @74.25MHz**；这是 RTL 边界固定延迟，不是摄像头到电脑的实测总延迟。
分析像素存入带行号、帧标记的四行循环 RAM，按延迟后的原图位置读出。
单拍分析 VS/HS 不直接驱动 HDMI。复位/失锁后等待新的完整 VS 边沿再输出。

## 重建与证据

```bash
bash sim/scripts/run_iverilog.sh vision diagnostic
bash sim/scripts/run_iverilog.sh vision diagnostic_720
bash sim/scripts/run_iverilog.sh vision all
bash sim/scripts/run_iverilog.sh vision_python
bash sim/scripts/run_vision_xsim.sh diagnostic
VISION_HDMI_OUT=sim/build/hdmi-diagnostic VISION_HDMI_EVDIR=data/logs/2026-10-07-hdmi-diagnostic/hdmi bash sim/scripts/run_vivado_hdmi.sh
VISION_BOARD_PKG=sim/build/board_pkg_diagnostic bash sim/scripts/make_board_pkg.sh sim/build/hdmi-diagnostic/vision.xsa
```

Windows 可用 `VISION_PYTHON` 指定实际 Python；Vivado/XSim 需可用本机许可。
串口传输入口 `sim/scripts/pynq_uart_send.ps1 -Archive sim/build/board_pkg_diagnostic/board_pkg.zip -Log data/logs/2026-10-07-hdmi-diagnostic/uart-transfer.txt`。
接收端校验 ZIP SHA256、CRC 和固定文件名集合后才写入诊断目录。
包内 manifest 记录 bit/hwh/脚本哈希；未提交源码明确标注 dirty。

失败回退：用上面的 load 命令把目录换成 `vision_m2`，等重新锁定，再重新打开 USB Video。
采集卡只能被一个程序独占。开机自动加载、CNN、自动目标定位、DDR 显示对照未实现。

## 拔插后的恢复顺序

2026-10-07实测表明：拔掉HDMI IN后控制寄存器仍可访问，提交按预期返回NOVIDEO；但直接
重插可能使树莓派在无EDID时退化为1664×746/74.440MHz，并可能让USB采集卡冻结损坏帧，
因此不能声明自动恢复。手动恢复顺序如下：

1. 保持PYNQ上电并加载诊断bit，使HDMI IN提供EDID。
2. 重启树莓派，`kmsprint`必须为connected、1280×720@60、74.250MHz、1650×750。
3. 再加载一次PYNQ bit，等待3秒并执行`display_view.py --view color`。
4. 若采集卡仍重复同一损坏帧，同时拔掉其USB和HDMI至少5秒，再先接HDMI、后接USB。
5. 抓取连续帧；要求0黑帧、首末哈希不同且目视无局部花屏。

完整证据见 `data/logs/2026-10-07-hdmi-diagnostic/README.md`。要实现无需干预的恢复，需为
树莓派固定CEA EDID或增加HDMI热插拔恢复管理；当前尚未实现。
