# sw/riscv_fw —— RISC-V 裸机程序

运行在自研 RISC-V 核上的裸机 C 程序：任务调度、协处理器驱动、基准测试。

## 规划内容

- `main.c`：主调度流程（触发预处理 → 启动推理 → 取结果 → 上报 PS）
- `cop_driver.c/h`：CNN 协处理器驱动（自定义指令封装）
- `bench.c`：CPI/性能基准测试程序
- `link.ld` / `start.S`：链接脚本与启动代码
- `Makefile`：riscv-gnu-toolchain 构建脚本

## 构建

依赖 riscv-gnu-toolchain（RV32IM），构建步骤定稿后写在此处，保证一键复现。

> 状态：🚧 待开发（M1 里程碑：先在核上跑通 hello + benchmark）
