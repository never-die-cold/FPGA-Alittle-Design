# RV32IM 冒烟固件启动代码：初始化栈指针 -> 清零 .bss -> 调用 main -> 结果写 tohost
# tohost 为 riscv-tests 风格观测点，供仿真/上板 testbench 读取

    .section .text.init
    .globl _start
_start:
    la      sp, _stack_top

    la      t0, __bss_start
    la      t1, __bss_end
1:
    bgeu    t0, t1, 2f
    sw      zero, 0(t0)
    addi    t0, t0, 4
    j       1b
2:
    call    main

    la      t0, tohost_exit
    sw      a0, 0(t0)
3:
    j       3b

    .section .tohost, "aw", @progbits
    .align  3
    .globl  tohost
tohost:
    .word   0
    .globl  tohost_exit
tohost_exit:
    .word   0
