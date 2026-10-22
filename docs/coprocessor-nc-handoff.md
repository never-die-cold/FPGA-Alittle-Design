# CNN 协处理器 NC 交接

> 交付边界：**JL 交付 ≠ 板级验收**。JL 负责 RTL、Windows Vivado 产物与可追溯包；
> NC 负责下载和现场稳定性；WC 负责软件接入、独立软件看门狗及消费式 W1C 流程。

## 当前真实状态

| 状态 | 结论 | 证据 / 缺口 |
|:---|:---|:---|
| 仿真跑通 | **PASS** | 行为级全回归；BRAM 模式 pattern/zero 各 73,795 元素逐项一致；延迟边界 PASS |
| 综合实现通过 | **UNVERIFIED** | 需 JL 在 Windows 执行 `coprocessor-vivado-checklist.md`；WSL 无 Vivado |
| 板上跑通 | **UNVERIFIED** | 无本轮 bitstream 下载、结果读取或稳定性记录；由 NC 现场验证 |

诊断网络不是正式训练模型，`score_q15` 是整数分数而非概率。生产 payload 地址适配、整机
SoC/BRAM 顶层与板级 IO 尚未验证；没有 JL 门禁通过的 bitstream 时，本包只能做离板交接，
不得下载旧 bitstream 冒充本轮结果。

## 生成与核验交付包

```bash
COPROCESSOR_PYTHON=sim/build/vision-venv-full/bin/python \
  bash sim/scripts/package_coprocessor_nc.sh [JL-verified.bit]
```

脚本会重跑 K3、生成 `dist/cop-board-gate-<commit>/` 与 `.tar.gz`，包含 `VERSION`、
`FILES.txt`、逐文件 `SHA256SUMS`、`EXPECTED_OUTPUTS.tsv`、golden、仿真日志和源码/脚本。
NC 解包后先执行 `sha256sum -c SHA256SUMS`；`VERSION` 中 `VIVADO` 或 `BOARD` 为
`UNVERIFIED` 是当前预期，不得手工改为 PASS。

## 下载、启动与复位

1. 仅接收 JL 明确标记为 40 MHz 门禁通过、且 SHA256 与包一致的 `.bit`；板卡断开外部视频源，
   保存当前可用 bitstream 的路径，连接单块 PYNQ-Z2 与 JTAG。
2. Windows 执行：

   ```bat
   board\scripts\program_soc.bat dist\cop-board-gate-<commit>\payload\JL-verified.bit
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

- OPEN-K2-1：16×64 权重 bank、BRAM 数量/端口模式及整机布线须由 Windows Vivado 确认。
- OPEN-FW-1：固件进入 bitstream/BRAM 初值的通路未验证；本轮只验证仿真加载，需 Windows 侧产出 bitstream。
- OPEN-ENV-1：`all` 已支持 riscv32/riscv64 前缀回落和无工具链 SKIP，仍需在干净环境复测依赖边界。
- OPEN-DOC-1（已修复）：`cop_job.hex` 曾陈旧且无引用；现由 Makefile `all` 重建，并由 `firmware_e2e` 加载。
- 生产 payload→物理 bank 的 manifest 地址适配与完整板级顶层尚未冻结；K3 init 口只用于可复现对拍。
- `compute` 与 `storage` 当前分开 OOC；两份报告资源相加不能替代整机实现。
- 本轮没有 Vivado、bitstream 或实板证据，综合实现与板上状态保持 UNVERIFIED。

## 本次例外与收尾理解题

本轮按 JL 指令覆盖 `AGENTS.md/workflow.md` 的逐步问答门槛：K1–K5 连续执行，不在中途等待；
仍保持小提交、逐步 TB、全回归和本地不 push。收尾一次性检查三题：

1. 为什么 READY 不能作为提交成功或等待条件，而 ACCEPTED 可以？
2. 为什么结果落盘失败时禁止写 CONSUME，RESULT_SEQ 又为什么不能被 CONSUME 清除？
3. 为什么 K3 BRAM 逐元素 PASS 与两个 OOC 报告仍不能宣称板上跑通？
