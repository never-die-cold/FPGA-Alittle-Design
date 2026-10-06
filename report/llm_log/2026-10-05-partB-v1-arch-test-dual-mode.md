# [2026-10-05] Part B D2.3a：arch-test 转发双档入口

> 标签：#riscv #arch-test #转发 #验证

## 1. 任务与实现

现有 arch-test 入口只能运行 `core_top` 默认参数。本步保持同一 tb、同一 RTL 和同一
参考签名，仅增加 elaboration 参数：

- `tb_arch_test.ENABLE_FORWARDING` 原样传入 `core_top`；
- `run_arch_test.sh <test> <ext> fwd|nofwd` 用 Icarus `-P` 切换；
- 输出分别命名为 `<test>.fwd.signature.output` 与
  `<test>.nofwd.signature.output`，避免后跑覆盖先跑；
- 工具前缀优先使用 `RISCV_PREFIX`/`riscv32-unknown-elf-`，当前环境缺少时回退到
  已安装的 `riscv64-unknown-elf-`。

本步没有改变参考签名、固件编译选项、存储器初始化或签名比较算法。

## 2. 验证与边界

```text
bash -n sim/scripts/run_arch_test.sh                         PASS
无效模式                                                      正确失败
缺少 sim/arch_test/suite                                      正确早失败
tb_arch_test ENABLE_FORWARDING=1/0                            均编译通过
riscv64 GCC -march=rv32i -mabi=ilp32                         生成 ELF32
multilib                                                      含 rv32i/ilp32
git diff --check                                              无输出
```

套件尚未获取，因此本步不能声称 `add-01/addi-01/and-01` 已通过。真实 3×2 签名
矩阵与两档 `cmp` 属 D2.3b。

## 3. 理解门槛

1. **为什么使用参数和 `-P`，不能复制两份 tb？**
   用户回答：同一 tb/RTL 只切一个 elaboration 参数，才能固定其他变量；复制或手改
   会使两版漂移，破坏公平性、复现性和审计性。

2. **为什么两档签名必须使用不同文件名？**
   用户回答：相同文件名会让后跑覆盖先跑，只剩一份证据，无法执行双档比较；分开
   命名才能保留两档输出并做 diff。

3. **为什么 `riscv64-unknown-elf-` 可以生成 RV32I？**
   用户回答：实际目标由 `-march=rv32i` 和 `-mabi=ilp32` 决定。补充判定：前缀是
   工具链目标/默认能力标识，不是宿主标记；安装还必须具有相应 multilib。本机实测
   multilib 包含 `rv32i/ilp32`，产物 ELF 头为 `Class: ELF32`、`Machine: RISC-V`。

### 判定

三题通过。用户理解单变量对照、证据隔离和交叉工具链目标选择。D2.3a 可以本地
提交；arch-test 实际 PASS、Vivado OOC 和正式 CPI 仍不得宣称完成。

## 4. D2.3b 三用例×双档矩阵

套件获取后确认 commit 为 `6f7f47bdc61c0c51c0cbf75789678a1235eeefc2`，与 Part A
锚点一致。`run_arch_test_matrix.sh` 顺序运行 `add-01/addi-01/and-01` 的 fwd 与
nofwd 六项，每档先逐字匹配官方参考，再 `cmp` 同用例的两档输出。结果为
588/564/584 字全部匹配，矩阵最终退出码 0。原始日志和环境记录位于
`data/logs/2026-10-05-partB-v1-arch-test/`。

### D2.3b 理解题与用户答案

1. **为什么既匹配官方参考，又执行两档 `cmp`？**
   用户回答：前者证明结果正确，后者证明转发没有改变语义；只互比会漏掉两档产生
   同一个错误签名的情况。
2. **为什么记录套件完整 commit？**
   用户回答：不同 commit 可能改变测试源码或参考签名，即使各自 PASS 也使用了不同
   标尺，不能公平比较；固定 commit 才可复现、审计。
3. **为什么短 hex 的 `Not enough words` 在这里安全？**
   用户回答：tb 在 `$readmemh` 前先将完整 IMEM/DMEM 初始化为确定值，短文件只覆盖
   实际镜像范围，尾部不会成为 X。若没有预填、文件被截断/路径错误，或程序读取未
   覆盖区，这条提示就可能代表真实问题。

### D2.3b 判定

三题全部通过。D2.3 arch-test 双档验收完成；这些签名只证明所列 RV32I 用例的架构
结果，不代表正式 CPI、Vivado OOC、时序或上板通过。
