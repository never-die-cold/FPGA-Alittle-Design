# ============================================================
# build.tcl —— v0 RISC-V 核可复现构建（综合 + 实现 + 报告归档）
# 用法：vivado -mode batch -source build/build.tcl
# 依赖：src/riscv/*.v、build/constraints/<top>.xdc
# 产出：build/run/（临时产物，不入库）、build/reports/（入库，指标证据）
# 说明：v0 核暂无板级顶层与 I/O 约束，采用 out_of_context（OOC）模式做
#       核级 Fmax/WNS 与资源基线——不插入/不放置 I/O 缓冲，避免
#       Place 30-58（166 个顶层 I/O > CLG400 可用 125 脚）；
#       bitstream 流程待 SoC 顶层就位后（M3）再挂接。
# ============================================================

set script_dir [file normalize [file dirname [info script]]]
set root       [file normalize [file join $script_dir ..]]
set part       xc7z020clg400-1
set top        core_top
set run_dir    [file join $script_dir run]
set rep_dir    [file join $script_dir reports]

file mkdir $run_dir
file mkdir $rep_dir

# ---- 1) 读入 RTL 与约束 ----
read_verilog [glob [file join $root src riscv *.v]]
read_xdc     [file join $script_dir constraints ${top}.xdc]

# ---- 2) 综合 ----
synth_design -top $top -part $part -mode out_of_context
write_checkpoint -force [file join $run_dir post_synth.dcp]
report_utilization    -file [file join $rep_dir utilization_synth.rpt]
report_timing_summary -file [file join $rep_dir timing_synth.rpt] -delay_type max

# ---- 3) 实现（opt / place / route）----
opt_design
place_design
route_design
write_checkpoint -force [file join $run_dir post_route.dcp]
report_utilization       -file [file join $rep_dir utilization_impl.rpt]
report_timing_summary    -file [file join $rep_dir timing_impl.rpt] -delay_type max
report_design_analysis   -file [file join $rep_dir design_analysis_impl.rpt]
report_timing -delay_type max -max_paths 10 -sort_by group \
    -file [file join $rep_dir timing_worst_paths.rpt]

# ---- 4) 控制台结果摘要 ----
set wns [get_property SLACK [get_timing_paths -delay_type max -max_paths 1]]
puts "============================================"
puts "BUILD DONE: $top @ $part"
puts "WNS = ${wns} ns （约束 10.000 ns / 100 MHz）"
puts "reports -> $rep_dir"
puts "============================================"
