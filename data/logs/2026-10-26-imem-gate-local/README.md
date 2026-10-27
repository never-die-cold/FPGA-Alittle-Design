# 2026-10-26 本机重跑 IMEM 整机门禁：PASS（未上板）

> 分支 `dev/riscv`（`8884046`，已 ff 到 origin）｜工具：本机 Vivado 2026.1
> 结论：**门禁 PASS，bit 内含固件初值**（`IMEM_FIRST_WORD=00008117`）。
> 板级结论仍归 NC；本机未做板验。

## 1. 为什么要本机重跑

JL 的门禁包（bit `1232769f…`）不在本机：`dist/` 为空、全盘无 `cop-board-gate-*.tar.gz`、
git 树里也没有 tar。本机原有的 `build/run/pynq_cop_40mhz/pynq_cop_40mhz.bit` 是早前本地构建
（`59c2c918…`，无 IMEM 门禁报告），不能作为门禁证据。故按 `docs/coprocessor-imem-init-gate.md`
的 Windows 流程本机重跑。

## 2. 失败与修复：PYTHONHOME 污染

直接跑 Tcl 时门禁在第一次 `cop_imem_gate.py` 调用就崩：

```text
File "…\Vivado\tps\win64\python-3.13.0\lib\argparse.py", line 89, in <module>
AssertionError: SRE module mismatch
```

Vivado 会把 `PYTHONHOME` 指向自带的 3.13；子进程用主机 Python 3.12 时加载 3.13 标准库 → SRE 断言。
修复方式（只在本机 wrapper，不改提交脚本）：`unset ::env(PYTHONHOME)/PYTHONPATH` 并显式
`set ::env(COP_PYTHON)`。wrapper 文件 `build/_gate_env.tcl`（build/ 不入库）。

## 3. 结果

```text
READMEM LOG GATE PASSED: relevant_lines=0 blocking=0
IMEM POST-SYNTH GATE PASSED: first_word=00008117 nonzero=1 cells=8
PYNQ COP WHOLE-SYSTEM GATE PASSED: WNS=2.771 DSP=136 BRAM36=69.0 CDC_ALLOWLIST=CDC-15=73,CDC-3=12,CDC-6=7 DRC=0
```

`gate_summary.txt` 现含 IMEM 四行（`IMEM_FIRST_WORD` / `IMEM_INIT_NONZERO` / `READMEM_WARNINGS`）。

## 4. 本机产物（不入库，按哈希引用）

| 文件 | SHA256 |
|:---|:---|
| `pynq_cop_40mhz.bit`（21:50） | `566b512abd63140fc9137e3c49c3d2a74b46520cf323139e914672aa35379032` |
| `pynq_cop_40mhz.hwh` | `d069db4fa760ccb0e49a0ccc566311829fcd9421e0cdddbea8c626e4ee65c6bb` |
| `pynq_cop_40mhz.xsa` | 见 `build/run/pynq_cop_40mhz/` |

注意：本机 bit 与 JL 的 `1232769f…` **不是同一构建**（不同主机/路径），哈希不可互认；
两者都由同一 Tcl 门禁判 PASS。

## 5. 已就绪的两个上板包

- `build/board-package-j02/`：诊断网 pattern/zero，`model_id=0x4A303250`；
  本地 preflight PASS（payload 36032 B、ROI 4096 B、DMA 16 位、期望 zero=class 2）。
- `build/board-package-trained/`：训练权重，`model_id=0x4A303251`；
  case `roi_001` 期望 `class=2 margin=53 score=6837 logits=-12,-30,41`（与 RTL 仿真
  `logits=29e2f4` 一致），case `frame` 期望 `class=0`。
  打包器 `sim/scripts/build_board_package.py` 按 network manifest 的 case 列表生成
  `EXPECTED_OUTPUTS.tsv`，不再写死 pattern/zero。

## 6. 板侧状态（21:48–21:54）

并行会话记录（`data/logs/2026-10-26-board/README.md`）：21:40 用旧本地 bit
`59c2c918…` 跑通 zero/pattern 6/6；随后第二笔不重载 Overlay 出现 `NO_ACK`（固件单作业），
尝试 SLCR 复位 cop 域后 **AXI 读挂死、SSH/串口同时不通**，板卡需断电重启。
本机 21:53 复测：ping 不通、paramiko banner reset、`192.168.50.1` 侧链路在位。

## 7. 通道恢复后的顺序（每 case 必须重载 Overlay）

```text
1. 断电重启板卡 → 确认 SSH/ping
2. 上传 board-package-j02 → sha256sum -c SHA256SUMS
3. sudo -E python3 payload/tools/cop_payload_loader.py clock --package . --reads 20
4. run --case zero → 期望 class 2 / margin 2 / score 258
5. run --case pattern → 期望 class 0 / margin 0 / score 0
6. 上传 board-package-trained → 重复 clock → run --case roi_001
   期望 class 2 / margin 53 / score 6837 / logits -12,-30,41
```

**不要**再用 SLCR `FPGA_RST_CTRL` 复位 cop 域；**不要**在同一 Overlay 下跑第二笔。
