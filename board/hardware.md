# board/hardware —— 演示硬件与 HDMI 接线

> 本文定义"最终演示形态"的物理链路、配件清单与硬限制；上板实测记录格式见 [`logs/README.md`](logs/README.md)。
> 依据：PYNQ 官方视频子系统文档（HDMI 前端分辨率限制）+ 2026-09-20 团队决议（视频源 = 笔记本 HDMI 输出，显示 = USB 采集卡回笔记本）+ 2026-09-21 修订（**视频源升级为真实 HDMI 摄像头/相机**——应用叙事要求"真实摄像头拍真实场景"，笔记本 HDMI 仅作开发调试源）。
> 决策记录：[`report/llm_log/2026-09-20-demo-hardware-chain.md`](../report/llm_log/2026-09-20-demo-hardware-chain.md)、[`report/llm_log/2026-09-21-narrative-architecture-fix.md`](../report/llm_log/2026-09-21-narrative-architecture-fix.md)

## 1. 最终演示链路

```
[Camera Module 3] ──CSI 排线──▶ [树莓派 4B] ──micro-HDMI(HDMI0)线──▶ [PYNQ-Z2 HDMI IN]  ← 演示正式源（真实场景拍摄）
笔记本 HDMI OUT ──HDMI线①──▶ [PYNQ-Z2 HDMI IN]       ← 开发调试备用源
[PYNQ-Z2 HDMI OUT] ──HDMI线②──▶ [USB 采集卡] ──USB──▶ 笔记本（采集窗口看画面）
笔记本浏览器 ──▶ 校园网 ──▶ Jupyter（<板卡内网IP>:9090）控制与调参
PYNQ-Z2 PROG-UART ──Micro-USB──▶ 笔记本（串口日志 + 下载/调试）
```

- **正式演示源 = 树莓派 4B + Camera Module 3**（对准真实场景拍摄），保证"摄像头进、检测结果出"叙事成立；笔记本 HDMI 输出仅用于开发调试与回归测试。
- 树莓派用独立 5V/3A USB-C 电源，不从 PYNQ USB host 口取电（见 §3.7）。
- 上电顺序：PYNQ 先上电并加载 PL（PL 内 EDID 就绪）→ 树莓派后上电读取 EDID 协商 720p60；顺序反了可能协商到非 720p 模式。
- 备选源：另一块 Zynq-7020 板 HDMI 输出——已有硬件，零新增成本。
- 笔记本一机两用：显示终端（USB 采集卡回显）+ Jupyter 控制中心。
- 数据流单向：视频源的输出只进 `HDMI IN`；`HDMI OUT` 只接采集卡/显示器。禁止把笔记本 HDMI 接到 `HDMI OUT`。

## 2. 配件清单

| 优先级 | 物品 | 规格/说明 |
|:---:|:---|:---|
| 🔴 待购 | **HDMI 输出摄像头/相机**：树莓派 4B（已有）+ **Camera Module 3**（标准 75°、AF 自动对焦、日光版，含 15pin CSI 排线） | 输出 1280×720@60 RGB444；Pi 侧锁 720p60（config.txt `hdmi_group=1`/`hdmi_mode=4` 或 PL EDID 协商）；不要 120° Wide / NoIR；旧款 CM2 固定焦距不适合桌面近摄 |
| 🔴 待购 | micro-HDMI→HDMI-A 公对公短线 0.3–0.5m | Pi 4B 视频口为 micro-HDMI，插 HDMI0（靠 USB-C 电源的口）；买直头，不要转接头 |
| 🟡 待购 | 树莓派 4B USB-C 5V/3A 电源适配器 | Pi 独立供电，不从 PYNQ USB host 取电（§3.7）；不能用 5V/2A 手机头 |
| ✅ 已购 | HDMI 线 ×2 | 标准 Type-A 公对公；1–2 m 短线更稳 |
| ✅ 已购 | USB 视频采集卡 | UVC 免驱；支持 720p60（YUY2）或 1080p30（MJPEG）即可 |
| 🟡 备用 | 笔记本 HDMI 扩展输出 | 开发调试源（测试图/视频）；正式演示不使用 |
| 🔴 已有 | PYNQ-Z2 / 网线 / Micro-USB 线 / microSD | 板卡到货已验证 |
| 🟢 已有 | 树莓派 4B | 演示正式源主机（接 Camera Module 3 经 HDMI 输出）；另一块 Zynq-7020 板 / ESP32 = 备选 HDMI 源与扩展控制硬件 |
| ✅ 已购 | 12V 电源适配器 | 跳线置 REG；HDMI + PL 满载时比 USB 供电稳 |
| 🟡 建议 | USB-C→USB-A 转接头 | 笔记本仅有 USB-C 口时接采集卡用 |
| 🟢 可选 | USB 功率计 | 测 ARM vs 协处理器能效（`data/metrics.csv` 有该项） |
| 🟡 建议 | 小三脚架/桌面支架 | 固定相机机位（工作距离 40–80cm）：保证定位效果与训练/测试数据集机位一致；兼作演示视频拍摄 |

