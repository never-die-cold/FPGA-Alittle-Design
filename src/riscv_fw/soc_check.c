/* SoC 端到端自检：DMEM 镜像预载、计时器读写和地址别名保护。 */
extern volatile unsigned int tohost;

#define TIMER_ADDR 0x80008000u
#define DMEM_BASE  0x80000000u
#define PASS_VALUE 0x534F4301u

static volatile unsigned int preload_word = 0x13579BDFu;

int main(void)
{
    volatile unsigned int *timer = (volatile unsigned int *)TIMER_ADDR;
    volatile unsigned int *dmem0 = (volatile unsigned int *)DMEM_BASE;
    volatile unsigned int work = 0;
    unsigned int mem0_before = *dmem0;
    unsigned int t0 = *timer;

    for (unsigned int i = 0; i < 16u; ++i)
        work += (i ^ 0x5Au);

    unsigned int t1 = *timer;
    *timer = 0xDEADBEEFu;
    unsigned int mem0_after = *dmem0;

    if (preload_word != 0x13579BDFu) {
        tohost = 0xBAD00001u;
        return 1;
    }
    if (t1 <= t0 || work == 0u) {
        tohost = 0xBAD00002u;
        return 2;
    }
    if (mem0_after != mem0_before) {
        tohost = 0xBAD00003u;
        return 3;
    }

    tohost = PASS_VALUE;
    return 0;
}
