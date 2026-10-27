# Multi-target result-slot fix and frozen CNN r6 on-board comparison

Date: 2026-10-28. FPGA build source HEAD: `cfbded8`, branch `dev/riscv`, plus the working-tree Python validation scripts. Exact hardware numeric comparison has passed; live paper-edge localization remains under investigation below.

## Inputs and commands

- RTL result-slot fix is already in HEAD, in `src/coprocessor/cop_task_ctrl.v`; no RTL was changed by this run. Its repository regression entry is `bash sim/scripts/run_iverilog.sh cop_multitarget_commit` (previous directed evidence, not rerun here).
- `vivado.bat -mode batch -nojournal -log data/logs/2026-10-28-multitarget-board-r6/init-probe-vivado.log -source sim/scripts/probe_vivado_project_init.tcl` passed `create_project -in_memory`.
- The same probe with `-tclargs nested` also passed a nested Vivado executable. The earlier fatal TclApp initialization failure was not reproduced by these probes. One current OOC child emitted `Could not open 'C' for writing` at startup and continued successfully; that message alone is not synthesis PASS evidence.
- Build: set `COP_BUILD_NAME=pynq_multitarget_r6_20261028`, `COP_WITH_VIDEO=1`, then run `vivado.bat -mode batch -nojournal -log data/logs/2026-10-28-multitarget-board-r6/build-vivado.log -source build/_gate_env.tcl`. Wrapper clears Vivado's Python environment and pins host Python 3.12. Build output names are unique; reproduction must choose a fresh build name.
- Frozen r6 payload SHA256 `ffc2620df59ab0292a4130d6741fb71b73d972696198a992a21a63877d2b12fa`; model ID `0x4a303257`, CRC `0xa73ee0d9`. Model provenance is in `data/evidence/2026-10-28-cnn-r6/README.md`.
- Exact vectors: `python sim/scripts/prepare_cnn_board_vectors.py --model sim/build/real-roi-ptq-20261028-r6 --comparison data/logs/2026-10-28-mixed-standing-r6/comparison --output data/logs/2026-10-28-multitarget-board-r6/vectors-r1`. `vectors/` is an incomplete first attempt (relative-path reporting error); only `vectors-r1/manifest.json` is used.
- Second scene's vectors and human labels are in `data/logs/2026-10-28-r6-holdout-layout04/`.
- Board commands are persisted in `run-board-r6.sh`, `resume-board-r6.sh`, `check-product-limit-r6.sh` and `start-r6-service.sh`; each refuses existing output directories. The first checks the known boot ID and previous service identity before stopping it. Final board-only `sim/scripts/check_cnn_board_vectors.py` tests 1, 3, full scene, reversed scene, the product's 10-target boundary and repeated full-scene jobs. It compares exact logits, IDs, valid/error bits, class, margin, score and low-confidence bits; the driver checks sequence and firmware decisions.

## Evidence and boundaries

- `board-before.log`, `board-stage.log`: same boot `30d6fc34-e372-4b0e-b9de-e8f4617b40d6`; original LIVE/C01/COP_HW service was PID 2566 and kept running during the build.
- Compile/shell syntax checks and `git diff --check` passed for the added validation scripts before board execution; these do not constitute hardware validation.
- Build reports: `build/reports/pynq_multitarget_r6_20261028/`. Never substitute reports or checkpoints from a different build.
- This is a provisional r6 development model. Exact integer/hardware agreement does not establish class accuracy. The new human-confirmed nine-object scene scores 8/9 in FP32 and INT8, with one washer classified as nut. It is excluded from training/calibration/model selection. The user has no new specimens; unseen-specimen generalization remains unimplemented.
- Product confidence threshold remains `.8`; numeric tests do not lower it to obtain a business PASS. Localization uses the predeclared local-background threshold 25 for alignment with the frozen scene comparisons. PL supplies raw video/capture and CNN; localization/ROI preprocessing run on PS.
- No commit, push or merge performed in this run. Existing local-only YOLO files and unrelated working-tree changes are preserved.

## Actual build and board results

