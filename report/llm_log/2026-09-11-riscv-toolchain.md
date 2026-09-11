# [2026-09-11] 协作记录：RISC-V 工具链落地——从"双路线"收敛为全队统一 MSYS2 预编译方案

> 标签：#riscv #工具链 #构建
> 平台：OpenCode ｜ 模型：deepseek-flash (deepseek/deepseek-flash)
> 相关 commit：`07104bd`（固件与构建流程）+ 本条记录本身

## 1. 任务与初始提示词

承接 issue #4「安装 RISC-V 工具链并编译 helloworld elf」。在"推荐当前要做的事"的会话中，用户选定该 issue 后给出的关键约束：

> "我们工具链统一使用一个"
> （此前在方案选择中已定：构建脚本用 Makefile + bin2hex.py）

背景：plan.md 排期 9/18 前打通「C 编译 → objdump 反汇编 → objcopy 转 hex」闭环，服务 Part A 基线核的 BRAM 预载。

## 2. 模型第一版方案

计划阶段首版给出**双路线并行**（A：MSYS2 pacman 预编译包；B：xPack `riscv-none-elf-gcc` 跨平台包），并建议两套都装、互相验证；构建脚本按用户选择为 Makefile + `bin2hex.py`。

固件首版 `main.c`：以 `extern volatile unsigned int tohost` 为观测点，局部变量做 `a*b+i` 累加，`-O2` 编译。

## 3. 失败现象（真实偏差）

1. **方案层面偏离团队约束**：双工具链方案被用户当场否决——"不不不，我们工具链统一使用一个"。两套工具链会给三人的构建结果引入不可控差异，违背"版本统一、可复现"的赛题要求。
2. **`-O2` 强度削减吞掉 M 扩展**：首版 `main.c` 中乘数为常量，GCC 把 `×3` 削减为 `slli+add` 序列，`hello.dis` 中**没有任何 `mul` 指令**，冒烟程序名不副实。
3. **第二次尝试仍缺 `div`**：改为 `return (prod / a) == b` 后，GCC 利用"无符号乘积回除等价于检查高 32 位"恒等式，把除法优化为 `mul` + `mulhu` + `snez`，依然没有 `divu/remu`。
4. **pacman 同步局部 404**（基础设施异常）：`pacman -Sy` 期间 `mirror.msys2.org` 的 `clang64.db` 返回 404；但 `ucrt64` 等仓库正常，安装未受影响。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | "我们工具链统一使用一个" | 双路线方案不符合团队一致性要求，且给文档与复现引入歧义 | 删除 xPack 路线，全队唯一指定 MSYS2 ucrt64 `riscv32-unknown-elf`；Makefile 固定 `CROSS`，不再做双工具链交叉验证 | ✅ 单一路线安装成功（GCC 14.2.0-1 / binutils 2.47-1 / newlib 4.5.0） |
| 2 | `hello.dis` 中只有移位无 `mul` | `-O2` 对常量乘数做强度削减，编译优化把 M 扩展"优化没了" | `main.c` 两操作数改为由 volatile 读取派生（`a=seed+7, b=seed+3, prod=a*b`） | ✅ 反汇编出现 `mul`、`mulhu` |
| 3 | `(prod/a)==b` 被折叠为 `mulhu+snez` | 无符号乘除恒等式允许编译器消除除法 | 改为未知除数构造：`1000000u/a` 与 `1000000u%a` | ✅ 反汇编出现 `divu`、`remu`，I/M 指令全覆盖 |
| 4 | pacman 报 `clang64.db` 404 | 单个镜像数据库文件缺失，非包安装失败 | 不处理（ucrt64 正常），记录现象备查 | ✅ 三个包安装完成 |

## 5. 最终结论

**全队统一工具链：MSYS2 ucrt64 `riscv32-unknown-elf`（GCC 14.2.0 / binutils 2.47 / newlib 4.5.0），安装命令与精确版本固定在 `sw/riscv_fw/README.md`，作为唯一权威出处。**

验证方式（2026-09-11 全部通过）：

- `readelf -h`：ELF32 / Machine RISC-V / Entry `0x80000000`
- `readelf -A`：`Tag_RISCV_arch: "rv32i2p1_m2p0_zmmul1p0"`（即 RV32IM）
- `hello.dis` 覆盖 `auipc/addi/lui/lw/sw/beq/bne/j/jalr/mul/mulhu/divu/remu`
- 与仓库内独立编码器 `sim/tools/verify_rv32i.py` 交叉核对 11 条 RV32I 指令机器码，ALL OK（M 扩展该脚本未覆盖，由 objdump/arch tag 佐证）
- `bin2hex.py` 产出 `hello.hex`（4093 个 32 位小端字），首字 `00000117` 与反汇编首条一致

产出：`sw/riscv_fw/` 冒烟固件（start.S / main.c / link.ld / Makefile / bin2hex.py）+ 证据 `hello.dis` / `hello.hex` 入库；预期执行结果 `tohost=142879 (0x22E1F)`、`main` 返回 0。

## 6. 经验沉淀

- 触发条件：选型/搭建交叉编译工具链，且团队多人需要复现同一构建 #skill候选
- 排查步骤：
  1. 先盘点本机既有环境（MSYS2/Node/WSL/磁盘），再给候选路线，不要默认从源码构建（Windows 下 riscv-gnu-toolchain 源码构建需 Linux，数小时）
  2. 团队项目**只允许一条工具链路线**，版本号与安装命令写进仓库 README，作为唯一权威
  3. "冒烟程序覆盖了某扩展"不能只看源码——`-O2` 强度削减会删掉 mul/div，必须**反汇编验证指令真实存在**
  4. 工具链输出的机器码要与仓库内独立实现（`verify_rv32i.py`）交叉核对，避免"工具链自证"
- 适用范围：换题目/换板卡/换到 Vitis、Quartus 等工具同样成立
