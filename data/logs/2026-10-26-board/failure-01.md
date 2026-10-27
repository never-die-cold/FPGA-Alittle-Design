# failure-01 —— edge 包 HWH 地址回归（DMA/GPIO 基址漂移）

> 日期：2026-10-26 22:4X ｜ 提交者：Agent B（上板线）｜ 目标：回传 Agent A（构建线）
> 板线红线遵守：未跑 Vivado/仿真/打包，只做实测与取证。

## 现象

- B4（loader clock，edge 诊断包 `cop-board-edge-fix-8884046`）**PASS**：
  `measured_fclk1_mhz=40.000000`、20/20 首读 `0x00000001`、`firmware_smoke=PASS`
  fw_decision=0x00001003。证据：`data/logs/2026-10-26-board/b4-clock-edge.txt`。
  **注意：全程无 JTAG/Vivado**——wrapper 先显式 `import pynq.pl_server.embedded_device`
  注册 EmbeddedDevice（裸 `import pynq` 设备列表为空的根因），loader 即可冷启动自举。
- B5（loader run zero，同包）**FAIL**：
  `BLOCKED: HWH address map differs from the three pinned base addresses`

## 最小证据

1. edge 包 hwh（SHA256 DB5B53B9D1B85E8F28DD83880C0015E3D55AE492BE114809C853955891432506）
   实测 C_BASEADDR：
   - `0x40400000`（应为 DMA `0x40010000`）
   - `0x41200000`（应为 GPIO `0x40020000`）
   - `0x40000000`（COP，正确）
   → Vivado 地址编辑器自动分配覆盖了钉死基址；loader 按 PS 驱动契约
   （docs/contracts/coprocessor-ps-driver-v0.md）拒载，**拒载行为正确**。
2. 对照：gate 包 hwh（board-package-j02，D069DB4F…C6BB）C_BASEADDR =
   `0x40010000/0x40020000/0x40000000`，钉死正确。→ 回归出现在**第二次构建**
   （22:08 重启的那次，PYTHONHOME 修复后）。
3. 板上 /tmp 无任何 A 会话留下的 case JSON（其 fast-run 探针未产出一例实测）。
4. 板上现状：edge bit（9341F7FA…4160）已加载，fclk1=40.000000，PL 处于 loader
   clock 成功后的状态；旧包三套目录未动。

## 结论与请求（给 A）

- **根因（B 已定位）**：`build/create_pynq_cop_bd.tcl:71` 的 `assign_bd_address`
  为空参调用——Vivado 对未指派段自动分配，且**两次构建结果不同**
  （gate 构建产出 0x40010000/0x40020000，edge 构建产出 0x40400000/0x41200000）。
  自动分配不可依赖；本 tcl 每次运行都重建 BD，无历史状态兜底。
- 门禁漏检：`build_pynq_cop_gate.tcl` 未校验生成 HWH 的 AXI 基址是否仍为
  钉死三基址——建议把 hwh_capabilities 的三基址断言加进门禁（防复发）。
- 构建线修复方向（B 推荐 a）：
  a. 在 `assign_bd_address` 之后对三段**显式 set_property offset/range**：
     - `ps7/M_AXI_GP0/SEG_pl_*`（COP 寄存器）= 0x40000000 / 4K
     - `ps7/M_AXI_GP0/SEG_dma_Reg` = 0x40010000 / 64K
     - `ps7/M_AXI_GP0/SEG_dma_control_Reg` = 0x40020000 / 64K
     （段名以 get_bd_addr_segs 实际返回为准）
  b. 并检查第二次构建为何与第一次产出不同（同 tcl 同版本，唯自动分配解释成立）。
- 修好后请给出新 bit/hwh/xsa SHA + gate 原始行（WNS/DRC/CDC/readmem 五行）。
- 本轮 B 侧已有成果（不受影响）：B2 四包校验、B3 板上逐文件对拍、
  B4 时钟/活性门禁 PASS、无 JTAG 冷启动路径打通（可复用 wrapper：
  `data/logs/2026-10-26-board/` 记载，脚本源 `~/cop-pkg-edge-20261026/remote-tools/run_loader.py`）。

## B 侧下一步（等新包）

- 新包到达 → 重跑 B2（SUMS）→ B3（上传新目录）→ B4/B5/B6 全套
  （zero/pattern/roi_001/frame 四例，全走正常 loader）。
