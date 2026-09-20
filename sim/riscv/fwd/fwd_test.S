# fwd_test.S —— 数据冒险（转发专项）契约级测试程序
# 用法：与 src/riscv_fw/start.S + link.ld 链接（-march=rv32i），main 返回 a0=0 表示程序自检通过
# 观测约定（sim/riscv/tb_core_fwd.v）：
#   dmem[0x8000_3E00] = 阶段标记（101..108 = 各阶段起止；200 = 程序结束），tb 在标记写入拍快照气泡计数
#   dmem[0x8000_3800..] = 各阶段结果，tb 与期望常数逐一比对
# 说明：同一程序供 v0（无停顿）与 v1（转发/停顿）复用，气泡期望值由 tb 参数给出
#       （v0 默认：数据阶段 0，taken 分支阶段 = taken 次数 5）

    .equ MARK,   0x80003E00
    .equ RESULT, 0x80003800

    .text
    .globl main
main:
    # ================= 阶段 A：R 型连读（纯 RAW 依赖链，无分支） =================
    li   x5, 101
    li   x6, MARK
    sw   x5, 0(x6)          # 标记：A 开始

    li   x5, 1
    li   x6, 2
    add  x7,  x5, x6        # x7  = 3
    add  x8,  x7, x7        # x8  = 6   (RAW x7)
    add  x9,  x8, x7        # x9  = 9   (RAW x8, x7)
    sub  x11, x9, x8        # x11 = 3   (RAW x9, x8)
    xor  x12, x11, x9       # x12 = 10  (RAW x11, x9)
    or   x13, x12, x8       # x13 = 14  (RAW x12, x8)
    and  x14, x13, x9       # x14 = 8   (RAW x13, x9)
    sll  x15, x14, x5       # x15 = 16  (RAW x14)
    srl  x16, x15, x6       # x16 = 4   (RAW x15)
    add  x17, x16, x14      # x17 = 12  (RAW x16, x14)

    li   x5, RESULT
    sw   x7,  0(x5)
    sw   x8,  4(x5)
    sw   x9,  8(x5)
    sw   x11, 12(x5)
    sw   x12, 16(x5)
    sw   x13, 20(x5)
    sw   x14, 24(x5)
    sw   x15, 28(x5)
    sw   x16, 32(x5)
    sw   x17, 36(x5)

    li   x5, 102
    li   x6, MARK
    sw   x5, 0(x6)          # 标记：A 结束

    # ================= 阶段 B：lw → 运算连读（load-use，无分支） =================
    li   x5, 103
    li   x6, MARK
    sw   x5, 0(x6)          # 标记：B 开始

    li   x5, 100
    sw   x5, 256(x0)        # dmem[0x100] = 100

    lw   x6,  256(x0)       # x6  = 100
    add  x7,  x6, x5        # x7  = 200 (load-use)
    lw   x8,  256(x0)       # x8  = 100
    add  x9,  x8, x7        # x9  = 300 (load-use)
    lw   x11, 256(x0)       # x11 = 100
    add  x12, x11, x9       # x12 = 400 (load-use)
    sub  x13, x12, x11      # x13 = 300 (RAW x12，可转发)
    lw   x14, 256(x0)       # x14 = 100
    xor  x15, x14, x13      # x15 = 328 (load-use)

    li   x5, RESULT
    sw   x7,  64(x5)
    sw   x9,  68(x5)
    sw   x12, 72(x5)
    sw   x13, 76(x5)
    sw   x15, 80(x5)

    li   x5, 104
    li   x6, MARK
    sw   x5, 0(x6)          # 标记：B 结束

    # ================= 阶段 C：taken 分支/跳转（v0 每次 1 拍气泡，共 5 次） =================
    li   x5, 105
    li   x6, MARK
    sw   x5, 0(x6)          # 标记：C 开始

    li   x5, 0
    li   x6, 4
C_loop:
    addi x5, x5, 1
    bne  x5, x6, C_loop     # taken 3 次（第 4 次不跳）
    jal  x7, C_after_jal    # taken 1 次
C_after_jal:
    la   x8, C_after_jalr
    jalr x9, 0(x8)          # taken 1 次
C_after_jalr:
    li   x6, RESULT
    sw   x5, 96(x6)         # 记录循环计数（期望 4）

    li   x5, 106
    li   x6, MARK
    sw   x5, 0(x6)          # 标记：C 结束

    # ================= 阶段 D：not-taken 分支（0 气泡；错跳则写错误标记） =================
    li   x5, 107
    li   x6, MARK
    sw   x5, 0(x6)          # 标记：D 开始

    li   x5, 1
    li   x6, 2
    beq  x5, x6, D_err      # 1==2 假
    bne  x5, x5, D_err      # 1!=1 假
    blt  x6, x5, D_err      # 2<1  假（signed）
    bge  x5, x6, D_err      # 1>=2 假
    bltu x6, x5, D_err      # 2<1  假（unsigned）
    bgeu x5, x6, D_err      # 1>=2 假

    li   x5, 108
    li   x6, MARK
    sw   x5, 0(x6)          # 标记：D 结束（正常路径）
    j    D_done

D_err:
    li   a0, 1              # 不应到达：任一 not-taken 分支被误跳
    li   x6, RESULT
    sw   a0, 100(x6)

D_done:
    li   a0, 0
    li   x6, MARK
    li   x5, 200
    sw   x5, 0(x6)          # 标记：程序结束
    ret
