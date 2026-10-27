# 2026-10-27 新包 2fc2bdd4 板验：zero / pattern PASS，clock smoke 与固件口径冲突

> 执行：WC 线（COM4 串口控制台，无有线网口）｜包：`cop-board-gate-2fc2bdd4a8f8.tar.gz`
> 结论：**两例诊断网在板上与黄金一致；preflight 通过；20/20 首读 PASS。**
> 但 JL 给的 `clock --smoke-timeout 2` 在新固件上会以 `FIRMWARE_NO_ACTIVITY` 退出——这是
> 判据与“空闲无超时”固件不兼容，不是硬件未跑；zero/pattern 已证明固件实际在跑。

## 1. 包与传输

- tar：2,660,217 B；SHA256 `e2eb5bd340f01c9cbfb2930a55d8ec36cbbdcdd6f0923636ed1e812b8b862127`（主机与板上一致）。
- 主机解包 `SHA256SUMS`：**116/116 OK**，见 `package-116.txt`。
- 串口 base64 整包传输到 `~/cop-pkg/cop-board-gate-2fc2bdd4a8f8.tar.gz`；板上 `sha256sum` 同上，见 `transfer-tar.txt`。
- 板上解包到 `~/pkg-2fc2bdd4a8f8/cop-board-gate-2fc2bdd4a8f8`，解包后 `sha256sum -c SHA256SUMS`：**116 OK**，见 `pkg-check-summary.txt`（`pkg-check-board.txt` 含 tar 的“时间戳在未来”警告，板端时钟偏慢，不影响内容）。
- 板端 `/home/xilinx` 剩余 6.4 GB；未删除/覆盖任何旧包。

## 2. PYNQ 坑：`.xsa` 不能和 `.bit` 同目录

首次 `clock` 在 `Overlay(bit)` 处失败：

```text
UnknownInputFileExtension: .../payload/pynq_cop_40mhz.bit is not a valid input
```

原因：PYNQ 的 `embedded_device.is_xsa()` 只看 `.bit` 旁是否有 `.xsa`，有就把 bit 当 XSA 解析。处理：板上把 `payload/pynq_cop_40mhz.xsa` 移到 `payload/xsa/`（bit/hwh 不动，内容不变；116/116 已在移动前完成）。建议 JL 打包器默认把 xsa 放子目录，或 loader 显式忽略它。

## 3. 时钟与固件口径

`clock` 的干净部分（`clock-no-smoke.txt`，同一 `prepare_board` 去掉 smoke）：

```text
board_sequence=hwh_clocks,reconfigure_pl,wait_stable,status_check
clock_topology=mmcm expected_cop_mhz=40.000000
measured_fclk1_mhz=142.857143
status_first_reads=0x00000001 ×20
CLOCK_NOSMOKE_EXIT=0
```

- 包内 HWH 明确：`FCLK1 = 142.857132 MHz` 送 `cop_mmcm`，`clk_out1 = 40.000000 MHz` 供 `cop_clk_40_i`。因此读回的 142.857143 是 **MMCM 输入**，协处理器域是 40 MHz。
- JL 指令要求“FCLK1 必须回读 40.000000”，与本包 HWH 不一致；若这是直连变体口径，本包不是该变体。按本包 HWH，142.857143 是正确输入；zero/pattern 在该拓扑下通过。
- JL 原命令 `clock --package . --reads 20 --smoke-timeout 2` 的 20 次首读与 FCLK1 均通过，但最后以
  `BLOCKED: FIRMWARE_NO_ACTIVITY` 退出，见 `clock.txt`。
- 原因在固件源码：新 `cop_job.c` 的 `main()` 是 `for(;;)` 空闲循环，只有 `CFG_APPLIED` 提交后才执行作业并写 `FW_DECISION`；无配置时**不写** `FW_DECISION`/`ACCEPTED`。loader 的 `firmware_smoke()` 却要求二者之一非零，所以必然超时。建议 JL 给 loader 加 `--no-smoke`，或把 clock 门禁改成只检查 20 次首读，或让固件在空闲时写一个 boot 状态。

## 4. preflight

命令（板上，base 取 Vivado Address Editor 的 PS AXI 基址）：

```bash
python ~/cop-pkg/sim/scripts/cop_board_preflight.py --base 0x40000000
```

输出（`preflight.txt`）：

```json
{
  "accepted": false,
  "busy": false,
  "capability": 0,
  "error_code": 0,
  "ip_id": 1129271344,
  "ready": true,
  "result_seq": 1,
  "status": 97,
  "unconsumed": false,
  "version": 0
}
```

`ip_id=0x434F5030`、`status=0x61`（READY+CFG_VALID+MODEL_VALID）、`result_seq=1`、无 UNCONSUMED。
`capability/version=0` 与此前一致，不影响本轮；如 JL 期望非零版本号需另补。

## 5. zero / pattern

板上命令（每例都会重新应用 HWH 时钟/Overlay）：

```bash
sudo -E python3 payload/tools/cop_payload_loader.py run --package . --case zero \
  --measurement /tmp/zero-2fc2.json --timeout 30
sudo -E python3 payload/tools/cop_payload_loader.py run --package . --case pattern \
  --measurement /tmp/pattern-2fc2.json --timeout 30
```

| case | exit | class | margin | score | logits | matches_expected | result_seq | fw_decision |
|:---|--:|--:|--:|--:|:---|:---|--:|:---|
| zero | 0 | 2 | 2 | 258 | 2,-3,4 | true | 1 | 0x10403 |
| pattern | 0 | 0 | 0 | 0 | 1,-3,1 | true | 1 | 0x10403 |

两例均 `payload_bytes=36032`、`payload_crc32=0x2f760211`、`error_code=0`、`valid=1`、`low_conf=1`、`accepted_snapshot=2146`、`status_first_reads=[1]`。原始输出见 `zero.txt`、`pattern.txt`。

## 6. JTAG 记录

为避免 PYNQ 同名 `pynq_cop_40mhz.bit` 的 `Overlay(download=True)` 空操作，先用 Vivado 2026.1 JTAG 直接烧本包 bit：

```text
Device xc7z020 (JTAG device index = 1) ...
End of startup status: HIGH
PROGRAM_DONE xc7z020_1
```

见 `jtag-program.txt`。JTAG 后 `clock` 仍是 smoke 超时、zero/pattern 仍 PASS，说明 bit 已进 PL，失败点只在 smoke 判据。

## 7. 判定与未覆盖

- ✅ 包完整性：主机/板上 116/116。
- ✅ 时钟/首读：142.857143 MHz（MMCM 输入）→ 40 MHz cop 域；20/20 `STATUS=0x1`。
- ✅ preflight：IP_ID/STATUS/RESULT_SEQ 可读，无 UNCONSUMED。
- ✅ zero/pattern：与 `EXPECTED_OUTPUTS.tsv` 完全一致。
- ⚠️ JL 原 `clock` 命令退出 1（smoke 判据），不是时钟/固件失败；建议 JL 修 loader 或固件空闲状态。
- ⚠️ FCLK1 字面 40.000000 与包内 MMCM 142.857 口径冲突，需 JL 确认变体。
- ⬜ 未覆盖：多目标（本包未含修复版）、连续作业/不重载 Overlay、长时/温度、正式模型精度、视频变体（本包明确不含）。
- 本包 `VERSION` 仍为 `BOARD=UNVERIFIED_NEEDS_NC`；本轮只把 zero/pattern/preflight 的板级结果交回，不等于整机验收。
