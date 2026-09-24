/* link_coremark.ld —— CoreMark 裸机链接脚本（32KB 哈佛布局，IMEM/DMEM 同基址）
 * 契约：docs/coremark.md §4.2
 * 布局要点（2026-09-23）：
 *   - .text/.data/.bss 在低区（实测 ~13KB，须止于 tohost 区前）
 *   - tohost/tohost_exit 固定 0x8000_3FF0 不可移动（design_v0 §3.3）
 *   - 栈顶 0x8000_7F00（紧邻观测块下沿），向下生长进 0x4000-0x7EFF 空闲区（~16KB）
 *   - 观测块 0x8000_7F00-0x8000_7FFF 全保留（契约 §4.3）
 */
OUTPUT_ARCH(riscv)
ENTRY(_start)

MEMORY
{
    BRAM (rwxa) : ORIGIN = 0x80000000, LENGTH = 32K
}

SECTIONS
{
    .text : {
        KEEP(*(.text.init))
        *(.text .text.*)
        *(.rodata .rodata.*)
    } > BRAM

    .data : {
        *(.data .data.*)
        *(.sdata .sdata.*)
    } > BRAM

    .bss (NOLOAD) : {
        __bss_start = .;
        *(.bss .bss.*)
        *(.sbss .sbss.*)
        *(COMMON)
        __bss_end = .;
    } > BRAM

    .tohost 0x80003FF0 : {
        KEEP(*(.tohost))
    }

    /* 栈顶：观测块下沿；栈向下生长，不与 tohost（0x3FF0）及观测块（0x7F00）碰撞 */
    _stack_top = 0x80007F00;

    ASSERT(__bss_end <= 0x80003FF0, "data/bss 溢出进入 tohost 区")
}
