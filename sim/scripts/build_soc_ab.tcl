# build_soc_ab.tcl —— SoC 复位/CE 结构研究 A/B 构建（build/build_soc.tcl 的对照变体）
# 与原脚本同 XDC、同 generic、同 opt/place/route 指令与门禁；仅三处差异：
#   1) RTL 源目录与报告输出目录由 -tclargs 指定，证据落
#      data/logs/2026-10-13-soc-reset-ce/vivado/<label>/，不写 build/；
#   2) 综合后追加 report_control_sets 与 report_high_fanout_nets，
#      用于对比复位驱动的控制集与高扇出网络；
#   3) 不写 checkpoint 与 bitstream（本任务只要时序与结构证据）。
# 用法：vivado -mode batch -source sim/scripts/build_soc_ab.tcl \
#         -tclargs <label> <srcdir> ?40|125? ?nofwd|fwd|bht1|bht2?
# 例：  ... -tclargs baseline data/logs/2026-10-13-soc-reset-ce/vivado/baseline_root/src/riscv 40 bht2
#       ... -tclargs postpatch src/riscv 40 bht2
set script_dir [file normalize [file dirname [info script]]]
set root       [file normalize [file join $script_dir .. ..]]
set part       xc7z020clg400-1
set top        pynq_z2_top
set out_root   [file join $root data logs 2026-10-13-soc-reset-ce vivado]

if {$argc < 2} {
    error "Usage: build_soc_ab.tcl <label> <srcdir> ?40|125? ?nofwd|fwd|bht1|bht2?"
}
set ab_label  [lindex $argv 0]
set ab_srcdir [lindex $argv 1]
set core_clk_mhz 40
set core_profile bht2
if {$argc >= 3} {set core_clk_mhz [lindex $argv 2]}
if {$argc >= 4} {set core_profile [lindex $argv 3]}
if {$argc > 4} {
    error "Usage: build_soc_ab.tcl <label> <srcdir> ?40|125? ?nofwd|fwd|bht1|bht2?"
}
switch -- $core_clk_mhz {
    40  {set core_clk_divide 25; set core_clk_period 25.000; set core_clk_name core_clk_40}
    125 {set core_clk_divide 8;  set core_clk_period 8.000;  set core_clk_name core_clk_125}
    default {error "Unsupported core clock: $core_clk_mhz MHz (choose 40 or 125)"}
}
switch -- $core_profile {
    nofwd {set enable_forwarding 0; set bht_mode 0}
    fwd   {set enable_forwarding 1; set bht_mode 0}
    bht1  {set enable_forwarding 1; set bht_mode 1}
    bht2  {set enable_forwarding 1; set bht_mode 2}
    default {error "Unsupported core profile: $core_profile (choose nofwd, fwd, bht1 or bht2)"}
}
set rep_dir [file join $out_root $ab_label]
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

# 读入指定源目录 RTL 与板级约束；当前目录为仓库根，供 $readmemh 找到固件。
set src_files [glob -nocomplain [file join $ab_srcdir *.v]]
if {[llength $src_files] == 0} {error "No .v files under $ab_srcdir"}
read_verilog $src_files
read_xdc [file join $root build constraints pynq_z2_soc.xdc]

set core_generics [list CORE_CLK_DIVIDE=$core_clk_divide \
    ENABLE_FORWARDING=$enable_forwarding BHT_MODE=$bht_mode]
synth_design -top $top -part $part -generic $core_generics
require_clock sys_clk_125 8.000
require_clock $core_clk_name $core_clk_period
report_utilization -file [file join $rep_dir soc_utilization_synth.rpt]
report_clock_utilization -file [file join $rep_dir soc_clock_utilization_synth.rpt]
if {[catch {report_control_sets -verbose -file [file join $rep_dir soc_control_sets_synth.rpt]} msg]} {
    puts "WARN: report_control_sets failed: $msg"
}
if {[catch {report_high_fanout_nets -load_types -max_nets 20 \
        -file [file join $rep_dir soc_high_fanout_synth.rpt]} msg]} {
    puts "WARN: report_high_fanout_nets failed: $msg"
}

opt_design
place_design -directive Explore
phys_opt_design -directive Explore
route_design -directive Explore
phys_opt_design -directive Explore

report_utilization -file [file join $rep_dir soc_utilization_impl.rpt]
report_clock_utilization -file [file join $rep_dir soc_clock_utilization_impl.rpt]
report_timing_summary -delay_type min_max -report_unconstrained \
    -check_timing_verbose -file [file join $rep_dir soc_timing_impl.rpt]
report_timing -delay_type max -max_paths 10 -sort_by group \
    -file [file join $rep_dir soc_timing_worst_paths.rpt]
report_drc -file [file join $rep_dir soc_drc_impl.rpt]

# 门禁与 build_soc.tcl 一致：时序检查无缺项、WNS 非负、DRC 无 Error/Critical Warning。
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

set version_file [open [file join $rep_dir soc_vivado_version.txt] w]
puts $version_file "[version -short] AB $ab_label src=$ab_srcdir clk=$core_clk_mhz profile=$core_profile"
close $version_file
puts "AB BUILD PASSED: label=$ab_label src=$ab_srcdir, core clock $core_clk_mhz MHz, profile=$core_profile, WNS=$wns ns"
