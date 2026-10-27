# [2026-10-26] J07 摸底、板端回传与 ROI 验收工具收口

> 分支 `dev/riscv`；本地未 push；本轮未运行 Vivado，未作板级结论。

## 1. 完成项与提交

| 任务 | 产物 | 提交 |
|:---|:---|:---|
| J07 摸底 | `docs/coprocessor-video-integration-plan.md` | `1f99409` |
| 板端断言 | `tools/cop_payload_loader.py` | `bbb082c` |
| 回传解析 | `tools/summarize_board_run.py` | `971d784` |
| 回传回归 | `sim/coprocessor/test_summarize_board_run.py` + runner | `e412e1d` |
| ROI 审计器 | `tools/check_roi_dataset.py` | `f5728a8` |
| ROI 合成回归 | `sim/coprocessor/test_check_roi_dataset.py` + runner | `6fbae3a` |
| ROI 交接 | `docs/roi-dataset-handoff.md` | `3c596ca` |
| 状态/Open/包台账 | `src/coprocessor/plan.md` + `docs/coprocessor-nc-handoff.md` | `6be9c3f` |

## 2. 验证证据

```bash
python3 -m py_compile tools/check_roi_dataset.py sim/coprocessor/test_check_roi_dataset.py
COPROCESSOR_PYTHON=sim/build/vision-venv-full/bin/python \
  bash sim/scripts/run_coprocessor_iverilog.sh roi_dataset
RISCV_CROSS=riscv64-unknown-elf- \
COPROCESSOR_PYTHON=sim/build/vision-venv-full/bin/python \
  bash sim/scripts/run_coprocessor_iverilog.sh all
```

- `roi_dataset` 退出 0：`PASS: roi_dataset synthetic 3-class/3-split fixture; dimensions, channels, bbox, split coverage, distribution, and per-file SHA256 audited; invalid samples rejected`
- `all` 退出 0；包含上述 ROI PASS 及
  `PASS: board_run_summary accepts exact clock/status/golden data and rejects clock, first-status, error, sequence, and result mismatches; verdict remains data-only`。
- `all` 最后一条：`PASS: cnn_sequencer .../zero all 9225 packed words/73795 elements match integer network; logits=04fd02 class=2 margin=2 cycles=472593`。
- `git diff --check` 退出 0。

## 3. J07 边界

- 已启动架构/资源/CDC 摸底，没有实现视频板顶。
- 保守相加为 DSP 136/220、BRAM36 113.5/140；完整 720p 帧缓存必须放 DDR。
- 最大风险：VDMA 帧槽所有权与 frame/ROI/result 身份未原子绑定，可能静默分类旧帧或混合帧。

## 4. 包与 OPEN 台账

- 唯一有效包：`dist/cop-board-gate-5653d5911b76.tar.gz`，SHA256
  `a342287dbce47e3d1f24e22b757243f97626d11336be248e88aed3fc805178af`；仍是 PROVISIONAL，板上 UNVERIFIED。
- `759744b99891` / `d66916c49b80` / `21c4e751bbe8` / `f856d5861db0` 已明确作废；
  其他 dist 中间包也非有效交付。
- OPEN-K2-1：已关闭；`utilization_impl.rpt` 记录 Block RAM Tile 69/140。
- OPEN-IMEM-1：综合已关，新 bit 的固件活性仍待板上验证。
- OPEN-BT-4：保持开启；任意目标描述表未接，非恒等 target/ROI 关联不可验收。
- 本轮未新增 OPEN。`dist/wip-backup-2026-10-25` 已按指令删除。

## 5. 下一步

1. JL 拍板 J07 采用 HDMI PL 取帧还是 PS USB/UVC，并选 HP0 共享调度或独立 HP 端口。
2. NC 用唯一有效包返回 loader JSON/串口日志，再运行 `tools/summarize_board_run.py`。
3. WC 按 `docs/roi-dataset-handoff.md` 交付真实 ROI；结构 PASS 不代替标签/来源审核。
