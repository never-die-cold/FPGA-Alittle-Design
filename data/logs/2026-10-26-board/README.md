# 2026-10-26 上板记录：首次硬件 CNN 诊断网 zero/pattern PASS（PROVISIONAL）

- 日期/执行者：2026-10-26，本机（板端执行）。
- 版本/板端：PYNQ-Z2 192.168.50.99，COM12；包 ~/cop-pkg-imem-20261026；
  bit 59c2c9185e6dcdf88f6971076a459bdf403511746a9e7b15a6ebbc6110f6d659，
  hwh ec3308361eaceda2eaf7a2e745c4d43bb1509c64f0da35fa4310c47f30a8f1e8；
  FCLK1=40.000000 MHz；诊断 payload 36032 B，CRC32 0x2f760211。
- 命令：板端 root + XRT/PYNQ venv：
  sudo -E python3 payload/tools/cop_board_fast_run.py --package . --case zero --measurement /tmp/zero.json
  sudo -E python3 payload/tools/cop_board_fast_run.py --package . --case pattern --measurement /tmp/pattern.json
- 结果（3 轮 zero + 3 轮 pattern，6/6 exit 0，matches_expected=true）：

  | 轮次 | zero | pattern |
  |---|---:|---:|
  | 1 | class 2 / margin 2 / score 258 | class 0 / margin 0 / score 0 |
  | 2 | class 2 / margin 2 / score 258 | class 0 / margin 0 / score 0 |
  | 3 | class 2 / margin 2 / score 258 | class 0 / margin 0 / score 0 |

  zero logits=[2,-3,4]，pattern logits=[1,-3,1]；result_seq=1（每次重新 Overlay 后），
  accepted_snapshot=2146，fw_decision=0x00010403（seq=1，verdict=3/RECHECK，低置信符合预期）；
  最终 STATUS=0x00000061、DMA_BYTES=0x00001000、无 UNCONSUMED。
- 关键板端 workaround（本机未跑 Vivado/仿真）：
  1. 先做 manifest/HWH/SHA 预检，再 Overlay 重载，避免固件等待窗口在预检期间过期；
  2. 用板端 C helper 产生极短 dma_start 高/低脉冲，避免 ack 返回后二次触发 adapter；
  3. 每个 case 独立 Overlay 重载，因此固件单作业限制未暴露；连续作业仍未验证。
- 复现脚本：sim/scripts/cop_board_fast_run.py（板上需 gcc；root + pynq venv）。
- 产物：本目录 zero-fast.json、pattern-fast.json、repeat/{zero,pattern}-{1,2,3}.json、
  camera-enum/、board-state.txt。
- 边界：J02 PROVISIONAL 诊断模型，不是正式 INT8/真实精度；每次检查需重载 bitstream；
  未验证不重载的连续作业、长时间/温度稳定性、真实相机、HDMI/EXE 全链；
  BOARD 首次诊断硬件输出 PASS，但整机验收仍 UNVERIFIED_NEEDS_NC。

## 后续事故（2026-10-26 21:4x，事故前 PASS 已保存）

- 不重载 Overlay 直接跑第二笔：`NO_ACK`，确认固件仍是单作业（每个 case 需重新 Overlay）。
- 尝试用 SLCR `FPGA_RST_CTRL` 复位 cop 域以省掉 Overlay：AXI 读挂死，随后 SSH banner reset、
  COM12 无输出。板卡需要断电重启。
- **SLCR 复位不是已验证 workaround，不要重复**；连续作业需要固件 loop/新 bitstream。
  事故前的最终状态为 `STATUS=0x61`、`RESULT_SEQ=1`、`FW_DECISION=0x10403`。

## 新 loader 的 reset 风险（2026-10-26 22:0x）

- 队友新包 `build/board-packages/diagnostic` 的 `prepare_board()` 会调用 `pulse_cop_reset()`。
- 本板 `FPGA_RST_CTRL` 读回为 `0`；该函数按读回值计算，可能写 `0x2` 再写 `0x0`，
  把 FCLK0/AXI 也一起复位。**不要直接调用新 loader 的 `prepare_board()/run_board()` 上板。**
- 上板改用自包含的 `sim/scripts/cop_board_fast_run.py`：preflight → Overlay → 配置/DMA，
  不调用 `prepare_board`，也不碰 SLCR。
- 新 bit `566B512A…379032` 本身待断电重启后上板验证；上述 reset 风险与 bit 内容无关。
