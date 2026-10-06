# ============================================================
# build_fmax.tcl —— OOC post-route 单轮 Fmax 跑（约束递减收敛法用）
# 用法：vivado -mode batch -source build/build_fmax.tcl -tclargs <top> <label> <period_ns> \
#       ?-core_profile nofwd|fwd|bht1|bht2? <src>...
#   src 为 .v 文件或目录（目录则 glob 其下 *.v），可传多个
# 产出：build/run/fmax/<label>/（临时产物，不入库）、build/reports/fmax/<label>/（报告证据）
# 口径：与 build/build.tcl（v0 基线）完全同法——OOC、默认优化 directive、
#       xc7z020clg400-1，仅时钟周期作为变量（约束递减 10ns→5ns→收敛），
#       保证自研核与 PicoRV32 两边同法可比（docs/core_comparison.md §3）
# ============================================================

set top    [lindex $argv 0]
set label  [lindex $argv 1]
set period [lindex $argv 2]
set core_profile ""
set src_start 3
if {$argc >= 5 && [lindex $argv 3] eq "-core_profile"} {
    set core_profile [lindex $argv 4]
    set src_start 5
}
set srcs [lrange $argv $src_start end]
if {[llength $srcs] == 0} {error "At least one RTL source or directory is required"}
if {$core_profile ne ""} {
    switch -- $core_profile {
        nofwd {set enable_forwarding 0; set bht_mode 0}
        fwd   {set enable_forwarding 1; set bht_mode 0}
        bht1  {set enable_forwarding 1; set bht_mode 1}
        bht2  {set enable_forwarding 1; set bht_mode 2}
        default {error "Unsupported core profile: $core_profile"}
    }
    set core_generics [list ENABLE_FORWARDING=$enable_forwarding BHT_MODE=$bht_mode]
}
set part       xc7z020clg400-1
set script_dir [file normalize [file dirname [info script]]]
set run_dir [file join $script_dir run fmax $label]
set rep_dir [file join $script_dir reports fmax $label]
file mkdir $run_dir
file mkdir $rep_dir

# ---- 周期约束落 run 目录（不入库），风格同 build/constraints/core_top.xdc ----
set xdc_path [file join $run_dir clock.xdc]
set fh [open $xdc_path w]
puts $fh "create_clock -name sys_clk -period $period \[get_ports clk\]"
puts $fh "set_property HD.CLK_SRC BUFGCTRL_X0Y0 \[get_ports clk\]"
close $fh

# ---- 源文件收集：.v 单文件直接读，目录 glob 其下 *.v ----
# 源码保持 Verilog-2001 兼容；沿用 -sv 读取方式以保持既有综合流程不变。
foreach s $srcs {
    set p [file normalize $s]
    if {[string match *.v $p]} {
        read_verilog -sv $p
    } else {
        read_verilog -sv [glob [file join $p *.v]]
    }
}
read_xdc $xdc_path

# ---- 综合（OOC）+ 实现，步骤同 build.tcl ----
if {$core_profile eq ""} {
    synth_design -top $top -part $part -mode out_of_context
} else {
    synth_design -top $top -part $part -mode out_of_context -generic $core_generics
}
write_checkpoint -force [file join $run_dir post_synth.dcp]
report_utilization    -file [file join $rep_dir utilization_synth.rpt]
report_timing_summary -file [file join $rep_dir timing_synth.rpt] -delay_type max

opt_design
place_design
route_design
write_checkpoint -force [file join $run_dir post_route.dcp]
report_utilization       -file [file join $rep_dir utilization_impl.rpt]
report_timing_summary    -file [file join $rep_dir timing_impl.rpt] -delay_type max
report_design_analysis   -file [file join $rep_dir design_analysis_impl.rpt]
report_timing -delay_type max -max_paths 10 -sort_by group \
    -file [file join $rep_dir timing_worst_paths.rpt]

# ---- 控制台摘要：Fmax = 1/(period - WNS)，WNS 为负表示超期到达 ----
set wns  [get_property SLACK [get_timing_paths -delay_type max -max_paths 1]]
set fmax [expr {1000.0 / ($period - $wns)}]
puts "============================================"
puts "FMAX RUN DONE: $top @ $part period=${period}ns"
if {$core_profile ne ""} {puts "CORE PROFILE = $core_profile"}
puts "WNS  = ${wns} ns"
puts "Fmax = [format %.1f $fmax] MHz"
puts "reports -> $rep_dir"
puts "============================================"
