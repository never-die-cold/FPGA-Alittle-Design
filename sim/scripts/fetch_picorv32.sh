#!/usr/bin/env bash
# fetch_picorv32.sh —— 取第三方 PicoRV32 源码到 sim/build/picorv32（.gitignore 区，不入库）
# 固定上游 commit 保证复现；跑分口径见 docs/core_comparison.md §2/§3。
set -e
cd "$(dirname "$0")/../.."
PINNED=ef203c2b0a3fb793280f5114941416c425c5b461   # 2026-10-03 master tip
DEST=sim/build/picorv32

if [ ! -f "$DEST/picorv32.v" ]; then
    git clone --depth 1 https://github.com/YosysHQ/picorv32.git "$DEST"
fi

actual=$(git -C "$DEST" rev-parse HEAD)
if [ "$actual" != "$PINNED" ]; then
    echo "picorv32 本地 $actual != 固定 $PINNED，重取…"
    rm -rf "$DEST"
    git clone https://github.com/YosysHQ/picorv32.git "$DEST"
    git -C "$DEST" checkout -q --detach "$PINNED"
fi
echo "picorv32 @ $(git -C "$DEST" rev-parse HEAD) OK"
