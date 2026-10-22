# [2026-10-22] 协作记录：pynq_cop_top 生产板顶、双时钟 CDC 与 16 ROI 槽

> 标签：#coprocessor #SoC #板顶 #CDC #PYNQ
> 平台：Codex（VS Code 扩展）｜ 模型：GPT-5
> 相关 commit：`c595292` `d4c8f6b` `2387150` `96af56c` `6f662fe`

## 1. 任务与初始提示词

Phase 2：新增生产板顶 `pynq_cop_top`（或扩展 `pynq_z2_top`）：PS AXI4-Lite（复用
`cop_axi_lite_frontend`）+ `soc_top(ENABLE_COP=1)` + `cop_top` + 权重 BRAM + DataMover +
IMEM 预载重新生成的 `cop_job.hex`；双时钟（PS 100 MHz / cop 40 MHz）与复位、CDC 约束齐全。
整机（非 OOC）40 MHz 门禁通过后才允许 bitstream/.hwh。

## 2. 模型第一版方案

`pynq_cop_top` 把 PS 域 AXI4-Lite、AXIS DataMover 与 cop 域计算/存储分开，经
`cop_axi_lite_cdc` 与 `cop_axis_async_fifo` 跨域；BD Tcl 生成 PS7+DMA+自定义 IP；
新增 `tb_pynq_cop_top` 验证 AXI-Lite 读 COP_ID 与 73-bit AXIS beat 保序；
板顶专用 `cop_activation_storage` 扩为 16 个 4,096 B ROI 槽。

## 3. 失败现象

1. 旧 `cop_bram_storage` 只有单 ROI；`ROI_COUNT>1` 时多目标会重复/覆盖同一 ROI。
2. `create_pynq_cop_bd.tcl` 使用了错误的 BD cell 名（`control/`、`memory/`、`gpio/`），
   `validate_bd_design` 直接失败；PS 未用 AXI 端口时钟脚悬空。
3. 任务描述表未接入，板顶当前只支持 `target_id == roi_index` 的恒等映射（OPEN-BT-4）。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | 旧存储单 ROI | 与 16 ROI 契约不一致 | 新增 `cop_activation_storage` 16 槽 | `activation_storage` PASS |
| 2 | BD validate 失败 | 实例名错 + 未用端口悬空 | 改用 `control_ic`/`memory_ic`/`dma_control`，关闭 GP1/S_AXI_GP0/HP2 | JL 侧 BD 可完成布线 |
| 3 | 只支持恒等映射 | 描述表未接入 | 记录 OPEN-BT-4，不冒充完整板顶 | 文档明确限制 |
| 4 | 双时钟 CDC 需要证据 | 不能只看波形 | `tb_pynq_cop_top` + 异步 FIFO 随机比率 TB | PASS |

## 5. 最终结论

已实现并仿真通过：

```text
PASS: pynq_cop_top 100/40MHz AXI-Lite reads COP_ID and AXIS FIFO preserves 73-bit beat; cop_job.hex elaborated
PASS: activation_storage keeps 16 ROI slots distinct and preserves ping/pong interface
```

双时钟/复位与 CDC 约束已落库；整机门禁与板级仍需 Windows Vivado/NC（见 K4/CDC/NC 记录）。
`target_id != roi_index` 的任意描述表仍为 OPEN-BT-4，不能据此宣称完整契约板顶。

## 6. 经验沉淀

- 触发条件：把已验证的离板 RTL 接到真实 PS/BD 板顶。
- 排查步骤：先核对 RTL 容量与最大 ROI/任务数；BD 用真实 cell 名并关闭未用 PS 端口；
  跨域必须有 TB 证据，不能只看“能综合”。
- 适用范围：PYNQ/Zynq 板顶；换 PS 配置或 FCLK 需重跑 BD 与 CDC。
#skill候选
