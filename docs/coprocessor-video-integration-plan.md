# J07 视频与协处理器集成摸底

> 状态：**PLAN / UNVERIFIED**。本文件只依据现有 RTL、BD 和 2026-10-12 capture 证据估算；
> 没有修改 RTL、没有运行 Vivado，也不表示视频、CNN 或板级链路已经接入。

## 现有边界

`pynq_cop_top` 只有 PS 100 MHz AXI-Lite/AXIS、CNN 40 MHz、DMA 控制与 LED；生产 BD 只有
PS7、MM2S AXI DMA、GPIO 和两组 interconnect，没有 HDMI 管脚、视频 RX/TX 或 S2MM 取帧。
现有 HDMI BD 则包含 `dvi2rgb`、`vision_axi`、`rgb2dvi` 与 74.25 MHz 像素通路；capture 候选
另加 Video In to AXI4-Stream、VDMA S2MM、capture status、复位与中断。

2026-10-12 证据只证明原 base 能取得 1280×720×3 BGR 完整副本并与 HDMI OUT/UVC 短时共存；
两路没有共同 capture_id。C01 候选的 DDR 帧槽所有权、动态颜色对拍和长测仍未验收。

## 三问结论

### a) 取帧能否并入现有 cop 位流

**HDMI：可以规划为同一 BD，但不能直接复用当前 cop 位流。** 需要新增或合并：

- `dvi2rgb`、`rgb2dvi`、`vision_axi`，以及 HDMI IN/OUT、DDC、HPD 外部端口和 `hdmi_pins.xdc`；
- `v_vid_in_axi4s` 异步视频 FIFO、AXI VDMA S2MM、`capture_status_axi`、`proc_sys_reset`、
  IRQ concat、AXI protocol converter；
- capture AXI-Lite 地址窗和 DDR 写通路；cop 的 HP0 已被 MM2S 使用，应把 memory interconnect
  扩为双主设备仲裁，或启用独立 HP1 给 capture，不能把两个 master 直接并接；
- 帧完成/错误/槽号到 PS 的所有权协议，以及 PS 生成 ROI 后复用现有 64-bit MM2S ROI loader。

**UVC：不能作为 PL HDMI 输入直接并入。** 现有 UVC 是 PYNQ HDMI OUT 后的 PC 采集卡；若改为
PS USB host 摄像头，必须由 Linux/OpenCV 取帧并经 DDR/PS 生成 ROI，再走现有 cop DMA，且会绕开
HDMI RX、像素时钟与 C01 状态证据。

### b) 资源余量

| 项目 | DSP | BRAM36 等价 | LUT / FF | 证据边界 |
|:---|---:|---:|---:|:---|
| 当前 cop 整机 | 136 | 69 | 当前门禁约 48% / 34% | Vivado 2026.1 实测 |
| 独立 C01 capture 整机 | 0 | 44.5 | 6,370 / 8,340 | 独立旧工程，不是增量综合 |
| 保守简单相加 | 136 | 113.5 | 约 60% / 42% | 仅容量筛查，重复计算 PS/互连 |
| x7z020 上限/余量 | 220/84 | 140/26.5 | 53,200 / 106,400 | 未扣实现拥塞与新互连 |

单帧 1280×720×3 为 2,764,800 B，剩余 26.5 BRAM36 约 119 KiB，**整帧绝不能放 PL BRAM**；
C01 的 4 帧缓存位于 DDR。最小方案不新增 PL 缩放器，由 PS 裁剪/缩放后复用现有 16×64×64
ROI 存储。若要求 PL 内定位、缩放或额外行缓存，DSP/BRAM 增量目前没有综合证据，可能超过
BRAM/布线余量，必须单独 OOC 和整机实现后判断。

### c) 三时钟域与 CDC

最小数据通路跨两次异步边界：

1. 74.25 MHz 像素域（周期 13.468 ns）→ PS/VDMA 100 MHz：用 `v_vid_in_axi4s` 异步 FIFO；
2. PS/DDR 100 MHz → CNN 40 MHz：复用现有 AXI DMA 和 `cop_axis_async_fifo`。

必须跨域的控制/元数据包括：pixel lock、overflow、SOF/帧完成/错误事件从像素域到 100 MHz；
视频配置从 100 MHz 到像素域；ROI payload/TLAST、DMA kind/start/ack、AXI-Lite 请求/响应从
100 MHz 到 40 MHz。多位帧号、槽号、ROI/target_id 不得逐位 2FF；应在源域锁存，经
toggle/ack 或 FIFO 原子传递。复位须分别在三域异步断言、同步释放，不能把改 FCLK 后的旧域
继续使用。

## 最小可落地方案

1. 以 C01 capture BD 为取帧前端，VDMA S2MM 写 4 个 DDR 帧槽，显示支路保持旁路。
2. PS 仅在 VDMA 完成且无 capture/VDMA 错误后取得槽所有权，复制稳定帧。
3. PS 完成定位、裁剪和 64×64 灰度缩放，按 manifest/ROI 格式经现有 MM2S 单包装载。
4. RISC-V/CNN 仍按现有 START/ACCEPTED/终态/RESULT_SEQ 流程；结果附同轮 frame/ROI 身份。
5. 最后才做同一顶层的资源、CDC、DRC、时序和断源恢复门禁；此前全部标 UNVERIFIED。

## NC 需要提供

- HDMI 与 UVC 两种拓扑的实际接线、分辨率/帧率/颜色格式，以及采用哪一种作为部署输入；
- 每次运行的 bit/hwh SHA256、boot/overlay id、FCLK 读回、capture/VDMA CSR 起止快照；
- 含动态标记的连续帧、槽号/帧号、DDR BGR SHA256，用于证明无撕裂、无混帧、颜色正确；
- 断源/恢复、冷启动和至少 30 分钟并发 capture+cop 日志，保留首个错误现场。

## 最大风险

最大风险不是静态资源，而是 **VDMA 帧槽所有权与 frame/ROI/result 身份没有原子绑定**：显示正常、
`stream_seq` 增长都不能证明 PS 读到稳定且属于当前轮的帧，可能产生静默的旧帧或混帧分类。

依据：`src/riscv/pynq_cop_top.v`、`build/create_pynq_cop_bd.tcl`、
`sim/scripts/create_hdmi_bd.tcl`、`sim/scripts/create_capture_hdmi_bd.tcl`、`hdmi_pins.xdc`、
`docs/contracts/c01-capture-implementation-baseline.md`、
`data/logs/2026-10-12-n03-base-return/README.md`。
