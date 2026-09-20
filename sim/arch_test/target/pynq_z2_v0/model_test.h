// model_test.h —— riscv-arch-test 目标宏（PYNQ-Z2 自研 v0 核，RV32I）
// 依据：riscv-arch-test old-framework-2.x 的 example-target；本核无 IO/中断/特权支持
// 约定：签名区间 [begin_signature, end_signature)；HALT = 自旋（由 tb 跑固定周期后比对）
#ifndef _MODEL_TEST_H
#define _MODEL_TEST_H

#define RVMODEL_DATA_SECTION            \
    .pushsection .tohost,"aw",@progbits;\
    .align 3; .global tohost; tohost: .word 0;     \
    .align 3; .global fromhost; fromhost: .word 0;\
    .popsection;

// 停机：死循环自旋；tb 跑固定周期后读签名区
#define RVMODEL_HALT \
    self_loop: j self_loop;

// 启动：无特殊初始化（统一镜像，tb 已预载数据）
#define RVMODEL_BOOT

// 签名区起止（16 字节对齐为 arch-test 要求）
#define RVMODEL_DATA_BEGIN \
    .align 4; .global begin_signature; begin_signature:

#define RVMODEL_DATA_END \
    .align 4; .global end_signature; end_signature: \
    RVMODEL_DATA_SECTION

// 无外设：IO 宏全部为空实现（只定义 RVMODEL_* 新名，避免触发套件的 deprecated 别名告警）
#define RVMODEL_IO_WRITE_STR(_SP, _STR)
#define RVMODEL_IO_ASSERT_GPR_EQ(_SP, _R, _I)
#define RVMODEL_IO_ASSERT_SFPR_EQ(_F, _R, _I)
#define RVMODEL_IO_ASSERT_DFPR_EQ(_D, _R, _I)

// 无中断支持（I 子集测试不触发）
#define RVMODEL_SET_MSW_INT
#define RVMODEL_CLEAR_MSW_INT
#define RVMODEL_CLEAR_MTIMER_INT
#define RVMODEL_CLEAR_MEXT_INT

#endif // _MODEL_TEST_H
