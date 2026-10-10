"""CJK 字体子集生成（构建期工具，非运行时依赖）。

产出 `NotoSansSC-Subset.ttf`：Noto Sans SC 变量字体（OFL）子集，字符集 =
ASCII + GB2312 全集（一/二级汉字及全角区，6763 字）+ 常用符号（EXTRA）。
全量字体约 17MB 不随仓库分发；子集约 4MB 入库。

用法（需 fonttools，仅构建机安装）：
    py -m pip install --target sim/build/vision-client-deps fonttools
    set PYTHONPATH=<仓库路径下的 sim/build/vision-client-deps>
    py src/vision_client/assets/fonts/make_cjk_subset.py

首次运行从 jsDelivr 下载全量字体（可复现源）。若 M3 后期出现缺字（豆腐块）：
把所需字符补进 EXTRA（或改用全量字体）后重跑本脚本。
"""
from __future__ import annotations

import subprocess
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
FULL = HERE / "NotoSansSC-VF.ttf"
SUBSET = HERE / "NotoSansSC-Subset.ttf"
CHARS = HERE / "cjk_subset_chars.txt"
URL = "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/notosanssc/NotoSansSC%5Bwght%5D.ttf"

EXTRA = " ✓✔✗×÷±≤≥≈≠·—…“”‘’〇○●◎◆◇■□▲▼△▽☆★℃°Ωμ∑√∞"


def gb2312_chars():
    """GB2312 全集（0xA1A1–0xF7FE 中可解码部分：符号区 + 一/二级汉字）。"""
    out = []
    for hi in range(0xA1, 0xF8):
        for lo in range(0xA1, 0xFF):
            try:
                out.append(bytes([hi, lo]).decode("gb2312"))
            except UnicodeDecodeError:
                pass
    return out


def main():
    if not FULL.exists():
        print("downloading full font from jsDelivr ...")
        urllib.request.urlretrieve(URL, FULL)
        print("downloaded:", FULL.stat().st_size, "bytes")
    chars = "".join(chr(c) for c in range(0x20, 0x7F)) + "".join(gb2312_chars()) + EXTRA
    CHARS.write_text(chars, encoding="utf-8")
    subprocess.run([sys.executable, "-m", "fontTools.subset", str(FULL),
                    f"--text-file={CHARS}", f"--output-file={SUBSET}",
                    "--layout-features=*", "--name-IDs=*", "--drop-tables+=DSIG"],
                   check=True)
    print("PASS:", SUBSET.name, SUBSET.stat().st_size, "bytes,", len(chars), "chars")


if __name__ == "__main__":
    main()
