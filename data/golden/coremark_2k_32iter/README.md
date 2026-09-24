# Golden：CoreMark 2K profile / 32 迭代 `crcfinal`

> 契约：`docs/coremark.md` §5.2（生成与复核）
> 生成：2026-09-23，基准线 `dev/bench`；复核状态见文末

## 固定 profile

| 项 | 值 |
|:---|:---|
| 源码 | `src/riscv_fw/coremark/vendor/`（EEMBC coremark，commit `1f483d5b`，SHA-256 见 `data/evidence/2026-09-23-coremark-source.md`） |
| 数据规模 | `TOTAL_DATA_SIZE=2000`（2K performance） |
| seeds | `0 / 0 / 0x66`（`PERFORMANCE_RUN`） |
| 迭代数 | `ITERATIONS=32` |
| 内存模型 | `MEM_STATIC`、`HAS_FLOAT=0` |

## 期望值（golden）

```text
iter=32 seedcrc=0xe9f5 crclist=0xe714 crcmatrix=0x1fd7 crcstate=0x8e3a crcfinal=0x8799
```

## 生成命令（host 双路）

在 `src/riscv_fw/` 下（MSYS2 ucrt64 的 x86_64 gcc）：

```bash
gcc -O2 -DTOTAL_DATA_SIZE=2000 -DITERATIONS=32 -Icoremark/host -Icoremark/vendor -Icoremark \
    coremark/core_main.c coremark/vendor/core_list_join.c coremark/vendor/core_matrix.c \
    coremark/vendor/core_state.c coremark/vendor/core_util.c coremark/host/core_portme.c \
    -o golden_host_o2.exe && ./golden_host_o2.exe
# -O0 同源再跑一遍（独立性检查）
```

host 移植层：`src/riscv_fw/coremark/host/core_portme.{c,h}`（时间桩返回 0；CRC 与时间无关）。

## 双路结果

| 路径 | 输出 | 结论 |
|:---|:---|:---|
| host gcc `-O2` | `GOLDEN ... crcfinal=0x8799 errors=1` | 一致 |
| host gcc `-O0` | `GOLDEN ... crcfinal=0x8799 errors=1` | 一致 |
| RTL v0 仿真（32 迭代） | `obs ... crcfinal=0x8799`、`tohost=34713(0x8799)` | 一致（`data/logs/2026-09-23-coremark/`） |

- `errors=1` 是官方 `<10s` 有效性的错误计数（host 与仿真均不足 10s），按契约 §5.4 只作证据、不作判据

## 复核状态

- 基准线双路（O2/O0）+ RTL 仿真三方一致 ✅
- 验证线独立环境复核 ⬜ 待办（契约 §7.2 未决项 #4 的收口条件）
