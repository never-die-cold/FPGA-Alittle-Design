# PYNQ-Z2 RISC-V SoC：综合、实现、门禁、报告与 bitstream。
# 用法：vivado -mode batch -source build/build_soc.tcl
set script_dir [file normalize [file dirname [info script]]]
set root       [file normalize [file join $script_dir ..]]
set run_dir    [file join $script_dir run soc]
set rep_dir    [file join $script_dir reports]
set part       xc7z020clg400-1
set top        pynq_z2_top

file mkdir $run_dir
file mkdir $rep_dir
cd $root

proc require_clock {name expected_period} {
    set clock [get_clocks -quiet $name]
    if {[llength $clock] != 1} {error "Missing or duplicate clock: $name"}
    set period [get_property PERIOD $clock]
    if {abs($period - $expected_period) > 0.001} {
        error "Clock $name period is $period ns, expected $expected_period ns"
    }
}

# 读入正式 RTL 与板级约束；当前目录为仓库根，供 $readmemh 找到固件。
read_verilog [glob [file join $root src riscv *.v]]
read_xdc [file join $script_dir constraints pynq_z2_soc.xdc]

synth_design -top $top -part $part
require_clock sys_clk_125 8.000
require_clock core_clk_40 25.000
write_checkpoint -force [file join $run_dir post_synth.dcp]
report_utilization -file [file join $rep_dir soc_utilization_synth.rpt]
report_clock_utilization -file [file join $rep_dir soc_clock_utilization_synth.rpt]

opt_design
place_design -directive Explore
phys_opt_design -directive Explore
route_design -directive Explore
phys_opt_design -directive Explore
write_checkpoint -force [file join $run_dir post_route.dcp]

report_utilization -file [file join $rep_dir soc_utilization_impl.rpt]
report_clock_utilization -file [file join $rep_dir soc_clock_utilization_impl.rpt]
report_timing_summary -delay_type min_max -report_unconstrained \
    -check_timing_verbose -file [file join $rep_dir soc_timing_impl.rpt]
report_timing -delay_type max -max_paths 10 -sort_by group \
    -file [file join $rep_dir soc_timing_worst_paths.rpt]
report_drc -file [file join $rep_dir soc_drc_impl.rpt]

# Vivado 正式时序检查不得发现无时钟、恒定时钟或未约束内部端点。
set checks {no_clock constant_clock unconstrained_internal_endpoints generated_clocks}
set check_result [check_timing -override_defaults $checks -verbose -return_string]
set check_file [open [file join $rep_dir soc_check_timing.rpt] w]
puts $check_file $check_result
close $check_file
foreach check $checks {
    set pattern [format {checking %s \(0\)} $check]
    if {![regexp $pattern $check_result]} {
        error "Timing check failed: $check"
    }
}
set worst_path [get_timing_paths -delay_type max -max_paths 1]
if {[llength $worst_path] == 0} {error "No setup timing path found"}
set wns [get_property SLACK [lindex $worst_path 0]]
if {![string is double -strict $wns] || $wns < 0} {error "Setup timing failed: WNS=$wns ns"}

set bad_drc [get_drc_violations -quiet \
    -filter {SEVERITY == Error || SEVERITY == "Critical Warning"}]
if {[llength $bad_drc] != 0} {error "DRC errors or critical warnings: $bad_drc"}

set bitstream [file join $run_dir pynq_z2_soc.bit]
write_bitstream -force $bitstream
if {![file isfile $bitstream] || [file size $bitstream] == 0} {
    error "Bitstream missing or empty: $bitstream"
}

set version_file [open [file join $rep_dir soc_vivado_version.txt] w]
puts $version_file [version -short]
close $version_file
puts "BUILD PASSED: $top @ $part, core clock 40 MHz, WNS=$wns ns"
puts "BITSTREAM: $bitstream"
