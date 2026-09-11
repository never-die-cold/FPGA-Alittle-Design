/* RV32IM 冒烟程序：验证工具链闭环（编译 -> elf -> 反汇编 -> hex），不依赖 libc。
 * 操作数由 volatile 读取派生，确保 RV32IM 的 mul/mulhu/divu 真实出现在反汇编中。
 * 预期执行结果（tohost 初值 0 时）：a=7, b=3, prod=21, 1000000/7=142857 余 1，
 * tohost 最终写入 142879；返回 0 表示走通预期路径。
 */
extern volatile unsigned int tohost;

int main(void)
{
    unsigned int seed = tohost;
    unsigned int a = seed + 7u;
    unsigned int b = seed + 3u;
    unsigned int prod = a * b;
    unsigned int quot = 1000000u / a;
    unsigned int rem = 1000000u % a;

    tohost = prod + quot + rem;
    return (prod == 21u && quot == 142857u && rem == 1u) ? 0 : 1;
}
