# Part C 四档 arch-test 回归（2026-10-06）

> 用途：riscv-arch-test 对 Part C **四档**（fwd/nofwd/bht1/bht2）的「优化不改语义」独立判据——同一测试集、签名逐字比对。
> 被测：`dev/rtl@3c6b794`（Part C）；套件 `old-framework-2.x @6f7f47b`。

## 环境

| 项 | 值 |
|:---|:---|
| 工具链 | `riscv32-unknown-elf-gcc` 14.2.0（MSYS2 ucrt64，本次安装） |
| iverilog | **原生 Icarus Verilog 12.0**（`C:\iverilog\bin`）|
| 套件 | `riscv-non-isa/riscv-arch-test` `old-framework-2.x`，commit `6f7f47b`（`sim/scripts/fetch_arch_test.sh` 拉取，不入库） |
| python | MSYS2 ucrt64（bin2hex.py） |
| 运行 | MSYS2 bash：`export PATH=/c/iverilog/bin:/ucrt64/bin:$PATH` |

> ⚠️ 为何用原生 iverilog：`core_top.v` 的前向引用（`bp_predict_taken`/`redirect_target` 先用后声明）在 **MSYS2 的 iverilog（精化阶段）与 Vivado `-sv`** 会报错；原生 bleyer iverilog 容忍。**请 RTL 线采纳 `../2026-10-06-partC-verify/core_top_fix.diff`**（此缺陷同时也阻塞团队「MSYS2 iverilog 四档」与 Vivado 综合/仿真）。

## 工具改动（sim/ 验证线边界）

为支持四档 arch-test，验证线补了两处**纯测试侧**改动：
- `sim/riscv/tb_arch_test.v`：新增 `parameter [1:0] BHT_MODE`，`core_top` 例化传入；
- `sim/scripts/run_arch_test.sh`：模式支持 `fwd|nofwd|bht1|bht2`，并给 `iverilog -P` 传 `BHT_MODE`。

## 结果：3 测试 × 4 档全 PASS，且同测试四档签名一致

| 测试 | fwd | nofwd | bht1 | bht2 | 签名 sha256（四档一致） |
|:---|:--:|:--:|:--:|:--:|:---|
| `add-01` | PASS | PASS | PASS | PASS | `2CF021B9706DB910…` |
| `addi-01` | PASS | PASS | PASS | PASS | `3B35D271BEDA81A7…` |
| `and-01` | PASS | PASS | PASS | PASS | `3E302355377BB10A…` |

- 每档各 `PASS: <test>-<mode> signature N words match reference`（add-01=588、addi-01=564、and-01=584 字）。
- **同一测试的 fwd/nofwd/bht1/bht2 四个签名输出 sha256 完全相同** → 四档语义一致。
- 原始日志：`add-01.{fwd,nofwd,bht1,bht2}.log` 等（共 12 份）。

## 复现

```bash
export PATH=/c/iverilog/bin:/ucrt64/bin:$PATH
bash sim/scripts/fetch_arch_test.sh          # 首次
for m in fwd nofwd bht1 bht2; do bash sim/scripts/run_arch_test.sh add-01 I $m; done
# 同理 addi-01 / and-01
```
签名输出：`sim/build/arch_test/rv32i_m/I/<test>.<mode>.signature.output`（gitignore）。

## 边界

- 只补测试侧（tb/脚本）与证据；未改 RTL（`core_top_fix.diff` 作为建议）。
- 本次测试集为既有 RV32I 子集（add/addi/and）；扩展子集/其他 device 未做。
