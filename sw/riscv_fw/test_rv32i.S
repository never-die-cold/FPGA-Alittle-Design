# test_rv32i.S —— RV32I 逐指令自检（作为 main 被 start.S 调用）
# 约定：a0 = 失败用例编号（失败即跳 L_done）；全部通过时 a0=0 后返回
# 编译期由 -march=rv32i 保证不含 M/A/C 扩展
# 覆盖：R/I 型算术逻辑移位、U 型、访存（sw/sh/sb/lw/lh/lhu/lb/lbu）、
#       6 条分支（taken 与 not-taken 双向）、jal/jalr、x0 硬连线

    .text
    .globl main
main:
    # ---- 1. add ----
    li      a0, 1
    li      x5, 7
    li      x6, 5
    add     x7, x5, x6
    li      x8, 12
    bne     x7, x8, L_done

    # ---- 2. sub ----
    li      a0, 2
    li      x5, 7
    li      x6, 5
    sub     x7, x5, x6
    li      x8, 2
    bne     x7, x8, L_done

    # ---- 3. sll ----
    li      a0, 3
    li      x5, 1
    li      x6, 5
    sll     x7, x5, x6
    li      x8, 32
    bne     x7, x8, L_done

    # ---- 4. slt（有符号：-1 < 0）----
    li      a0, 4
    li      x5, -1
    li      x6, 0
    slt     x7, x5, x6
    li      x8, 1
    bne     x7, x8, L_done

    # ---- 5. sltu（无符号：1 < 0xFFFFFFFF）----
    li      a0, 5
    li      x5, 1
    li      x6, -1
    sltu    x7, x5, x6
    li      x8, 1
    bne     x7, x8, L_done

    # ---- 6. xor ----
    li      a0, 6
    li      x5, 0xF0F0
    li      x6, 0x0FF0
    xor     x7, x5, x6
    li      x8, 0xFF00
    bne     x7, x8, L_done

    # ---- 7. srl（逻辑右移）----
    li      a0, 7
    li      x5, 0xF0000000
    li      x6, 4
    srl     x7, x5, x6
    li      x8, 0x0F000000
    bne     x7, x8, L_done

    # ---- 8. sra（算术右移）----
    li      a0, 8
    li      x5, 0xF0000000
    li      x6, 4
    sra     x7, x5, x6
    li      x8, 0xFF000000
    bne     x7, x8, L_done

    # ---- 9. or ----
    li      a0, 9
    li      x5, 0xF0F0
    li      x6, 0x0F0F
    or      x7, x5, x6
    li      x8, 0xFFFF
    bne     x7, x8, L_done

    # ---- 10. and ----
    li      a0, 10
    li      x5, 0xF0F0
    li      x6, 0xFF00
    and     x7, x5, x6
    li      x8, 0xF000
    bne     x7, x8, L_done

    # ---- 11. addi（含负立即数）----
    li      a0, 11
    li      x5, 7
    addi    x7, x5, -3
    li      x8, 4
    bne     x7, x8, L_done

    # ---- 12. slti ----
    li      a0, 12
    li      x5, -1
    slti    x7, x5, 0
    li      x8, 1
    bne     x7, x8, L_done

    # ---- 13. sltiu ----
    li      a0, 13
    li      x5, 1
    sltiu   x7, x5, 2
    li      x8, 1
    bne     x7, x8, L_done

    # ---- 14. xori ----
    li      a0, 14
    li      x5, 0xF0
    xori    x7, x5, 0xFF
    li      x8, 0x0F
    bne     x7, x8, L_done

    # ---- 15. ori ----
    li      a0, 15
    li      x5, 0xF0
    ori     x7, x5, 0x0F
    li      x8, 0xFF
    bne     x7, x8, L_done

    # ---- 16. andi ----
    li      a0, 16
    li      x5, 0xFF
    andi    x7, x5, 0x0F
    li      x8, 0x0F
    bne     x7, x8, L_done

    # ---- 17. slli ----
    li      a0, 17
    li      x5, 1
    slli    x7, x5, 7
    li      x8, 0x80
    bne     x7, x8, L_done

    # ---- 18. srli ----
    li      a0, 18
    li      x5, 0x80000000
    srli    x7, x5, 7
    li      x8, 0x01000000
    bne     x7, x8, L_done

    # ---- 19. srai ----
    li      a0, 19
    li      x5, 0x80000000
    srai    x7, x5, 7
    li      x8, 0xFF000000
    bne     x7, x8, L_done

    # ---- 20. lui ----
    li      a0, 20
    lui     x5, 0x12345
    li      x6, 0x12345000
    bne     x5, x6, L_done

    # ---- 21. auipc（x5 应为本条指令地址）----
    li      a0, 21
