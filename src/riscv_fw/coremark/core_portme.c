/* core_portme.c —— CoreMark 移植层实现（自研 RV32IM 核，裸机无 libc）
 * 契约：docs/coremark_tb_contract.md §3.3（计时）/§4.3（观测块字段表）/§4.4（结束协议）
 * 结束协议：导出钩子写观测块 + tohost=crcfinal → main 返回 0 → start.S 写 tohost_exit=0 → 自旋
 */
#include "coremark.h"
#include "core_portme.h"

/* ---- 官方 seeds 通道（契约 §4.1：2K performance profile，seeds 0/0/0x66） ----
 * 注意：本核 DMEM 上电全 0（contract §3.2），.data 初值不会被预载；
 * 因此 seeds 不能靠 .data 初始化，统一在 portable_init（官方在读 seeds 之前调用）里赋值。
 */
volatile ee_s32 seed1_volatile;
volatile ee_s32 seed2_volatile;
volatile ee_s32 seed3_volatile;
volatile ee_s32 seed4_volatile;
volatile ee_s32 seed5_volatile;

/* ---- 计时：读 SoC 计时计数器（同拍、32 位自由运行；契约 §3.3） ---- */
static ee_u32 port_t0, port_t1;

static ee_u32 port_timer_read(void)
{
    return *(volatile ee_u32 *)PORT_TIMER_ADDR;
}

void start_time(void)
{
    port_t0 = port_timer_read();
}

void stop_time(void)
{
    port_t1 = port_timer_read();
}

CORE_TICKS get_time(void)
{
    return (CORE_TICKS)(port_t1 - port_t0); /* 无符号模 2^32，契约 §3.3 */
}

secs_ret time_in_secs(CORE_TICKS ticks)
{
    return ticks / (secs_ret)EE_TICKS_PER_SEC; /* HAS_FLOAT=0：整数口径，仅用于官方 10s 检查 */
}

ee_u32 default_num_contexts; /* 值在 portable_init 里赋 1（避开 .data 预载依赖） */

/* ---- 无控制台：ee_printf 置空；结果走观测块 + tohost（契约 §4.3） ---- */
int ee_printf(const char *fmt, ...)
{
    (void)fmt;
    return 0;
}

void portable_init(core_portable *p, int *argc, char *argv[])
{
    (void)argc;
    (void)argv;

    /* 2K performance profile 冻结值（契约 §4.1）；此处赋值以避开 .data 预载依赖 */
    seed1_volatile = 0x0;
    seed2_volatile = 0x0;
    seed3_volatile = 0x66;
    seed4_volatile = ITERATIONS; /* 显式迭代数，禁止触发官方自动标定（需 ≥10s 计时） */
    seed5_volatile = 0;
    default_num_contexts = 1;

    p->portable_id = 1;
}

void portable_fini(core_portable *p)
{
    p->portable_id = 0;
}

/* ---- 结果导出钩子（core_main.c 末尾调用；字段表 = 契约 §4.3，顺序 = 契约 §4.4） ---- */
#define PORT_OBS_BASE   0x80007F00u /* 观测块基址（字索引 0x1FC0），契约 §3.2/§4.3 */
#define PORT_MAGIC_ID   0x434D4B31u /* "CMK1"，块首写 */
#define PORT_MAGIC_DONE 0x444F4E45u /* "DONE"，块尾最后写（封口） */

extern volatile ee_u32 tohost;

void port_results_export(ee_u32 iterations,
                         ee_u16 seedcrc,
                         ee_u16 crclist,
                         ee_u16 crcmatrix,
                         ee_u16 crcstate,
                         ee_u16 crcfinal,
                         ee_s32 errors_raw)
{
    volatile ee_u32 *obs = (volatile ee_u32 *)PORT_OBS_BASE;

    obs[0]  = PORT_MAGIC_ID;
    obs[1]  = iterations;
    obs[2]  = seedcrc;
    obs[3]  = crclist;
    obs[4]  = crcmatrix;
    obs[5]  = crcstate;
    obs[6]  = crcfinal;
    obs[7]  = port_t0;
    obs[8]  = port_t1;
    obs[9]  = (ee_u32)errors_raw;
    obs[10] = PORT_MAGIC_DONE; /* 封口：必须先于 tohost_exit（由 start.S 后续写） */
    tohost  = crcfinal;        /* 契约 §4.4 步骤 3：tohost = crcfinal */
}
