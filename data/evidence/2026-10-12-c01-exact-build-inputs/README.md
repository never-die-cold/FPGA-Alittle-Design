# C01构建输入的精确字节恢复（2026-10-12）

来源：`data/logs/c01-capture-e2a602d6e0da49a2b6da072abca47c70/manifest.json`及其归档inputs。
旧归档受Git `text=auto / eol=lf`转换，68个文件不再直接匹配构建清单的原始字节。
本目录只在新增副本中恢复CRLF；每个文件同时匹配原清单SHA256和字节数后才写入，共98文件全部一致。
清单本身逐字节复制，旧归档和原始失败保留。定向-text避免再次规范化这些证据。

严格复算（不启用恢复）：

```powershell
python sim/scripts/audit_c01_build_inputs.py data/evidence/2026-10-12-c01-exact-build-inputs/manifest.json --output sim/build/c01-input-recheck-new.json
```

输出必须是新文件。再次重建恢复包时：

```powershell
python sim/scripts/audit_c01_build_inputs.py data/logs/c01-capture-e2a602d6e0da49a2b6da072abca47c70/manifest.json --recover-to sim/build/c01-input-recovery-new --output sim/build/c01-input-recovery-new.json
```

目标目录也必须是新目录。哈希不匹配、内容变化、路径越界或重复条目仍拒绝，不会覆写旧证据。
失败后留下的部分目录不可作为完整包；仅命令正常结束且全部98条通过才完整。

核对时当前96个输入与原清单同字节；`build_capture_hdmi.tcl`与`run_c01_capture.ps1`已有后续改动。
所有归档vision RTL/XDC仍与当前一致；不能把后加包装/检查改动说成参与了此前构建。
对应候选XSA的逐字节bit/hwh配对由`check_c01_artifacts.py`另行检查，本恢复只证明输入字节可复算。
它不独立证明bit到源码映射、可重复产生同一位流、CDC全部通过或实机DDR/工业验收。

原始诊断、恢复输出、严格复算与最终命令见`data/logs/2026-10-12-nc-offline/`。