- Whole-system build gate passed. Routed setup WNS 1.359 ns, hold WHS 0.012 ns, no failing setup/hold endpoints; DSP 136, BRAM36-equivalent 72.5, latches 0, blocking DRC 0, IMEM first word `00008117`, readmem warnings 0. CDC allowlist counts: CDC-15=73, CDC-3=12, CDC-6=7. Raw-capture vision structural checks passed without relaxing assertions.
- Bit SHA256 `a929904866213f4133a6c12ee1a3dada0538ea99da6db89ab6f3fb6316807ce9`; HWH SHA256 `f01b96a3f9435b369595ef7bcdaaa32980213130df6b4e9a0f0ff622cd8c3527`.
- Methodology is not warning-free: TIMING-2/4 identify the clock wizard's internal primary-clock definition/redefinition; TIMING-6/7 identify PS/COP clock relationships. Vendor clock/reset topology and I/O-delay warnings also remain. Preserve `cop_system_wrapper_methodology_drc_routed.rpt`; the reported gate PASS is limited to the implemented timing/CDC/DRC checks and these board tests, not a claim that every methodology finding was resolved.
- `board-evidence/attempt-1/golden-roi_001.json`: r6 golden matches exactly, logits `[67,-60,-13]`, class 0, margin 80, score 10320, model CRC `0xa73ee0d9`, payload 36032 bytes, FCLK1 142.857143 MHz feeding the 40 MHz MMCM.
- `board-evidence/numeric-pass/mixed/summary.json`: 6 jobs, 44 target results, all exact; `holdout/summary.json`: 6 jobs, 41 target results, all exact. Total 12 jobs / 85 results. Each scene's RESULT_SEQ is 1,2,3,4,5,6. Reversed and repeated inputs pass. No result-slot shift reappeared.
- Final immutable package: host `build/board-package-r6-multitarget-20261028-r1`, board `/home/xilinx/cop-pkg-r6-multitarget-20261028-r1`. Board app `/home/xilinx/cop-app-r6-20261028`.
- LIVE service restored, session `1960f427-2896-4c1c-a1d7-4913e11e250f`, backend C01, engine COP_HW, prototype=false. Runtime root `/home/xilinx/cop-live-r6-20261028`; no boot/autostart change was made.
- HDMI output independently recaptured as 24 valid 1280x720 BGR frames after restoration; `uvc-after-r6/raw.png` was visually checked and is not black. Frame SHA256 `9c8a382155d35026c6625202a7298ff1cea4f3ab770d35c78c1d017cbe889e4a`.
- First real C01 rounds detect 11 candidates: nine objects plus top/right paper/table seams. Product limit 10 correctly returns RECHECK/target_limit before inference. Full frames, all candidate boxes and packets are retained under `board-evidence/live/1960f427/`; user was asked to cover the seams before a new real capture. This result is not counted as a successful live CNN round.
- Evidence download: `python data/logs/2026-10-28-multitarget-board-r6/fetch-evidence.py` (new output directory required). Remote byte copies and SHA256 are in `board-evidence/manifest.json`.

## Concurrent workspace update and retained failed attempts

- At host 02:21:08, another operation executed `git pull --ff-only`, advancing this shared checkout from `cfbded8` to `0430257` after the FPGA build had finished. The RTL in the build source manifest did not change; only the build gate's descriptive CDC comment changed. The loader changed `prepare_board` from a two-item to a three-item return.
- Attempt 0 packaged that new loader with the existing fast runner and stopped at tuple unpacking after READY=1, before inference. `board-numeric-console.log` and `board-evidence/attempt-0/` preserve it. The fast runner and numeric checker now read the compatible first two returned fields. Package r1 pins the loader from `0430257` plus this one-line runner fix; it does not depend on further checkout changes.
- Attempt 1's golden and 1/3/10/reversed-10 hardware jobs passed. A 15-target test was then rejected by the existing business policy (limit 10) before hardware submission. The test harness was corrected to the product boundary 10, keeping the refusal under `board-evidence/attempt-1/`; the complete subsequent tests are in `numeric-pass/`.
- The first LIVE response was generated successfully but its host command attempted to save into a root-owned board directory as xilinx. A sudo curl saved the next response successfully; both host console logs are retained. Service startup polling connection refusals were transient before the status endpoint became available.
