#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
PY="${COPROCESSOR_PYTHON:-sim/build/vision-venv-full/bin/python}"
if ! command -v "$PY" >/dev/null 2>&1; then PY=python3; fi
if [ "$#" -gt 1 ]; then echo "usage: $0 [JL-verified.bit]"; exit 2; fi
if [ "$#" -eq 1 ] && [ ! -s "$1" ]; then echo "ERROR: bitstream missing or empty: $1"; exit 1; fi

# Package evidence is regenerated, never copied from an unverified handwritten table.
COPROCESSOR_PYTHON="$PY" bash sim/scripts/run_coprocessor_iverilog.sh bram_network
commit="$(git rev-parse HEAD)"
short="$(git rev-parse --short=12 HEAD)"
version="cop-board-gate-$short"
dist="$ROOT/dist"
stage="$dist/$version"
if [ -e "$stage" ]; then echo "ERROR: output already exists: $stage"; exit 1; fi
mkdir -p "$stage/payload" "$stage/golden" "$stage/evidence"

files=(
  docs/contracts/coprocessor-integration-v0.md docs/coprocessor-wc-interface.md
  docs/coprocessor-storage-plan.md docs/coprocessor-vivado-checklist.md docs/coprocessor-nc-handoff.md
  src/riscv/design_v1.md src/riscv_fw/cop_job.c src/coprocessor/*.v
  sim/coprocessor/tb_cnn_sequencer.v sim/coprocessor/tb_cop_bram_latency.v
  sim/coprocessor/generate_network_vectors.py sim/scripts/run_coprocessor_iverilog.sh
  build/build_coprocessor_gate.tcl build/constraints/coprocessor_ooc.xdc
  build/constraints/coprocessor_storage_ooc.xdc build/constraints/coprocessor_board_clock.xdc
  board/scripts/program_soc.bat board/scripts/program_soc.tcl
)
for file in "${files[@]}"; do mkdir -p "$stage/payload/$(dirname "$file")"; cp "$file" "$stage/payload/$file"; done
cp -a sim/build/coprocessor/network-vectors/. "$stage/golden/"
cp sim/build/coprocessor/network_bram_pattern.log sim/build/coprocessor/network_bram_zero.log \
   sim/build/coprocessor/cop_bram_latency.log "$stage/evidence/"
bit_status=UNVERIFIED
if [ "$#" -eq 1 ]; then cp "$1" "$stage/payload/JL-verified.bit"; bit_status=JL_SUPPLIED_UNVERIFIED_ON_BOARD; fi
{
  echo "VERSION=$version"
  echo "GIT_COMMIT=$commit"
  echo "BITSTREAM=$bit_status"
  echo "VIVADO=UNVERIFIED_NEEDS_WINDOWS"
  echo "BOARD=UNVERIFIED_NEEDS_NC"
} > "$stage/VERSION"

"$PY" - "$stage/golden/manifest.json" "$stage/evidence" "$stage/EXPECTED_OUTPUTS.tsv" <<'PY'
import json,re,sys,zlib
from pathlib import Path
manifest=Path(sys.argv[1]); evidence=Path(sys.argv[2]); out=Path(sys.argv[3])
data=json.loads(manifest.read_text())
rows=["case\tclass_id\tmargin_q\tscore_q15\tlow_conf\tlogits\tresult_crc32\tpacked_words\telements\tcycles\tsim_log_crc32"]
for name in ("pattern","zero"):
    case=data["cases"][name]; result=case["result"]
    result_bytes=(manifest.parent/name/"result.txt").read_bytes()
    log_bytes=(evidence/f"network_bram_{name}.log").read_bytes(); log=log_bytes.decode()
    match=re.search(r"all (\d+) packed words/(\d+) elements.*cycles=(\d+)",log)
    if not match or "PASS:" not in log: raise SystemExit(f"missing BRAM PASS evidence: {name}")
    rows.append("\t".join(map(str,(name,result["class_id"],result["margin_q"],result["score_q15"],
        int(result["low_conf"]),",".join(map(str,case["logits"])),f"{zlib.crc32(result_bytes)&0xffffffff:08x}",
        match.group(1),match.group(2),match.group(3),f"{zlib.crc32(log_bytes)&0xffffffff:08x}"))))
out.write_text("\n".join(rows)+"\n")
PY

(cd "$stage"; find VERSION EXPECTED_OUTPUTS.tsv payload golden evidence -type f -print | sort > FILES.txt
 while IFS= read -r file; do sha256sum "$file"; done < FILES.txt > SHA256SUMS)
tar -czf "$stage.tar.gz" -C "$dist" "$version"
sha256sum "$stage.tar.gz" > "$stage.tar.gz.sha256"
echo "PASS: NC package $stage"
