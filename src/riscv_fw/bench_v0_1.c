/* benchmark v0.1：固定种子的整数/数组/分支/位运算混合负载。 */
extern volatile unsigned int tohost;

#define EXPECTED_CHECKSUM 0x1385CBD1u

static volatile unsigned int data_words[16];

int main(void)
{
    unsigned int x = 0x12345678u;
    unsigned int sum = 0u;

    for (unsigned int i = 0; i < 64u; ++i) {
        x = x * 1664525u + 1013904223u;
        unsigned int value = x ^ (x >> 16);
        data_words[i & 15u] = value;
        if (x & 1u)
            sum += value + i;
        else
            sum ^= value;
    }

    for (unsigned int i = 0; i < 16u; ++i) {
        sum = (sum << 5) | (sum >> 27);
        sum ^= data_words[i] + i * 0x9E3779B9u;
    }

    sum &= 0x7FFFFFFFu;
    tohost = sum;
    return (sum == EXPECTED_CHECKSUM) ? 0 : 1;
}
