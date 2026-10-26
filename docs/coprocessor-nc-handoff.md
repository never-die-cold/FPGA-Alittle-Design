# CNN 协处理器 NC 交接

> 交付边界：**JL 交付 ≠ 板级验收**。JL 负责 RTL、Windows Vivado 产物与可追溯包；
> NC 负责下载和现场稳定性；WC 负责软件接入、独立软件看门狗及消费式 W1C 流程。

## 当前真实状态

| 状态 | 结论 | 证据 / 缺口 |
|:---|:---|:---|
| 仿真跑通 | **PASS** | 行为级全回归；BRAM 模式 pattern/zero 各 73,795 元素逐项一致；延迟边界 PASS |
| 综合实现通过 | **历史 PASS / 当前 UNVERIFIED** | 旧源码门禁 WNS +2.771 ns、DSP 136/220、BRAM36 69/140；加入 IMEM INIT 门禁后的新源码待 Windows clean build |
| 板上跑通 | **UNVERIFIED / BLOCKED** | 40 MHz 下 fresh Overlay 后 STATUS 20/20 为 `0x1`；但 FW_DECISION/ACCEPTED 均无活动，bit 内 IMEM 初值尚未验证 |

诊断网络不是正式训练模型，`score_q15` 是整数分数而非概率。PROVISIONAL payload 地址适配
与整机顶层已仿真。JL 已提供本次门禁生成的 bit/hwh；JL 门禁通过不等于板级验收，
NC 仍须完成下载、读回与现场稳定验证，不得用旧 bitstream 冒充本次产物。

继续操作前先按 [`coprocessor-board-clock-runbook.md`](coprocessor-board-clock-runbook.md)
确认 FCLK1 实测 40 MHz；payload/GPIO/DMA 序列见
[`coprocessor-payload-loader.md`](coprocessor-payload-loader.md)。JTAG 只配置 PL，不应用 PS7 时钟。

## 生成与核验交付包

```bash
COPROCESSOR_PYTHON=sim/build/vision-venv-full/bin/python \
  bash sim/scripts/package_coprocessor_nc.sh \
    build/run/pynq_cop_40mhz/pynq_cop_40mhz.bit \
    build/run/pynq_cop_40mhz/pynq_cop_40mhz.hwh \
    build/run/pynq_cop_40mhz/pynq_cop_40mhz.xsa \
    build/reports/pynq_cop_40mhz/gate_summary.txt
```

脚本会重跑 K3、生成 `dist/cop-board-gate-<commit>/` 与 `.tar.gz`，包含 `VERSION`、
`FILES.txt`、逐文件 `SHA256SUMS`、`EXPECTED_OUTPUTS.tsv`、golden、仿真日志和源码/脚本。
四个产物参数只能在整机 Tcl 门禁 PASS 后同时提供；本包应显示
`VIVADO=PASS_2026.1_40MHZ_WHOLE_SYSTEM`，而 `BOARD=UNVERIFIED_NEEDS_NC`。
NC 解包后先执行 `sha256sum -c SHA256SUMS`，不得手工修改 VERSION。

本次源产物 SHA256：bit 为 `d14a4bd037b1809c74fe511f1c7667edbc6bd6ecac8a8712a423946f5f1e2a1a`，
hwh 为 `928f0d594ccbb83c8bd17e5ed284a6f2849e1b598c28073c779afb1ff9849107`，xsa 为
`755f70337bdc5a06da0dcaa715c512806b7011efa09f95128314cb78a2ad96ec`。同日首构 `9e1b24e2…`
与固件提交并发，已经作废；只采用仓库干净后生成的上述产物，旧哈希包禁止继续沿用。

## 下载、启动与复位

1. 仅接收 JL 明确标记为 40 MHz 门禁通过、且 SHA256 与包一致的 `.bit`；板卡断开外部视频源，
   保存当前可用 bitstream 的路径，连接单块 PYNQ-Z2 与 JTAG。
2. Windows 执行：

   ```bat
   board\scripts\program_soc.bat dist\cop-board-gate-<commit>\payload\pynq_cop_40mhz.bit
   ```

3. 看到 `PROGRAM PASSED` 后按 BTN0 复位再释放；等待 MMCM 锁定与软件启动。下载成功本身不算验收。
4. WC 按 `coprocessor-wc-interface.md` 提交：先确认无 UNCONSUMED，写 CMD，等 sticky ACCEPTED
   或软件超时，再等唯一终态或软件超时；不得等待 READY。