L_auipc:
    auipc   x5, 0
    la      x6, L_auipc
    bne     x5, x6, L_done

    # ---- 22. lw（sw 往返）----
    li      a0, 22
    li      x5, 0x12345678
    sw      x5, -16(sp)
    lw      x6, -16(sp)
    bne     x5, x6, L_done

    # ---- 23. lh（符号扩展）----
    li      a0, 23
    li      x5, 0xFFFF8000
    sw      x5, -16(sp)
    lh      x6, -16(sp)
    li      x7, 0xFFFF8000
    bne     x6, x7, L_done

    # ---- 24. lhu（零扩展）----
    li      a0, 24
    lhu     x6, -16(sp)
    li      x7, 0x00008000
    bne     x6, x7, L_done

    # ---- 25. lb（符号扩展，低字节 0x80）----
    li      a0, 25
    li      x5, 0x00000080
    sw      x5, -16(sp)
    lb      x6, -16(sp)
    li      x7, 0xFFFFFF80
    bne     x6, x7, L_done

    # ---- 26. lbu（零扩展）----
    li      a0, 26
    lbu     x6, -16(sp)
    li      x7, 0x00000080
    bne     x6, x7, L_done

    # ---- 27. sw ----
    li      a0, 27
    li      x5, 0x0BADF00D
    sw      x5, -16(sp)
    lw      x6, -16(sp)
    bne     x5, x6, L_done

    # ---- 28. sh（高半字保留）----
    li      a0, 28
    li      x5, 0xFFFF0000
    sw      x5, -16(sp)
    li      x5, 0x0000ABCD
    sh      x5, -16(sp)
    lw      x6, -16(sp)
    li      x7, 0xFFFFABCD
    bne     x6, x7, L_done

    # ---- 29. sb（仅改最低字节）----
    li      a0, 29
    li      x5, 0x000000FF
    sw      x5, -16(sp)
    li      x5, 0x00000012
    sb      x5, -16(sp)
    lw      x6, -16(sp)
    li      x7, 0x00000012
    bne     x6, x7, L_done

    # ---- 30. beq（taken + not-taken）----
    li      a0, 30
    li      x5, 5
    li      x6, 5
    beq     x5, x6, 1f
    j       L_done
1:  li      x5, 5
    li      x6, 6
    beq     x5, x6, L_done

    # ---- 31. bne ----
    li      a0, 31
    li      x5, 5
    li      x6, 6
    bne     x5, x6, 1f
    j       L_done
1:  li      x5, 5
    li      x6, 5
    bne     x5, x6, L_done

    # ---- 32. blt（taken + not-taken）----
    li      a0, 32
    li      x5, -1
    li      x6, 0
    blt     x5, x6, 1f
    j       L_done
1:  li      x5, 0
    li      x6, -1
    blt     x5, x6, L_done

    # ---- 33. bge ----
    li      a0, 33
    li      x5, 0
    li      x6, -1
    bge     x5, x6, 1f
    j       L_done
1:  li      x5, -1
    li      x6, 0
    bge     x5, x6, L_done

    # ---- 34. bltu（无符号：1 < 0xFFFFFFFF）----
    li      a0, 34
    li      x5, 1
    li      x6, -1
    bltu    x5, x6, 1f
    j       L_done
1:  li      x5, -1
    li      x6, 1
    bltu    x5, x6, L_done

    # ---- 35. bgeu ----
    li      a0, 35
    li      x5, -1
    li      x6, 1
    bgeu    x5, x6, 1f
    j       L_done
1:  li      x5, 1
    li      x6, -1
    bgeu    x5, x6, L_done

    # ---- 36. jal（用 x5 作 link，保护 ra）----
    li      a0, 36
    jal     x5, L_jal_target
L_jal_ret:
    j       L_done
L_jal_target:
    la      x7, L_jal_ret
    bne     x5, x7, L_done

    # ---- 37. jalr ----
    li      a0, 37
    la      x6, L_jalr_target
    jalr    x5, 0(x6)
L_jalr_ret:
    j       L_done
L_jalr_target:
    la      x7, L_jalr_ret
    bne     x5, x7, L_done

    # ---- 38. x0 硬连线（写入无效）----
    li      a0, 38
    addi    x0, x0, 5
    add     x5, x0, x0
    bne     x5, x0, L_done

L_pass:
    li      a0, 0
    ret

L_done:
    ret
