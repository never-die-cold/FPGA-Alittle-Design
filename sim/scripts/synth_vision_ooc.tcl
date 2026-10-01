# 模块二 OOC 综合脚本（不上板，仅资源/时序基线）
# 用法：vivado -mode batch -source sim/scripts/synth_vision_ooc.tcl -tclargs <module> [variant]
#   module  ∈ {rgb2gray, gaussian_3x3, sobel, scaler, line_buffer, vision_top}
#   variant ∈ {unit(默认), real, real75}
#     unit：单元级参数（WIDTH=16/HEIGHT=8/NLINES=16），第一批基线口径；
#     real：720p 行宽参数（WIDTH=1280/HEIGHT=720；scaler 目标 224×224，NLINES=8——
#           行步进 720/224=3.2 <= NLINES-2=6 成立；8 槽减少选择逻辑与 BRAM，
#           实测关键路径仍为两级 lerp，减少槽数未改善时序，2026-09-30），
#           验证 BRAM 推断与真实时序，模块三输入尺寸拍板前用 224 占位。10ns 约束。
#     real75：参数同 real，时钟约束改 13.468ns（= 720p60 像素钟 74.25 MHz）——
#           720p60 达标随访档：WNS >= 0 即该模块 720p60 达标（2026-10-01 新增）。
#   vision_top（2026-10-01 新增）：全链顶层 OOC——双时钟（pclk 13.468/10ns + s_axi_aclk
#           10ns）+ 异步 clock group（R0 位 2FF 同步器为跨域路径），并出 report_cdc 验证
#           同步器识别；仅 real/real75 档（单元档无意义）。
# 输出：build/reports/vision_ooc/<mod>[_<variant>]_{utilization,timing}.rpt 与 _ooc_result.txt
if {$argc < 1} { puts "ERROR: 需要 -tclargs <module> [variant]"; exit 1 }
set mod     [lindex $argv 0]
set variant [expr {$argc >= 2 ? [lindex $argv 1] : "unit"}]
set part xc7z020clg400-1
set rep  build/reports/vision_ooc
file mkdir $rep
set suffix [expr {$variant eq "unit" ? "" : "_$variant"}]
set period [expr {$variant eq "real75" ? 13.468 : 10.0}]

if {$mod eq "vision_top"} {
    set files [list src/vision/rgb2gray.v src/vision/line_buffer.v src/vision/gaussian_3x3.v \
                    src/vision/sobel.v src/vision/scaler.v src/vision/osd_overlay.v \
                    src/vision/axi_regs.v src/vision/in_align.v src/vision/cop_buf.v \
                    src/vision/vision_top.v]
} else {
    set files [list src/vision/${mod}.v]
    if {$mod eq "gaussian_3x3" || $mod eq "sobel" || $mod eq "scaler"} {
        lappend files src/vision/line_buffer.v
    }
}
foreach f $files { read_verilog $f }

set synth_args [list synth_design -top $mod -part $part -mode out_of_context]
if {$variant eq "real" || $variant eq "real75"} {
    switch $mod {
        gaussian_3x3 { foreach g {WIDTH=1280 HEIGHT=720} { lappend synth_args -generic $g } }
        sobel        { foreach g {WIDTH=1280 HEIGHT=720} { lappend synth_args -generic $g } }
        scaler       { foreach g {SW=1280 SH=720 DW=224 DH=224 NLINES=8} { lappend synth_args -generic $g } }
        line_buffer  { foreach g {WIDTH=1280} { lappend synth_args -generic $g } }
        vision_top   { foreach g {SW=1280 SH=720 DW=224 DH=224 NLINES=8} { lappend synth_args -generic $g } }
    }
}
eval $synth_args

if {$mod eq "vision_top"} {
    create_clock -name pclk      -period $period [get_ports clk]
    create_clock -name s_axi_aclk -period 10.0   [get_ports s_axi_aclk]
    set_clock_groups -asynchronous -group [get_clocks pclk] -group [get_clocks s_axi_aclk]
    report_cdc -file $rep/${mod}${suffix}_cdc.rpt
} else {
    create_clock -name clk -period $period [get_ports clk]
}

report_utilization    -file $rep/${mod}${suffix}_utilization.rpt
report_timing_summary -file $rep/${mod}${suffix}_timing.rpt
set wns [get_property SLACK [lindex [get_timing_paths] 0]]
set fp [open $rep/${mod}${suffix}_ooc_result.txt w]
puts $fp "module=$mod variant=$variant period=${period}ns wns=$wns"
close $fp
puts "OOC_RESULT module=$mod variant=$variant period=${period}ns wns=$wns"
