# ============================================================
# build_cop.tcl —— cop_top 的 OOC 综合 + 实现（双时钟）
# 用法：vivado -mode batch -source build/build_cop.tcl
# 产出：build/run/cop/（临时产物，不入库）、build/reports/cop/（报告证据）
# 口径：xc7z020clg400-1、out_of_context、默认优化 directive；
#       core_clk 25 ns（40 MHz，对齐板端核时钟）、cop_clk 10 ns（100 MHz，C03 目标）；
#       两个时钟设为异步组，不做跨域时序检查（CDC 交给 report_cdc 与 TB）。
# 说明：OOC 只约束寄存器到寄存器路径，I/O 无 input/output delay，
#       因此这里的 WNS 只能说明“内部逻辑过不过 100 MHz”，不能当成整机时序结论。
# ============================================================

set part       xc7z020clg400-1
set script_dir [file normalize [file dirname [info script]]]
set run_dir    [file join $script_dir run cop]
set rep_dir    [file join $script_dir reports cop]
file mkdir $run_dir
file mkdir $rep_dir

# 源码：默认 Verilog-2001 模式读取（不加 -sv），顺带验证综合语言边界。
set src_dir [file normalize [file join $script_dir .. src coprocessor]]
foreach f [lsort [glob [file join $src_dir *.v]]] {
    read_verilog $f
}

set xdc_path [file join $run_dir cop.xdc]
set fh [open $xdc_path w]
puts $fh {create_clock -name core_clk -period 25.000 [get_ports core_clk]}
puts $fh {create_clock -name cop_clk  -period 10.000 [get_ports cop_clk]}
puts $fh {set_clock_groups -asynchronous -group [get_clocks core_clk] -group [get_clocks cop_clk]}
puts $fh {set_property HD.CLK_SRC BUFGCTRL_X0Y0 [get_ports core_clk]}
puts $fh {set_property HD.CLK_SRC BUFGCTRL_X0Y1 [get_ports cop_clk]}
close $fh
read_xdc $xdc_path

synth_design -top cop_top -part $part -mode out_of_context
write_checkpoint -force [file join $run_dir post_synth.dcp]
report_utilization    -file [file join $rep_dir utilization_synth.rpt]
report_timing_summary -file [file join $rep_dir timing_synth.rpt] -delay_type max
report_cdc            -file [file join $rep_dir cdc_synth.rpt]

opt_design
place_design
route_design
write_checkpoint -force [file join $run_dir post_route.dcp]
report_utilization       -file [file join $rep_dir utilization_impl.rpt]
report_timing_summary    -file [file join $rep_dir timing_impl.rpt] -delay_type max
report_cdc               -file [file join $rep_dir cdc_impl.rpt]
report_design_analysis   -file [file join $rep_dir design_analysis_impl.rpt]
report_timing -delay_type max -max_paths 10 -sort_by group \
    -file [file join $rep_dir timing_worst_paths.rpt]

set wns_cop  [get_property SLACK [get_timing_paths -delay_type max -max_paths 1 -group [get_clocks cop_clk]]]
set wns_core [get_property SLACK [get_timing_paths -delay_type max -max_paths 1 -group [get_clocks core_clk]]]
puts "============================================"
puts "COP RUN DONE: cop_top @ $part"
puts "WNS cop_clk  (10 ns) = $wns_cop ns"
puts "WNS core_clk (25 ns) = $wns_core ns"
puts "Fmax cop_clk  = [format %.1f [expr {1000.0/(10.0-$wns_cop)}]] MHz"
puts "reports -> $rep_dir"
puts "============================================"
