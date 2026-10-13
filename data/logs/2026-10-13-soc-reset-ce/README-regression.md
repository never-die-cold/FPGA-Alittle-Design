# 2026-10-13 SoC reset/CE simulation evidence

Baseline input: branch `dev/model`, HEAD `3e2e1c9e612df5c01da4699ea2940493f0e99839`, with pre-existing user changes recorded in `baseline-git-status.txt`.

- Entry point: `C:\msys64\usr\bin\bash.exe sim/scripts/run_iverilog.sh <mode>` from the repository root.
- PATH prefix: `C:\msys64\ucrt64\bin;C:\msys64\usr\bin`.
- Versions: Icarus Verilog 13.0 (stable), GNU Bash 5.3.15; full output in `baseline-tools.txt`.
- Source/test/firmware/entry-point SHA-256: `baseline-input-sha256.txt`.
- `baseline-mem_wb.txt` preserves the initial sandbox failure (`NtCreateDirectoryObject`, status 0xC0000022; exit -1073741502).
- `baseline-approved-*.txt` preserve the successfully rerun simulations after tool approval; adjacent `.command.txt` and `.exit.txt` files contain exact entry commands and exit codes.

| Baseline mode | Exit | cycles | retired | bubbles | CPI printed by tb | BHT lookup/hit/miss |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| mem_wb | 0 | n/a | n/a | n/a | n/a | PASS: 3 captures |
| bench_nofwd | 0 | 2850 | 1205 | 1645 | 2.365 | 0/0/0 |
| bench_fwd | 0 | 2423 | 1205 | 1218 | 2.011 | 0/0/0 |
| bench_bht1 | 0 | 2380 | 1205 | 1175 | 1.975 | 161/93/68 |
| bench_bht2 | 0 | 2351 | 1205 | 1146 | 1.951 | 161/122/39 |

All benchmark modes exit through `tohost=327535569`. These are short benchmark v0.1 measurements, not full CoreMark 2K/32 measurements. The original timescale and short-image `$readmemh` warnings are retained in the raw logs.

No RTL, testbench, script, or firmware file was modified by the regression subtask. Post-patch/full-regression results will be recorded separately.

## Post-patch regression (after the mem_wb reset/CE rewrite, 2026-10-13)

The RTL change is `src/riscv/mem_wb_stage.v` only: `mem_valid` keeps its asynchronous reset; all payload fields moved to a separate `always @(posedge clk)` block with no reset and no enable. The testbench `sim/riscv/tb_mem_wb_stage.v` gained reset-time payload, release, and short-pulse checks (39 captures, up from 3). The contract text is `src/riscv/design_v1.md` §12.5.

- Entry point unchanged: msys2 bash + `sim/scripts/run_iverilog.sh <mode>` from the repository root.
- Environment fix vs baseline: this host's msys2 child shell had an empty `TMP`, so iverilog fell back to the non-existent `C:\TEMP`. Every post-patch command therefore exports `TMP=/c/Users/ASUS/AppData/Local/Temp` first (exact lines in `postpatch-*.command.txt`).
- 28 modes ran, all exit 0, no FAIL/FATAL in any log.

| Post-patch mode | Exit | cycles | retired | bubbles | CPI | cycles vs baseline |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| mem_wb | 0 | n/a | n/a | n/a | n/a | new checks PASS (39 captures) |
| bench_nofwd | 0 | 2850 | 1205 | 1645 | 2.365 | identical |
| bench_fwd | 0 | 2423 | 1205 | 1218 | 2.011 | identical |
| bench_bht1 | 0 | 2380 | 1205 | 1175 | 1.975 | identical |
| bench_bht2 | 0 | 2351 | 1205 | 1146 | 1.951 | identical |
| coremark (full 2K/32 golden) | 0 | 17114141 | 10106386 | 7007755 | 1.693 | baseline ran no full coremark; this is the post-patch golden PASS |

The other 22 modes (`v0 fwd v1_flow v1_mem v1_hazard_fwd v1_hazard_nofwd v1_muldiv_flow v1_muldiv_fwd v1_muldiv_nofwd muldiv rv32im imem dmem if_stage id_ex decode forwarding hazard branch_predict pc_control bht_flow_off bht_flow_1 bht_flow_2 soc soc_check`) all exit 0. `vision*`/`cop_*` were not run this round: no vision or coprocessor RTL changed.

Cycle-identical benchmarks plus the full coremark golden PASS are the CPI-preservation evidence for the rewrite. Vivado A/B evidence is in `vivado/README-ab.md`.
