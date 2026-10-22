# [2026-10-22] 协作记录：AXI-Lite CDC 常 1 锁存、FIFO 空判断与 CDC allowlist

> 标签：#coprocessor #CDC #latch #异步FIFO #门禁
> 平台：Codex + JL（Windows Vivado 2026.1）｜ 模型：GPT-5
> 相关 commit：`8de5de1` `2cf7a9c` `0b1455d` `83f6d77` `bcf6b40`

## 1. 任务与初始提示词

整机门禁 FAIL：`no_clock=360`、`unconstrained_internal_endpoints=120`。要求诊断
`cop_axi_lite_cdc.v` 载荷为何被常量折叠；新增能抓住该 bug 的 TB；给整机门禁加
LDCE/LDPE/LATCH 计数为 0 的硬门禁。CDC 判定必须按真实 `ID Severity Count` 表解析，
建立逐条 allowlist，禁止整类忽略或放宽上限。

## 2. 模型第一版方案

m 侧载荷寄存器全部显式复位；载荷寄存 + toggle 跨域 + 目标域打拍，禁止依赖“未赋值保持”。
TB 在写一笔 MMIO 后断言 m 侧 `awaddr/araddr/wdata/wstrb` 与 s 侧一致且不为全 1，并覆盖读路径。
CDC 解析器要求汇总与明细数量一致、每条路径恰好匹配一条 allowlist；
Critical、未列 ID、超量、格式异常全部 fail-closed。FIFO 改为 next-pointer 注册 full/empty。

## 3. 失败现象

1. 120 个 LDCE 全部落在 `pl/inst/axil_cdc` m 侧 `aw/ar/wd/ws` 载荷链；
   `ar_m1_reg[*]_LDC` 的 D/GE 接常量 VCC、G 接 m_clk 反相——载荷被综合成“常 1 锁存器”，
   等价于 PS 侧地址恒为 1。
2. 去掉 `SHREG_EXTRACT="NO"` 后仍是 120 个 LDCE，排除该属性。
3. 修复 latch 后门禁又因 CDC 报告格式失败：真实表是 `CDC-3 Info 11`、`CDC-6 Warning 7`、
   `CDC-15 Warning 73`，报告中没有旧解析器要求的 `Unsafe/Unknown` 字段。
4. 旧 FIFO 组合 empty 在指针同步边界多预取一项；随机比率 TB 暴露重复/丢失风险。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | 120 LDCE、D/GE 接 VCC | 复位块漏掉载荷链赋值 | `8de5de1` 全载荷显式复位 | Register as Latch=0 |
| 2 | 门禁仍报 CDC 格式 | 解析器按旧字段猜 | `0b1455d` 按 ID/Severity/Count 解析 | 解析通过 |
| 3 | 73 条 CDC-15 | FIFO 读口需结构证据 | 随机时钟比 TB + allowlist | 四档 257 beat 全绿 |
| 4 | allowlist 不足 | JL 回写 5 条 | `bcf6b40` single_sync≤12、gpio_sync≤1 等 | 最终门禁 PASS |

## 5. 最终结论

- 根因：AXI-Lite CDC 载荷链在带异步复位的 always 块中漏赋复位值，Vivado 将其映射为常 1 LDCE。
- latch 修复后：`Register as Latch=0`、`check_timing=0/0/0/0`、WNS +2.607、WHS +0.035。
- CDC allowlist 5 条：single_sync≤12、gpio_sync≤1、axil_payload≤7、fifo_rgray≤5、fifo_read≤73；
  全局 CDC-3≤12、CDC-6≤7、CDC-15≤73，无 Critical。
- `tb_cop_axis_async_fifo_random`：Ts:Tm=10:26、26:10、14:22、22:14，各 257 beat，
  `PASS: axis_fifo_random all ratios no duplicate, loss, or reorder`。
- 最终整机门禁 PASS；板级仍未验证。

## 6. 经验沉淀

- 触发条件：跨域载荷寄存器依赖“未赋值保持”，或在 `always @(posedge clk or negedge rst_n)`
  中只复位控制位、忘记载荷链。
- 排查步骤：先看综合后的 LATCH/LDCE 计数与网表常量；给门禁加 latch=0 硬失败；
  再按真实 CDC 报告 ID/Severity/Count 建 allowlist，逐条给结构证据。
- 适用范围：所有异步 CDC/FIFO；换 Vivado 版本需重看报告格式。
#skill候选