## 3. 硬限制与参数口径

1. **分辨率锁定 720p**：PYNQ 官方文档明确 Z1/Z2 的 DVI 前端"因差分引脚速率限制，官方只支持到 720p"（视频流水线 142 MHz vs 1080p60 像素时钟 148.5 MHz）。源设备统一设 **1280×720@60**（含 HDMI 摄像头输出分辨率，采购时确认）。
2. **PL 直接收发 TMDS**：PYNQ-Z2 没有 ADV7611；采用 `dvi2rgb`/`rgb2dvi`，DDC/EDID 在 PL，HDCP 不支持。依据 [官方视频说明](https://pynq.readthedocs.io/en/v3.0.0/pynq_overlays/pynqz2/pynqz2_base_overlay.html)。`adv7611_init.py` 仅为外接接收器示例，不用于本板。
3. **摄像头走 HDMI**：本演示采用 HDMI 输出相机。板上另有 USB 2.0 host（不应与 PROG-UART 混淆），但 USB 摄像头不是本 PL 直通链路的视频源。
4. **采集卡不参与指标**：USB 采集链路自带 50–200 ms 延迟，只影响观感；端到端延迟指标用 OSD 帧计数器/时间戳或 GPIO 打点实测，`data/metrics.csv` 测量条件注明"经采集卡观测，不计入延迟"。
5. **供电**：USB 供电仅够启动与点灯；跑 HDMI 流水线建议 12V 适配器（Power 跳线切 REG，USB 供电切 USB）。
6. **串口看日志**：Linux 启动日志与 `ip addr` 一律走 PROG-UART 串口（115200-8N1）；HDMI OUT 由 PL 驱动，不显示系统日志。
7. **演示源供电与上电顺序（2026-10-03 定）**：正式源 = 树莓派 4B + Camera Module 3。① 树莓派用独立 5V/3A USB-C 电源，不从 PYNQ USB host 口取电——该口 5V 来自板载共享轨：整板 USB 供电时上游约 500mA，仅够启动（第 5 条）；12V 供电时 5V 轨还要喂 Zynq/PHY/TMDS，抽 3A 给 Pi 会导致 Pi 欠压复位并恶化 HDMI 信号完整性。② 上电顺序：PYNQ 先上电并加载 PL（PL 内 EDID 就绪）→ 树莓派后上电读取 EDID 协商 1280×720@60；顺序反了可能协商到非 720p 模式。③ Pi 侧双保险：config.txt 锁 `hdmi_group=1`/`hdmi_mode=4`（换 Pi OS 版本失效则以 PL EDID 为准，验线时确认）。

## 4. 到货后验线步骤（第一件事）

1. 按 §1 接线；笔记本设 720p 输出；确认 Jupyter 可打开（[`setup.md`](setup.md) §4）
2. base overlay 视频直通验证（Jupyter 新建 notebook）：

```python
from pynq import Overlay
from pynq.lib.video import *

base = Overlay('base.bit')
hdmi_in = base.video.hdmi_in
hdmi_out = base.video.hdmi_out
hdmi_in.configure()
hdmi_out.configure(hdmi_in.mode)
hdmi_in.start()
hdmi_out.start()
hdmi_in.tie(hdmi_out)   # 直通：采集窗口应立即看到笔记本画面
```

3. 通过后按 [`logs/README.md`](logs/README.md) 留记录（硬件连接列写明"视频源 + 采集卡显示 + 720p"），再进入 `src/vision/` 自研流水线开发。

## 5. 状态

- 接线方案：📌 已定（2026-09-20 笔记本源 + 采集卡显示；2026-09-21 修订为真实 HDMI 相机源；**2026-10-03 定案：树莓派 4B + Camera Module 3**，micro-HDMI(HDMI0)→HDMI IN；笔记本 HDMI 输出降级为开发调试源）
- 采购：✅ 已购：HDMI 线 ×2 / USB 采集卡 / 12V 电源适配器；⛔ 待购：Camera Module 3（标准 75° AF 日光版，含 15pin CSI 排线）/ micro-HDMI→HDMI-A 短线 / 树莓派 4B USB-C 5V/3A 电源（建议加桌面支架）；负责人：待认领
- 验线：⬜ 未开始（线到后执行 §4）
