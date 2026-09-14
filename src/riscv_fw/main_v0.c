/* v0 核（RV32I 子集）冒烟程序：不依赖 libc，不使用 M 扩展。
 * volatile 数组强制真实的 lw/sw（防编译器标量折叠），循环练习分支。
 * 预期：tohost = 13，返回 0。
 * RV32IM 全量冒烟（含 mul/divu）见 main.c，待 Part A 收尾补 M 后启用。
 */
extern volatile unsigned int tohost;

int main(void)
{
    volatile unsigned int buf[4];
    unsigned int seed = tohost;
    unsigned int sum = 0;

    buf[0] = seed + 1u;
    buf[1] = seed + 2u;
    buf[2] = seed + 4u;
    buf[3] = seed + 6u;

    for (int i = 0; i < 4; i++)
        sum += buf[i];

    tohost = sum;
    return (sum == 13u) ? 0 : 1;
}
