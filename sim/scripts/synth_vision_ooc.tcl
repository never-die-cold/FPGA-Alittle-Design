# 模块二 OOC 综合脚本（不上板，仅资源/时序基线）
# 用法：vivado -mode batch -source sim/scripts/synth_vision_ooc.tcl -tclargs <module> [variant]
#   module  ∈ {rgb2gray, gaussian_3x3, sobel, scaler, line_buffer}
#   variant ∈ {unit(默认), real}
#     unit：单元级参数（WIDTH=16/HEIGHT=8/NLINES=16），第一批基线口径；
#     real：720p 行宽参数（WIDTH=1280/HEIGHT=720；scaler 目标 224×224，NLINES=16），
#           验证 BRAM 推断与真实时序，模块三输入尺寸拍板前用 224 占位。
# 输出：build/reports/vision_ooc/<mod>[_<variant>]_{utilization,timing}.rpt 与 _ooc_result.txt
if {$argc < 1} { puts "ERROR: 需要 -tclargs <module> [variant]"; exit 1 }
set mod     [lindex $argv 0]
set variant [expr {$argc >= 2 ? [lindex $argv 1] : "unit"}]
set part xc7z020clg400-1
set rep  build/reports/vision_ooc
file mkdir $rep
set suffix [expr {$variant eq "unit" ? "" : "_$variant"}]

set files [list src/vision/${mod}.v]
if {$mod eq "gaussian_3x3" || $mod eq "sobel" || $mod eq "scaler"} {
    lappend files src/vision/line_buffer.v
}
foreach f $files { read_verilog $f }

set synth_args [list synth_design -top $mod -part $part -mode out_of_context]
if {$variant eq "real"} {
    switch $mod {
        gaussian_3x3 { foreach g {WIDTH=1280 HEIGHT=720} { lappend synth_args -generic $g } }
        sobel        { foreach g {WIDTH=1280 HEIGHT=720} { lappend synth_args -generic $g } }
        scaler       { foreach g {SW=1280 SH=720 DW=224 DH=224 NLINES=16} { lappend synth_args -generic $g } }
        line_buffer  { foreach g {WIDTH=1280} { lappend synth_args -generic $g } }
    }
}
eval $synth_args
create_clock -name clk -period 10.0 [get_ports clk]

report_utilization    -file $rep/${mod}${suffix}_utilization.rpt
report_timing_summary -file $rep/${mod}${suffix}_timing.rpt
set wns [get_property SLACK [lindex [get_timing_paths] 0]]
set fp [open $rep/${mod}${suffix}_ooc_result.txt w]
puts $fp "module=$mod variant=$variant period=10.0ns wns=$wns"
close $fp
puts "OOC_RESULT module=$mod variant=$variant period=10.0ns wns=$wns"
