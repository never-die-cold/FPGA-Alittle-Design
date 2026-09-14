/* RV32IM 冒烟固件链接脚本：代码/数据基址 0x8000_0000（16K BRAM，后续随 SoC 外壳调整） */

OUTPUT_ARCH(riscv)
ENTRY(_start)

MEMORY
{
    BRAM (rwxa) : ORIGIN = 0x80000000, LENGTH = 16K
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

    . = ALIGN(16);
    . += 0x400;
    _stack_top = .;

    .tohost 0x80003FF0 : {
        KEEP(*(.tohost))
    }
}
