# CNN 协处理器 NC 交接

> 交付边界：**JL 交付 ≠ 板级验收**。JL 负责 RTL、Windows Vivado 产物与可追溯包；
> NC 负责下载和现场稳定性；WC 负责软件接入、独立软件看门狗及消费式 W1C 流程。

## 当前真实状态

| 状态 | 结论 | 证据 / 缺口 |
|:---|:---|:---|
| 仿真跑通 | **PASS** | 行为级全回归；BRAM 模式 pattern/zero 各 73,795 元素逐项一致；延迟边界 PASS |
| 综合实现通过 | **PASS** | Vivado 2026.1 整机 40 MHz 门禁：WNS +2.498 ns、DSP 136/220、BRAM36 69/140、latch/DRC blocking 均 0；CDC allowlist 全命中 |
| 板上跑通 | **UNVERIFIED** | 尚无本轮 bitstream 下载、结果读取或稳定性记录；由 NC 现场验证 |

诊断网络不是正式训练模型，`score_q15` 是整数分数而非概率。PROVISIONAL payload 地址适配
与整机顶层已仿真。JL 已提供本次门禁生成的 bit/hwh；JL 门禁通过不等于板级验收，
NC 仍须完成下载、读回与现场稳定验证，不得用旧 bitstream 冒充本次产物。

## 生成与核验交付包

```bash
COPROCESSOR_PYTHON=sim/build/vision-venv-full/bin/python \
  bash sim/scripts/package_coprocessor_nc.sh \
    build/run/pynq_cop_40mhz/pynq_cop_40mhz.bit \
    build/run/pynq_cop_40mhz/pynq_cop_40mhz.hwh \
    build/reports/pynq_cop_40mhz/gate_summary.txt
```

脚本会重跑 K3、生成 `dist/cop-board-gate-<commit>/` 与 `.tar.gz`，包含 `VERSION`、
`FILES.txt`、逐文件 `SHA256SUMS`、`EXPECTED_OUTPUTS.tsv`、golden、仿真日志和源码/脚本。
三个产物参数只能在整机 Tcl 门禁 PASS 后同时提供；本包应显示
`VIVADO=PASS_2026.1_40MHZ_WHOLE_SYSTEM`，而 `BOARD=UNVERIFIED_NEEDS_NC`。
NC 解包后先执行 `sha256sum -c SHA256SUMS`，不得手工修改 VERSION。

本次源产物 SHA256：bit 为 `7e1e34304ef71efdfe86ec3e6dbeead6ab419c741806a3334a71474746aa0b6c`，
hwh 为 `cba4d12c58213897c0dbdafd327348ce5d4bd9d21dad6d5a469eb44bd03d799d`。
两次独立构建仅位流文件头 4 B 不同，网表等价且门禁数字一致；旧哈希包禁止继续沿用。

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

## 本次例外与收尾理解题

本轮按 JL 指令覆盖 `AGENTS.md/workflow.md` 的逐步问答门槛：K1–K5 连续执行，不在中途等待；
仍保持小提交、逐步 TB、全回归和本地不 push。收尾一次性检查三题：

1. 为什么 READY 不能作为提交成功或等待条件，而 ACCEPTED 可以？
2. 为什么结果落盘失败时禁止写 CONSUME，RESULT_SEQ 又为什么不能被 CONSUME 清除？
3. 为什么 K3 BRAM 逐元素 PASS 与两个 OOC 报告仍不能宣称板上跑通？
