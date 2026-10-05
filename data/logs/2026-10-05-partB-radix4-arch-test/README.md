# Part B Radix-4 功能回归（2026-10-05）

## 口径

- 仓库 HEAD：`2e03716010bef1ec61daf50bdeef21cdb1e8c65b`；
- 未提交 RTL/sim 指纹见 `environment.txt` 的 `rtl_sim_diff_sha256`；
- riscv-arch-test：`old-framework-2.x`，commit `6f7f47bdc61c0c51c0cbf75789678a1235eeefc2`；
- 两档使用同一 RTL、ELF、参考签名和周期上限，只切 `ENABLE_FORWARDING`。

## 一键复现

```bash
ARCH_TEST_LOG_DIR="$PWD/data/logs/2026-10-05-partB-radix4-arch-test" \
  bash sim/scripts/run_arch_test_matrix.sh
bash sim/scripts/run_iverilog.sh rv32im
```

## 结果

| 用例 | 参考字数 | fwd | nofwd | 两档签名 |
|:---|---:|:---:|:---:|:---:|
| `add-01` | 588 | PASS | PASS | identical |
| `addi-01` | 564 | PASS | PASS | identical |
| `and-01` | 584 | PASS | PASS | identical |

`rv32im.log` 重新确认整核 `tohost=142879`、`exit=0`。六份 arch-test 日志均先逐字
匹配官方参考签名，再由矩阵脚本比较 fwd/nofwd 输出；对应 SHA-256 见
`*.signatures.sha256`。短 hex 的 `Not enough words` 为预期提示：tb 已预先初始化全部
8192 个字。本目录证明 Radix-4 后功能语义保持，不代替 CoreMark、Vivado 或上板证据。
