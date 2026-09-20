#!/usr/bin/env bash
# fetch_arch_test.sh —— 下载 riscv-arch-test 套件（old-framework-2.x 分支，自带参考签名）
# 目的目录：sim/arch_test/suite（已加入 .gitignore，不入库）；可用 ARCH_TEST_DIR 覆盖
# 用法：bash sim/scripts/fetch_arch_test.sh
set -euo pipefail

repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
dest="${ARCH_TEST_DIR:-$repo/sim/arch_test/suite}"
branch="old-framework-2.x"

if [ -d "$dest/.git" ]; then
    echo "已存在：$dest"
    echo "当前 commit：$(git -C "$dest" rev-parse HEAD)"
    exit 0
fi

mkdir -p "$(dirname "$dest")"
echo "== clone riscv-arch-test@$branch =="
git clone --depth 1 --branch "$branch" https://github.com/riscv-non-isa/riscv-arch-test.git "$dest"
echo "OK: $dest"
echo "commit: $(git -C "$dest" rev-parse HEAD)"