5. DONE 时读 `RESULT_*` 和 `RESULT_SEQ`，校验序号并成功落盘后才写 CONSUME；ERROR 时先读
   `ERROR_CODE` 再 CONSUME。落盘失败禁止清灯。

## 应看到什么

- `EXPECTED_OUTPUTS.tsv` 的诊断锚点：pattern 为 class 0、margin 0、score_q15 0、logits
  `1,-3,1`；zero 为 class 2、margin 2、score_q15 258、logits `2,-3,4`。两者 low_conf=1。
- 每笔被受理命令出现 ACCEPTED；随后 DONE/ERROR/TIMEOUT 恰有一个；空闲时 READY=`!BUSY`。
- DONE 的 RESULT_SEQ 比提交前加 1；CONSUME 后 DONE/ERROR/TIMEOUT、RESULT_VALID、ACCEPTED、
  ERROR_CODE 同时清零，RESULT_SEQ 保持。

## 失败恢复与现场记录

软件 NO_ACK/HW_TIMEOUT 时停止新 START，保留状态快照；已有终态或结果落盘失败时不要 CONSUME。
先采集 STATUS、ERROR_CODE、RESULT_SEQ、版本、bitstream SHA256 与复现步骤，再按 BTN0 复位。
复位仍失败则重新下载已知可用 bitstream；无法恢复时保持 `ENABLE_COP=0` 的可用基线，禁止反复
覆盖现场证据。NC 将温度、电源、连续运行次数、首次失败时间和恢复结果写入新的板级日志。

## 已知限制与 OPEN

- OPEN-K2-1（已验证）：Windows 整机门禁已确认 BRAM36 69/140 并完成布局布线。
- OPEN-FW-1：Windows 已生成包含重建 `cop_job.hex` 的 bitstream；BRAM 初值在实板启动仍待 NC 验证。
- OPEN-ENV-1：`all` 已支持 riscv32/riscv64 前缀回落和无工具链 SKIP，仍需在干净环境复测依赖边界。
- OPEN-DOC-1（已修复）：`cop_job.hex` 曾陈旧且无引用；现由 Makefile `all` 重建，并由 `firmware_e2e` 加载。
- OPEN-BT-4：板顶候选的 16 ROI 槽已仿真，但任意 `TARGET_DESC_ADDR` 描述表尚未接入；
  当前只支持 `target_id == roi_index` 恒等映射，不能据此声称完整契约或板级验收。
- manifest v1→影子物理 bank 与生产 PL 顶层已仿真；正式 RELEASE 参数和板验未完成。
- `compute` 与 `storage` OOC 历史结论保留；本次整机门禁已独立 PASS，不能反推板级通过。
- 本轮已有门禁通过的协处理器 bitstream，但尚无实板证据；板上状态保持 UNVERIFIED。
- OPEN-BOARD-CLK-1（顺序根因已复现）：改成 40 MHz 会使旧 cop 域失效；必须重配 PL、等待稳定并
  脉冲 FCLKRESETN1。`0x0` 表示域未就绪/无效，不能作为超频结论；板级功能仍未验收。
- OPEN-IMEM-1：fresh Overlay 后固件两秒内 FW_DECISION/ACCEPTED 均无活动；旧门禁未证明
  `$readmemh` 内容进入 bit。新 Tcl 已加绝对路径、显式依赖、日志与 INIT 门禁，待 Windows 复跑。
- OPEN-LOADER-1（离板已修/板上待验证）：BD 与 HWH 均确认 `C_SG_LENGTH_WIDTH=16`，loader 保持
  36,032 B 单次传输；新 bit/hwh 已过整机门禁，NC 尚未实测 payload 装载。
- OPEN-LOADER-2（离板已修/板上待验证）：`cop_job` 已驻留等 CFG/MODEL/ROI，firmware_e2e 延迟配置
  用例 PASS，干净门禁位流已包含重建固件；NC 尚未验证板上等待路径。PS 仍不得越权写 START。

## 本次例外与收尾理解题

本轮按 JL 指令覆盖 `AGENTS.md/workflow.md` 的逐步问答门槛：K1–K5 连续执行，不在中途等待；
仍保持小提交、逐步 TB、全回归和本地不 push。收尾一次性检查三题：

1. 为什么 READY 不能作为提交成功或等待条件，而 ACCEPTED 可以？
2. 为什么结果落盘失败时禁止写 CONSUME，RESULT_SEQ 又为什么不能被 CONSUME 清除？
3. 为什么 K3 BRAM 逐元素 PASS 与两个 OOC 报告仍不能宣称板上跑通？
