# [2026-10-21] 协作记录：固件驱动的 SoC→MMIO→协处理器端到端 TB

> 标签：#riscv_fw #coprocessor #SoC #E2E #回归
> 平台：Codex（VS Code 扩展）｜ 模型：GPT-5
> 相关 commit：`ee1aff2` `7fe58f3` `e0337ad`

## 1. 任务与初始提示词

缺陷 2：此前没有任何 TB/位流加载 `cop_job.hex`，固件只被主机 C 单测覆盖。
要求新增固件驱动的端到端 TB：IMEM 预载 `cop_job` 产物，CPU 真实执行
submit → 等 ACCEPTED → 等终态 → 读结果 → 校验 `RESULT_SEQ` → 写 CONSUME，并对上 J02 golden；
必须能在 runner 单独跑；Makefile 补 `cop_job.hex` 依赖，不允许“入库但没人用且已过期”。

## 2. 模型第一版方案

`tb_cop_firmware_e2e.v` 复用真实 `soc_top(ENABLE_COP=1)`、真实 `cop_core_mmio_gate` 与
`cop_ctrl_regs`，只把耗时 CNN 替换为由 J02 `zero/result.txt` 驱动的确定性完成模型。
CPU 执行真实固件到 `tohost`；TB 以 PS 身份观察 START/ACCEPTED/DONE/RESULT_META/
至少 3 次 RESULT_SEQ 读取，再执行真实 CONSUME，保持“CONSUME 仅 PS”的冻结边界。

## 3. 失败现象

1. 首次运行 `generate_network_vectors.py` 因系统 `python3` 缺 NumPy 退出 1。
2. TB 在 `saw_*` 断言处 FATAL，且 `fw_counts=0`、`fw_decision=0x00010a03`：
   `result_data` 的字段拼接位宽错位（`6'd0` 与 `5'd0,1'b0` 混用），固件读到的工单字段不对。
3. 已入库的 `cop_job.hex` 陈旧：重建后有 198 个字变化；测试还重生成了 `cop_job.dis`。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | `No module named numpy` | 环境入口 | 使用仓库 venv `COPROCESSOR_PYTHON=...` | 越过 |
| 2 | FATAL；counts=0、decision 错 | 结果字段拼接线宽错位 | 改为 `24'h04fd02,5'd0,1'b0,golden_low,1'b1,6'd0,...` | `firmware_e2e` PASS |
| 3 | `cop_job.hex` 陈旧 | 入库产物无人重建 | Makefile `all` 纳管 `cop_job.hex`，刷新并标 binary | 镜像与固件一致 |
| 4 | `cop_job.dis` 被测试改写 | 生成副产物 | 恢复到 HEAD，不提交 | 工作树干净 |

## 5. 最终结论

`bash sim/scripts/run_coprocessor_iverilog.sh firmware_e2e` 退出 0，PASS 行：

```text
PASS: firmware_e2e CPU START/ACCEPTED/DONE/RESULT_META/RESULT_SEQ/FW writes + PS CONSUME; J02 zero=2/2/258/1
```

覆盖：CPU 执行真实固件 → 真实 `soc_top`/MMIO gate/寄存器 → START/ACCEPTED/终态 →
RESULT_META/RESULT_SEQ → FW_COUNTS/FW_DECISION → PS CONSUME。未覆盖：真实 bitstream/BRAM 初值
通路与板级（OPEN-FW-1）。

## 6. 经验沉淀

- 触发条件：固件只有单元测试、没有装载真实镜像的 SoC 级闭环。
- 排查步骤：先确认镜像真的被 IMEM 加载，再查字段拼接；`counts/decision` 一类“看起来像业务错”
  往往是位宽错位；生成物要么由 Makefile 纳管，要么从仓库移除。
- 适用范围：任何 CPU 固件 + MMIO 外设的端到端验证；换 SoC 仍需重接内存映射。
#skill候选
