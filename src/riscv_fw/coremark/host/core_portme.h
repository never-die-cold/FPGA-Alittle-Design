/* core_portme.h（host 版）—— CoreMark golden 复算用 PC 宿主移植层
 * 用途：同源同 profile 在 PC 上运行，复算 crcfinal（契约 §5.2 golden 生成）
 * 差异：无 MMIO/计数器，get_time 返回 0（CRC 与时间无关）；ee_printf 走 stdout
 */
#ifndef CORE_PORTME_H
#define CORE_PORTME_H

#include <stddef.h>
#include <stdint.h>

#define HAS_FLOAT  0
#define HAS_TIME_H 0
#define USE_CLOCK  0
#define HAS_STDIO  0
#define HAS_PRINTF 0

#define COMPILER_VERSION "host-gcc " __VERSION__
#ifndef FLAGS_STR
#define FLAGS_STR "-O2 (host)"
#endif
#define COMPILER_FLAGS FLAGS_STR
#define MEM_LOCATION   "static host"

typedef int16_t  ee_s16;
typedef uint16_t ee_u16;
typedef int32_t  ee_s32;
typedef float    ee_f32;
typedef uint8_t  ee_u8;
typedef uint32_t  ee_u32;
typedef uintptr_t ee_ptr_int; /* host 指针宽度（64 位），与 RISC-V 档的 ee_u32 不同 */
typedef size_t    ee_size_t;
#define NULL ((void *)0)
#define align_mem(x) (void *)(4 + (((ee_ptr_int)(x)-1) & ~3))

#define CORETIMETYPE ee_u32
typedef ee_u32 CORE_TICKS;
#define EE_TICKS_PER_SEC 100000000u

#ifndef TOTAL_DATA_SIZE
#define TOTAL_DATA_SIZE 2000
#endif
#if !defined(PROFILE_RUN) && !defined(PERFORMANCE_RUN) && !defined(VALIDATION_RUN)
#define PERFORMANCE_RUN 1
#endif

#define SEED_METHOD       SEED_VOLATILE
#define MEM_METHOD        MEM_STATIC
#define MULTITHREAD       1
#define MAIN_HAS_NOARGC   1
#define MAIN_HAS_NORETURN 0

extern ee_u32 default_num_contexts;

typedef struct CORE_PORTABLE_S
{
    ee_u8 portable_id;
} core_portable;

void portable_init(core_portable *p, int *argc, char *argv[]);
void portable_fini(core_portable *p);

int ee_printf(const char *fmt, ...);

void port_results_export(ee_u32 iterations,
                         ee_u16 seedcrc,
                         ee_u16 crclist,
                         ee_u16 crcmatrix,
                         ee_u16 crcstate,
                         ee_u16 crcfinal,
                         ee_s32 errors_raw);

#endif /* CORE_PORTME_H */
