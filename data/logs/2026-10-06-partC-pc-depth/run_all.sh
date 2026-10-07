#!/usr/bin/env bash
# Durable full regression launcher: preserves stdout, stderr and real exit status.
set -u
evidence_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
repo_dir=$(cd -- "$evidence_dir/../../.." && pwd)
cd -- "$repo_dir" || exit 1
if [ -e "$evidence_dir/all-final.log" ]; then
    echo "Refusing to overwrite all-final.log" >&2
    exit 1
fi
printf '%s\n' "bash sim/scripts/run_iverilog.sh all" > "$evidence_dir/all-final.command.txt"
date -Iseconds > "$evidence_dir/all-final.started.txt"
bash sim/scripts/run_iverilog.sh all > "$evidence_dir/all-final.log" 2>&1
pc_depth_status=$?
printf 'run_iverilog all exit_code=%s\n' "$pc_depth_status" > "$evidence_dir/all-final.exit.txt"
date -Iseconds > "$evidence_dir/all-final.finished.txt"
exit "$pc_depth_status"
