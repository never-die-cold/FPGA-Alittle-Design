#!/usr/bin/env python3
# coremark_score.py —— 解析 CoreMark 回归日志，输出 score/CPI 与 metrics 填报行
# 用法：python data/scripts/coremark_score.py <run_coremark.log>
# 口径（docs/coremark.md §5.3/§5.4）：
#   ticks = t1 - t0（移植层 start/stop 计时窗口，非 tb 全局周期）
#   CoreMark/MHz = iterations × 1e6 / ticks（仿真外推口径；短迭代不满足官方 ≥10s）
#   CPI = cycles / instrs（tb 全局口径，含 muldiv 多拍与分支气泡，仅作体检不参与评分）
#   errors_raw 为官方 <10s 错误计数，只作证据不作判据（§5.4）
import re
import sys

USAGE = "用法：python data/scripts/coremark_score.py <run_coremark.log>"

OBS_RE = re.compile(
    r"obs iter=(\d+) seedcrc=0x([0-9a-fA-F]+) crclist=0x([0-9a-fA-F]+) "
    r"crcmatrix=0x([0-9a-fA-F]+) crcstate=0x([0-9a-fA-F]+) crcfinal=0x([0-9a-fA-F]+) "
    r"t0=(\d+) t1=(\d+) errors=(\d+)"
)
CORE_RE = re.compile(r"PASS: coremark cycles=(\d+) instrs=(\d+) bubbles=(\d+) cpi=(\d+)\.(\d+)")


def main(argv):
    if len(argv) != 2:
        sys.stderr.write(USAGE + "\n")
        return 2
    with open(argv[1], encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    obs = OBS_RE.search(text)
    core = CORE_RE.search(text)
    if not obs or not core:
        print("FAIL: 日志缺少 obs/PASS 行（是否为 PASS 日志？）")
        return 1
    iters, seedcrc, crclist, crcmatrix, crcstate, crcfinal, t0, t1, errors = obs.groups()
    cycles, instrs, bubbles, cpi_i, cpi_f = core.groups()

    iters, t0, t1 = int(iters), int(t0), int(t1)
    cycles, instrs, bubbles = int(cycles), int(instrs), int(bubbles)
    ticks = t1 - t0
    score_mhz = iters * 1_000_000 / ticks
    cpi = cycles / instrs if instrs else 0.0

    print("== CoreMark 解析：%s" % argv[1])
    print("iter=%d seedcrc=0x%s crclist=0x%s crcmatrix=0x%s crcstate=0x%s crcfinal=0x%s errors_raw=%s"
          % (iters, seedcrc, crclist, crcmatrix, crcstate, crcfinal, errors))
    print("计时窗口 ticks=%d（t0=%d t1=%d）" % (ticks, t0, t1))
    print("tb 全局：cycles=%d instrs=%d bubbles=%d cpi=%.3f（体检口径）" % (cycles, instrs, bubbles, cpi))
    print("CoreMark/MHz = %d × 1e6 / %d = %.3f（仿真外推口径）" % (iters, ticks, score_mhz))
    print("metrics.csv 建议行：")
    print("RISC-V 核 CoreMark/MHz,核级基准(仿真外推),%.3f,CoreMark/MHz,"
          "iverilog；coremark 2K/32 迭代；ticks=%d；详见日志,%d,%s"
          % (score_mhz, ticks, iters, argv[1].replace("\\", "/")))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
