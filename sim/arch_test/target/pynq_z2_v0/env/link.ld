/* link.ld —— arch-test 统一镜像链接脚本（PYNQ-Z2 自研 v0 核）
 * 地址空间：0x8000_0000 起 32KB（匹配核契约与 tb；双口预载同一镜像）
 * 入口：rvtest_entry_point（test 源文件里 .text.init 首个符号，复位 PC=0x8000_0000）
 */
OUTPUT_ARCH(riscv)
ENTRY(rvtest_entry_point)

MEMORY
{
    ram (rwx) : ORIGIN = 0x80000000, LENGTH = 32K
}

SECTIONS
{
    .text : {
        *(.text.init)
        *(.text)
        *(.text.*)
        *(.rodata)
        *(.rodata.*)
    } > ram

    .data : {
        *(.data)
        *(.data.*)
        *(.sdata)
        *(.sdata.*)
        *(.data.string)
    } > ram

    .tohost : {
        *(.tohost)
    } > ram

    .bss (NOLOAD) : {
        *(.bss)
        *(.bss.*)
        *(.sbss)
        *(.sbss.*)
        *(COMMON)
    } > ram
}
