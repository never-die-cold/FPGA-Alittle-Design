# CoreMark 脚本接入回归（2026-09-23）

> 基线 commit：`ac6dcee`；修改后 commit hash 待提交后补录。
> 工具：Icarus Verilog 13.0 / MSYS2 UCRT64；RISC-V 工具链由 arch-test 脚本调用。

## 命令

从仓库根目录运行：

```bash
bash sim/scripts/run_iverilog.sh coremark
bash sim/scripts/run_iverilog.sh all
bash sim/scripts/run_arch_test.sh add-01
bash sim/scripts/run_arch_test.sh addi-01
bash sim/scripts/run_arch_test.sh and-01
```

## 原始日志

- `run_coremark.log`
- `run_all.log`
- `arch_add-01.log` / `arch_addi-01.log` / `arch_and-01.log`

## 结果

- `coremark`：PASS；`tohost=34713 (0x8799)`、`exit=0`、`iterations=32`、四个 CRC/golden 判据全对；21,275,738 cycles，CoreMark/MHz=1.506。官方 `<10s` 字段 `errors_raw=1` 按契约不作为 FAIL 判据。
- `all`：8/8 PASS（imem、dmem、RV32I smoke、RV32I 38 用例、fwd、muldiv、RV32IM、CoreMark）。
- arch-test：`add-01` 588 words、`addi-01` 564 words、`and-01` 584 words，均与参考签名一致。
- Icarus 对短 hex 的 `$readmemh` 深度提示为预期；arch-test 使用 `-s tb_arch_test` 后无未例化 `imem` 的加载错误。

| 日志 | SHA-256 |
|:---|:---|
| `run_coremark.log` | `D16A1C1674309A212B55CF6FC7437C11CD345CE10116C1B7534FE2D078905D63` |
| `run_all.log` | `E39BA0FF625C7CB0C8D4FD683E72E8A5F34AC7AC880A269CB63F0055884CEDCF` |
| `arch_add-01.log` | `B87C1B298D76172E7AF3DF3665D564CC1D3DD35F0C6EA12D445E4CA01A4F374D` |
| `arch_addi-01.log` | `B1053C47E0DA46166CC190893DD0654262C5B83CCA0ABC7B13DAD7CE748DD69D` |
| `arch_and-01.log` | `3F1940E21A4C36FF9B928C78D3BCF5CB67F0178DC59C4DA1B620869193AF9920` |

本文件记录脚本入口回归结果；已有 CoreMark 评分/黄金数据见 `data/logs/2026-09-23-coremark/`。
