# 模块二：彩色视频直通与分析快照

正式目标为 PYNQ-Z2、1280×720@60、RGB888；224×224 是模块三输入的占位尺寸。
当前接口见 [design_v0.md](design_v0.md)，离板证据见
[本轮记录](../../data/logs/2026-10-02-vision-offboard/README.md)。

```text
HDMI IN → dvi2rgb → 彩色原图直通 → rgb2dvi → HDMI OUT → USB 采集卡 → Windows EXE
                   └→ 归一化 → 灰度 → 高斯/边缘 → 缩放 → 双帧缓冲 → cop_* / 调试 ILA
PS AXI-Lite → 暂存参数 → R11 提交 → 帧首整组生效 → R12 配置号确认
```

PYNQ-Z2 HDMI 直接连 PL，没有 ADV7611。物理工程固定 Digilent IP 提交
`f4613fff005b098065fd5d619a2b88e55720a423`，官方 PYNQ v3.0.1 引脚和 PS 配置经 SHA256 核对。
Digilent 并行视频字节顺序是 R,B,G，`vision_axi.v` 双向转换为内部 R,G,B。

## 已实现与验证

- 22 个仓库内 RTL tb：Icarus 和 XSim 同判据通过；含真实 720p 两帧，
  1,843,200 显示像素、100,352 快照像素、448 行及帧/配置号精确核对。
- AXI AW/W 独立握手、响应反压；整组配置请求/确认；不同频率时钟测试。
- 显示 RGB/原始同步波形恒延迟直通；分析使用内部单拍行尾/帧首标记。
- 双帧缓冲争用修复：读启动与写完成同拍也保护读银行；拥塞、覆盖、排空、复位测试。
- Sobel 增加一级流水；单元首像素延迟 gray=1、gauss=25、gray+sobel=26、gauss+sobel=50 拍。
  灰度诊断口延迟不能当作彩色 HDMI 延迟。
- `video_pipeline` 内部 post-route：WNS +0.330 ns / WHS +0.027 ns，像素周期13.468ns、
  AXI周期10ns；1985 LUT、1515 寄存器、38 BRAM tile、0 DSP。
- PS 配置绑定、定位/逐目标裁剪黄金参考、明确标为 MOCK 的 HTTP 接口和 Windows EXE 原型。

## 一键入口

在仓库根目录、MSYS2 UCRT64 shell 中运行：

```bash
bash sim/scripts/run_iverilog.sh all          # 核、CoreMark、门禁、视觉、stdlib Python
bash sim/scripts/run_iverilog.sh vision all   # 22 个视觉 tb
bash sim/scripts/run_iverilog.sh vision_python
bash sim/scripts/run_vision_xsim.sh all
bash sim/scripts/run_vivado_vision_impl.sh    # 并行边界 OOC 布线
bash sim/scripts/fetch_hdmi_ip.sh             # 固定第三方源，首次需要网络
bash sim/scripts/run_vivado_hdmi.sh           # 全物理 HDMI 工程，离板生成 bitstream
```

`VISION_PYTHON` 可指定 Python 路径；`VISION_VIVADO_BIN` 可指定 Vivado bin 目录。
默认 Vivado 路径为 `/d/Vivado_downloads/2026.1/Vivado/bin`。
物理输出在 `sim/build/hdmi-project/`；脚本不会打开 Hardware Manager 或下载板卡。
EXE 构建和接口原型操作见 [客户端说明](../vision_client/README.md)。

## 验收边界

内部 OOC 正余量不证明 TMDS 引脚、电缆、相机和采集卡闭环。全物理工程状态与余量
以本轮证据记录为准，不能沿用历史综合值。实际下载、相机锁定、源断连/重连、
EDID 兼容、采集卡显示、端到端延迟及 DDR 对照实测仍需上板。

灰度 `out_*` 的 OSD 是诊断能力；HDMI 主显示保留彩色原图。EXE 模拟框不是物体检测；
UVC 原型显示 `UNASSOCIATED`，在硬件帧关联未完成前不叠加网络框。

未实现 / 未接入：正式 CNN/协处理器、实际定位部署、工单检查服务、真实识别结果与
采集卡画面关联。它们属于模块三应用交接，整帧快照不代表逐目标硬件裁剪已经完成。
