#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
dest=sim/build/hdmi-library-full
revision=f4613fff005b098065fd5d619a2b88e55720a423
if [ ! -d "$dest/.git" ]; then
    git clone --no-checkout https://github.com/Digilent/vivado-library.git "$dest"
fi
git -C "$dest" cat-file -e "$revision^{commit}" || git -C "$dest" fetch origin "$revision"
git -C "$dest" checkout --detach "$revision"
[ "$(git -C "$dest" rev-parse HEAD)" = "$revision" ]
"${VISION_PYTHON:-python}" sim/scripts/prepare_hdmi_sources.py
echo "PASS: pinned HDMI IP and official PYNQ-Z2 inputs prepared"
