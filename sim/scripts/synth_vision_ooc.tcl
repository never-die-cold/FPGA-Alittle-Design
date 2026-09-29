# 模块二 OOC 综合脚本（不上板，仅资源/时序基线）
# 用法：vivado -mode batch -source sim/scripts/synth_vision_ooc.tcl -tclargs <module>
#   module ∈ {rgb2gray, gaussian_3x3, sobel, scaler}
# 输出：build/reports/vision_ooc/<mod>_utilization.rpt / <mod>_timing.rpt
if {$argc < 1} { puts "ERROR: 需要 -tclargs <module>"; exit 1 }
set mod  [lindex $argv 0]
set part xc7z020clg400-1
set rep  build/reports/vision_ooc
file mkdir $rep

set files [list src/vision/${mod}.v]
if {$mod eq "gaussian_3x3" || $mod eq "sobel" || $mod eq "scaler"} {
    lappend files src/vision/line_buffer.v
}
foreach f $files { read_verilog $f }

synth_design -top $mod -part $part -mode out_of_context
create_clock -name clk -period 10.0 [get_ports clk]

report_utilization    -file $rep/${mod}_utilization.rpt
report_timing_summary -file $rep/${mod}_timing.rpt
set wns [get_property SLACK [lindex [get_timing_paths] 0]]
set fp [open $rep/${mod}_ooc_result.txt w]
puts $fp "module=$mod period=10.0ns wns=$wns"
close $fp
puts "OOC_RESULT module=$mod period=10.0ns wns=$wns"
