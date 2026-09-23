/* core_portme.h —— CoreMark 移植层配置（自研 RV32IM 核，裸机无 libc）
 * 契约：docs/coremark_tb_contract.md §4.1（配置冻结）/§3.3（计时计数器）/§4.3（观测块）
 * 位置：本文件属"允许改动"的移植层；vendor/ 内算法文件与 coremark.h 禁止改动
 */
#ifndef CORE_PORTME_H
#define CORE_PORTME_H

/* ---- 平台能力（全整数路径，不引 libc / 浮点 / 时间库） ---- */
#define HAS_FLOAT  0
#define HAS_TIME_H 0
#define USE_CLOCK  0
#define HAS_STDIO  0
#define HAS_PRINTF 0

#ifndef FLAGS_STR
#define FLAGS_STR "-O2 -march=rv32im -mabi=ilp32 (src/riscv_fw/Makefile)"
#endif
#define COMPILER_VERSION "riscv32-unknown-elf-gcc " __VERSION__
#define COMPILER_FLAGS   FLAGS_STR
#define MEM_LOCATION     "static DMEM"

/* ---- 数据宽度（ee_ptr_int 必须容纳指针，否则 CoreMark 结果会错） ---- */
typedef signed short   ee_s16;
typedef unsigned short ee_u16;
typedef signed int     ee_s32;
typedef float          ee_f32; /* 不使用：HAS_FLOAT=0 且 MATDAT_INT=1 */
typedef unsigned char  ee_u8;
typedef unsigned int   ee_u32;
typedef ee_u32         ee_ptr_int;
typedef ee_u32         ee_size_t; /* 不引 stddef.h，裸机无 libc */
#define NULL ((void *)0)
#define align_mem(x) (void *)(4 + (((ee_ptr_int)(x)-1) & ~3))

/* ---- 计时（契约 §3.3 提案地址；仿真与板上须同语义：32 位自由运行、同拍读） ---- */
#define CORETIMETYPE ee_u32
typedef ee_u32 CORE_TICKS;
#ifndef PORT_TIMER_ADDR
#define PORT_TIMER_ADDR 0x80008000u /* 提案值，待 RTL 线确认后随契约 §3.3 冻结 */
#endif
#ifndef PORT_CLOCK_HZ
#define PORT_CLOCK_HZ 100000000u /* 100 MHz 标称；只影响秒数换算，不影响 CoreMark/MHz */
#endif
#define EE_TICKS_PER_SEC PORT_CLOCK_HZ

/* ---- seeds / 内存 / 主函数（契约 §4.1 冻结 profile） ---- */
#define SEED_METHOD       SEED_VOLATILE
#define MEM_METHOD        MEM_STATIC
#define MULTITHREAD       1
#define MAIN_HAS_NOARGC   1
#define MAIN_HAS_NORETURN 0 /* 必须 0：start.S 用 a0 = main 返回值写 tohost_exit */

/* 2K performance profile 选择（TOTAL_DATA_SIZE=2000 由编译宏给出） */
#ifndef TOTAL_DATA_SIZE
#define TOTAL_DATA_SIZE 2000
#endif
#if !defined(PROFILE_RUN) && !defined(PERFORMANCE_RUN) && !defined(VALIDATION_RUN)
#if (TOTAL_DATA_SIZE == 1200)
#define PROFILE_RUN 1
#elif (TOTAL_DATA_SIZE == 2000)
#define PERFORMANCE_RUN 1
#else
#define VALIDATION_RUN 1
#endif
#endif

/* ---- 官方框架需要的类型与声明 ---- */
extern ee_u32 default_num_contexts;

typedef struct CORE_PORTABLE_S
{
    ee_u8 portable_id;
} core_portable;

void portable_init(core_portable *p, int *argc, char *argv[]);
void portable_fini(core_portable *p);

int ee_printf(const char *fmt, ...);

/* ---- 本核扩展：结果导出钩子（core_main.c 末尾调用；契约 §4.3/§4.4） ---- */
void port_results_export(ee_u32 iterations,
                         ee_u16 seedcrc,
                         ee_u16 crclist,
                         ee_u16 crcmatrix,
                         ee_u16 crcstate,
                         ee_u16 crcfinal,
                         ee_s32 errors_raw);

#endif /* CORE_PORTME_H */
