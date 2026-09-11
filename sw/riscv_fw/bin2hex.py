# -*- coding: utf-8 -*-
"""二进制转 $readmemh 十六进制（32 位小端字，用于 BRAM 预载）。

用法: python bin2hex.py <input.bin> <output.hex>
"""
import sys


def bin_to_hex(src, dst):
    with open(src, "rb") as f:
        data = f.read()
    data += b"\x00" * ((-len(data)) % 4)
    words = [data[i:i + 4] for i in range(0, len(data), 4)]
    with open(dst, "w") as f:
        for w in words:
            f.write("%08x\n" % int.from_bytes(w, "little"))
    return len(data), len(words)


def main():
    if len(sys.argv) != 3:
        print("用法: python bin2hex.py <input.bin> <output.hex>")
        return 1
    size, words = bin_to_hex(sys.argv[1], sys.argv[2])
    print("%s -> %s: %d bytes, %d words (32-bit little-endian)"
          % (sys.argv[1], sys.argv[2], size, words))
    return 0


if __name__ == "__main__":
    sys.exit(main())
