# sw/riscv_fw —— RISC-V 裸机程序

运行在自研 RISC-V 核上的裸机 C 程序：任务调度、协处理器驱动、基准测试。

## 规划内容

- `main.c`：主调度流程（触发预处理 → 启动推理 → 取结果 → 上报 PS）
- `cop_driver.c/h`：CNN 协处理器驱动（自定义指令封装）
- `bench.c`：CPI/性能基准测试程序
- `link.ld` / `start.S`：链接脚本与启动代码
- `Makefile`：工具链构建脚本

> 当前 `main.c` 为工具链冒烟程序（无 libc，做 RV32IM 乘除运算并写 `tohost`），
> 跑通后按规划内容逐步替换为真实固件。

## 统一工具链（全队唯一指定）

MSYS2 ucrt64 预编译 GNU 工具链，2026-09-11 安装验证版本：

| 组件 | 版本 |
|:---|:---|
| gcc | 14.2.0-1 |
| binutils | 2.47-1 |
| newlib | 4.5.0.20241231-1 |

```powershell
# 1. 安装 MSYS2（已装可跳过），确认 C:\msys64\ucrt64\bin 在 PATH
# 2. 刷新源并安装 RV32IM 工具链（下载约 186 MB）
& C:\msys64\usr\bin\bash.exe -lc "pacman -Sy --noconfirm && pacman -S --noconfirm --needed mingw-w64-ucrt-x86_64-riscv32-unknown-elf-gcc"
# 3. 验收：版本 + rv32im/ilp32 库存在
riscv32-unknown-elf-gcc --version
riscv32-unknown-elf-gcc -march=rv32im -mabi=ilp32 -print-multi-lib
```

精确版本复现记录：

```text
mingw-w64-ucrt-x86_64-riscv32-unknown-elf-gcc 14.2.0-1
mingw-w64-ucrt-x86_64-riscv32-unknown-elf-binutils 2.47-1
mingw-w64-ucrt-x86_64-riscv32-unknown-elf-newlib 4.5.0.20241231-1
```

## 构建

```powershell
mingw32-make          # 产出 hello.*（RV32IM）、hello_v0.*（RV32I）、hello_test.*（逐指令自检）
mingw32-make clean
```

编译参数固定在 `Makefile`：`-mcmodel=medany -mno-relax -O2`，
链接使用 `-nostdlib -nostartfiles -T link.ld`；`hello` 用 `-march=rv32im`，`hello_v0` 用 `-march=rv32i`。

| 产物 | 入库 | 说明 |
|:---|:---:|:---|
| `hello.elf` / `hello_v0.elf` | 否 | 完整链接结果（ELF32 / RISC-V） |
| `hello.bin` / `hello_v0.bin` | 否 | 裸二进制 |
| `hello.dis` / `hello_v0.dis` | 是 | objdump 反汇编，测试证据 |
| `hello.hex` / `hello_v0.hex` | 是 | `$readmemh` 32 位小端字，指令 BRAM 预载用 |

## 冒烟程序与预期

| 程序 | 指令集 | 预期执行结果 | 用途 |
|:---|:---|:---|:---|
| `main_v0.c` → `hello_v0.hex` | RV32I | `tohost = 13`（`0xD`），`tohost_exit = 0` | **v0 核程序级冒烟**（`sim/riscv/tb_core_smoke.v`） |
| `test_rv32i.S` → `hello_test.hex` | RV32I | `tohost_exit = 0`；失败则为用例编号（1–38） | **RV32I 逐指令自检**（`sim/riscv/tb_core_test.v`） |
| `main.c` → `hello.hex` | RV32IM | `tohost = 142879`（`0x22E1F`），`tohost_exit = 0` | Part A 收尾补 M 后上核 |

> 观测约定：`main` 写结果值到 `tohost`（`0x8000_3FF0`）；`start.S` 写退出码到 `tohost_exit`（`0x8000_3FF4`）——两者分离，退出码不会覆盖结果值。

## 冒烟验收（2026-09-11 已通过）

- `readelf -h`：ELF32、Machine RISC-V、Entry `0x80000000`
- `readelf -A`：`Tag_RISCV_arch: "rv32i2p1_m2p0_zmmul1p0"`（即 RV32IM）
- 反汇编覆盖 I/M：`auipc/addi/lui/lw/sw/beq/bne/j/jalr/mul/divu/remu`
- 与 `sim/tools/verify_rv32i.py` 独立编码器交叉核对 11 条指令机器码，ALL OK
- 程序观测：`main` 写 `tohost = 142879` 等结果值，`start.S` 写 `tohost_exit = 0`（工具链阶段验证）
- 2026-09-11 v0 核实测：`hello_v0` 在 `sim/riscv/tb_core_smoke.v` 上 PASS（`tohost=13, tohost_exit=0`）
