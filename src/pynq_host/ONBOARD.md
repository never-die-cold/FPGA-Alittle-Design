# ONBOARD —— 模块二上板 runbook（PYNQ-Z2）

> 产物由 `bash sim/scripts/make_board_pkg.sh` 组装到 `sim/build/board_pkg/`（bit/XSA 为构建产物不入库）。
> 基址依据：`sim/scripts/create_hdmi_bd.tcl` `assign_bd_address 0x40000000/64K → pipe/s_axi/reg0`。

## 接线（上电前）

- HDMI IN（板上收口侧）← 源设备（HDMI 摄像头 / 笔记本），源输出 **1280×720@30 或 @60**
- HDMI OUT ← 显示器或 USB 采集卡 → Windows EXE 预览
- 板卡以太网接同一网段（SSH 传输文件与远程执行）；串口留作救援通道

## 步骤（每步独立取证）

0. **环境**：`python3 m2_onboard.py env` —— pynq 版本、包内文件齐全。
1. **传输**：PC 侧 `scp board_pkg/* xilinx@<板IP>:/home/xilinx/vision_m2/`。
2. **加载**：`python3 m2_onboard.py load` —— Overlay 下载成功，ip_dict 有 0x40000000 段。
3. **通路**：源接 HDMI IN，OUT 出彩色原图（本 overlay 显示路径恒为彩色直通）。
4. **视频在位**：`python3 m2_onboard.py smoke` —— PASS = commit 帧首确认（视频流动）；
   NOVIDEO = 查源分辨率/线材；FAIL = 寄存器通路异常。
5. **演示**：`python3 m2_onboard.py demo` —— 灰度诊断口拓扑切换 GRAY→GAUSS→GAUSS_SOBEL→
   GRAY_SOBEL 各 5s → OSD 框动效 60 组 → SNAPSHOT 点亮（HDMI 显示不变）。
6. **鲁棒性**：源断电/重插 → OUT 恢复；换源（笔记本 720p60 ↔ 摄像头）；采集卡侧观察。
7. **延迟**：秒表/高帧率拍摄对比源与 OUT（口径：直通实测，非 PLL 对照）。

## 证据归档

板上输出重定向到 `data/logs/<日期>-vision-onboard/`（env/load/smoke/demo 各自日志 +
现场照片/采集卡截图）；提交前过理解门槛（AGENTS.md）。

## 已知边界（离板已定）

- 灰度 `out_*` 的 OSD 是诊断口，HDMI 主显示恒为彩色原图——别在 HDMI 上找检测框。
- dvi2rgb 无 PS 侧锁定状态寄存器：锁定与否只能从 OUT 画面/NOVIDEO 判定。
- 无视频时 commit 按契约超时（vision_regs.wait_applied TimeoutError），属预期行为。

## 板端环境备忘（PYNQ 3.1 镜像实测，2026-10-03）

- 用 `/usr/local/share/pynq-venv/bin/python3`（裸 python3 无 pynq）；Overlay/MMIO 需 root。
- `xilinx` 用户需在 render/video 组（`sudo usermod -aG render,video xilinx`），
  否则 pyxrt 打不开 `/dev/dri/renderD128`。
- **load 之后等 2-3 秒再 smoke**：bit 重载后 dvi2rgb 重锁有竞争，紧跟 load 的
  commit 会 NOVIDEO（已实测复现一次，等待后复跑 PASS）。
- bit 为易失配置：断电后重新执行 load 即可，无需重传文件。
- 视频在位/断连监视：`sudo … python3 onboard_smoke.py watch [秒]`（周期 commit 探测
  R12 帧首确认，打印 STREAM/STALL/BUSY 事件与 WATCH-SUMMARY，退出码可判）。
  原 `watch_video.py` 已并入该子命令并删除。
