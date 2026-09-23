/* RV32IM 冒烟固件链接脚本：代码/数据基址 0x8000_0000，统一 32KB 地址范围 */

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

    ASSERT(__bss_end <= 0x80003FF0, "firmware sections overlap tohost")

    .tohost 0x80003FF0 : {
        KEEP(*(.tohost))
    }

    _stack_top = ORIGIN(BRAM) + LENGTH(BRAM);
}
