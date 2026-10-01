# 2026-10-02 XSA 补导出：对已布线的 vision_hdmi 工程补 bit-in-run + write_hw_platform。
# 与 build_hdmi.tcl 修复段同流程；复现（仓库根）：
#   VIVADO bin/vivado.bat -mode batch -source 本文件
# 不打开 Hardware Manager、不操作板卡。
if {[catch {
    open_project sim/build/hdmi-project/vision_hdmi.xpr
    launch_runs impl_1 -to_step write_bitstream -jobs 2
    wait_on_run impl_1
    if {[get_property PROGRESS [get_runs impl_1]] ne "100%"} { error "HDMI bitstream failed" }
    set runbit [file join [get_property DIRECTORY [get_runs impl_1]] [get_property TOP [current_fileset]].bit]
    file copy -force $runbit sim/build/hdmi-project/vision.bit
    write_hw_platform -fixed -include_bit -force -file sim/build/hdmi-project/vision.xsa
    puts "PASS: HDMI XSA exported with bit and hwh"
} reason]} {
    puts stderr "ERROR: $reason"
    exit 1
}
