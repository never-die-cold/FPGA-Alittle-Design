/* core_portme.c（host 版）—— CoreMark golden 复算用 PC 宿主移植层
 * 契约：docs/coremark.md §5.2（golden 生成）；profile 与 RISC-V 档完全一致
 */
#include "coremark.h"
#include "core_portme.h"

#include <stdarg.h>
#include <stdio.h>

/* 官方 seeds 通道（host 可直接用 .data 初值） */
volatile ee_s32 seed1_volatile = 0x0;
volatile ee_s32 seed2_volatile = 0x0;
volatile ee_s32 seed3_volatile = 0x66;
volatile ee_s32 seed4_volatile = ITERATIONS;
volatile ee_s32 seed5_volatile = 0;

/* 时间桩：CRC 与时间无关；get_time 返回 0，time_in_secs 恒 0（触发官方 <10s 检查，仅作对照） */
static ee_u32 host_ticks_marker;

void start_time(void)
{
    host_ticks_marker = 0;
}

void stop_time(void)
{
    host_ticks_marker = 1;
}

CORE_TICKS get_time(void)
{
    return (CORE_TICKS)host_ticks_marker; /* 0 或 1，仅占位 */
}

secs_ret time_in_secs(CORE_TICKS ticks)
{
    (void)ticks;
    return 0;
}

ee_u32 default_num_contexts = 1;

int ee_printf(const char *fmt, ...)
{
    va_list ap;
    va_start(ap, fmt);
    vprintf(fmt, ap);
    va_end(ap);
    return 0;
}

void portable_init(core_portable *p, int *argc, char *argv[])
{
    (void)argc;
    (void)argv;
    p->portable_id = 1;
}

void portable_fini(core_portable *p)
{
    p->portable_id = 0;
}

void port_results_export(ee_u32 iterations,
                         ee_u16 seedcrc,
                         ee_u16 crclist,
                         ee_u16 crcmatrix,
                         ee_u16 crcstate,
                         ee_u16 crcfinal,
                         ee_s32 errors_raw)
{
    printf("GOLDEN iter=%u seedcrc=0x%04x crclist=0x%04x crcmatrix=0x%04x crcstate=0x%04x crcfinal=0x%04x errors=%d\n",
           (unsigned)iterations,
           (unsigned)seedcrc,
           (unsigned)crclist,
           (unsigned)crcmatrix,
           (unsigned)crcstate,
           (unsigned)crcfinal,
           (int)errors_raw);
}
