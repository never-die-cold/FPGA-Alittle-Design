# Part B v1 arch-test 转发双档证据（2026-10-05）

## 口径

- 核版本：`3ef7020012509004d0e4f4d346b1c6467e7adf04`
- 套件：riscv-arch-test `old-framework-2.x`，commit
  `6f7f47bdc61c0c51c0cbf75789678a1235eeefc2`
- 工具：`riscv64-unknown-elf-gcc 10.2.0`（RV32I/ILP32 multilib）、Icarus 11.0
- 两档使用同一 RTL、tb、ELF、初始内存、参考签名和 200000 周期上限，只切
  `tb_arch_test.ENABLE_FORWARDING`。

## 一键复现

```bash
bash sim/scripts/fetch_arch_test.sh
ARCH_TEST_LOG_DIR="$PWD/data/logs/2026-10-05-partB-v1-arch-test" \
  bash sim/scripts/run_arch_test_matrix.sh
```

## 结果

| 用例 | 参考字数 | fwd | nofwd | 两档 `cmp` |
|:---|---:|:---:|:---:|:---:|
| `add-01` | 588 | PASS | PASS | identical |
| `addi-01` | 564 | PASS | PASS | identical |
| `and-01` | 584 | PASS | PASS | identical |

六份原始输出为 `<test>.fwd.log` / `<test>.nofwd.log`；环境在
`environment.txt`；两档签名 SHA-256 在 `<test>.signatures.sha256`。每个用例的
两份哈希相同，且每档都先由 tb 逐字匹配官方参考签名，再执行两档 `cmp`。

短 hex 预载 8192 字数组时的 `Not enough words` 是预期提示：tb 已先清零完整数组，
随后只覆盖镜像实际包含的字，不影响签名比较。此处只证明三个 RV32I 用例的架构
结果一致，不是 CPI、Vivado OOC、时序或上板证据。
