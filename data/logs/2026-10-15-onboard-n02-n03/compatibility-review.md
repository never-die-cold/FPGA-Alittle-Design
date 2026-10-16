# N03 首轮实验输入与兼容核对

本轮是 NC 的有界实验，不代签 JL 集成验收或正式 N03。
用户已明确恢复上板任务，并要求无代码改动的检查连续推进、跳过理解题。

## 版本选择

- 主工作区：`dev/model@891cba2` + 既有未提交改动，保留不覆盖。
- 应用交付：`origin/dev/exe@ffb7ab2`，新增 9 个提交；通过 git archive
  保存独立快照，未 merge/cherry-pick。新 C01/backend/base 适配不包含新位流。
- 首轮单帧脚本取 10/14 `inputs/` 冻结三件套，复制到本目录 `single-inputs/`。
  SHA 对照 `single-input-sha256.json`；没有使用新增 park 开关的漂移入口。
- 候选位流为 `capture-1791713720540454.bit/hwh`，SHA 分别为
  `86d2adb0343de1785270d207eee3c6b8fee2a6444bc64705bc068e3fc781d14f`、
  `eaaf68c3732f1a2bf85756fc0b3a8c6b07bb5cf5b36f32020882860a6aaebf5c`。
  板上仍须重新核对；不把当前已漂移 RTL 视为该位流源码。

## 静态核对

对照冻结输入 `data/evidence/2026-10-12-c01-exact-build-inputs/inputs/`：

- 地址：pipe/status/VDMA 分别为 0x40000000/0x42000000/0x43000000，
  各 64KiB，入口在下载前解析 HWH 并逐段校验。
- VDMA：6.3，仅 S2MM，四槽、24bit stream、64bit HP0，TUSER fsync。
- 复位：PS FCLK_RESET0_N 接已核对极性的 proc_sys_reset；
  peripheral_aresetn 统一接 DMA、AXI 控制/内存、输入桥及状态；
  像素侧另由 video lock/pixel_reset 驱动。冻结 Tcl 明确断言辅助复位为低有效且绑高。
- 单帧驱动：复位/四地址/3840 stride 与 HSIZE/720 VSIZE；
  几何配置后清停机粘滞错误，读回不干净则拒绝 RUN。
- 正常发布须联合确认自动停止、IRQ、槽 0、描述符、代次与 CAP 错误状态，
  再 invalidate/独立复制；异常人工停止不授权正常发布。
- 清理不能确认时由入口持有缓冲并保活；本轮不加 timeout-k 包装或强杀。

## 官方寄存器依据

本轮重新读取 AMD PG020 6.3：

- [S2MM VDMACR](https://docs.amd.com/r/en-US/pg020_axi_vdma/S2MM_VDMACR-S2MM-VDMA-Control-Register-Offset-30h)：
  FrameCntEn/IRQFrameCount 支持指定帧数完成后停止；人工 RS 清零可提前终止流传输。
- [S2MM VDMASR](https://docs.amd.com/r/en-US/pg020_axi_vdma/S2MM_VDMASR-S2MM-VDMA-Status-Register-Offset-34h)：
  保留实际错误位；不以 Halted 单独证明完整帧。
- [Park pointer](https://docs.amd.com/r/en-US/pg020_axi_vdma/PARK_PTR_REG-Park-Pointer-Register-Offset-28h)：
  当前写槽与请求 park 槽有不同字段。park 候选的实际完成/保护绑定尚待实测。

静态匹配与服务替身不能代替动态完整性、颜色、慢复制或持续共存测试。
本轮不据此冻结驱动；完整 WC/JL/NC 交接验收仍另留证据。
