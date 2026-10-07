#!/usr/bin/env bash
# deploy_vision_onboard —— 把视觉 overlay 上板包一键推到 PYNQ-Z2（模块二上板入口）
#
# 前置（一次性，串口执行）：
#   1) hostname -I                      # 拿板卡内网 IP
#   2) mkdir -p ~/.ssh && chmod 700 ~/.ssh && echo '<主机公钥>' >> ~/.ssh/authorized_keys \
#      && chmod 600 ~/.ssh/authorized_keys && echo KEY-OK
# 用法（仓库根目录，Git Bash）：
#   bash sim/scripts/deploy_vision_onboard.sh <板卡IP> [用户名] [板端目录]
# 默认 xilinx@<IP>:~/vision（PYNQ 默认账号密码 xilinx）。
set -euo pipefail
IP=${1:?用法: $0 <板卡IP> [用户名] [板端目录]}
BRD_USER=${2:-xilinx}
DEST=${3:-vision}
ROOT=$(cd "$(dirname "$0")/../.." && pwd)

BUILD="${VISION_HDMI_OUT:-$ROOT/sim/build/hdmi-project}"
BIT="$BUILD/vision.bit"
HWH="$BUILD/vision_hdmi.gen/sources_1/bd/vision/hw_handoff/vision.hwh"
HOST_DIR="$ROOT/src/pynq_host"

for f in "$BIT" "$HWH" \
         "$HOST_DIR/vision_regs.py" "$HOST_DIR/vision_protocol.py" \
         "$HOST_DIR/vision_demo.py" "$HOST_DIR/onboard_smoke.py" "$HOST_DIR/display_view.py"; do
  [ -f "$f" ] || { echo "缺少交付物: $f（先跑 sim/scripts/run_vivado_hdmi.sh）" >&2; exit 1; }
done

SSH_OPTS=(-o StrictHostKeyChecking=accept-new -o ConnectTimeout=5)
echo "== 连通性检查 $BRD_USER@$IP =="
ssh "${SSH_OPTS[@]}" "$BRD_USER@$IP" "cat /etc/version; mkdir -p ~/$DEST"

echo "== 推送 bit/hwh/脚本 → ~/$DEST =="
scp "${SSH_OPTS[@]}" "$BIT" "$HWH" "$BRD_USER@$IP:~/$DEST/"
scp "${SSH_OPTS[@]}" "$HOST_DIR"/vision_regs.py "$HOST_DIR"/vision_protocol.py \
    "$HOST_DIR"/vision_demo.py "$HOST_DIR"/onboard_smoke.py "$HOST_DIR"/display_view.py "$BRD_USER@$IP:~/$DEST/"

echo "== 板端清点 =="
ssh "${SSH_OPTS[@]}" "$BRD_USER@$IP" "ls -la ~/$DEST"
echo "部署完成。下一步: ssh $BRD_USER@$IP 'cd ~/$DEST && python3 onboard_smoke.py load'"
