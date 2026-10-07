# Offline full PYNQ-Z2 HDMI build. Never opens a hardware target.
if {[catch {
    set out sim/build/hdmi-project
    if {[info exists ::env(VISION_HDMI_OUT)]} {set out $::env(VISION_HDMI_OUT)}
    create_project -force vision_hdmi $out -part xc7z020clg400-1
    set_property target_language Verilog [current_project]
    set_property ip_repo_paths [file normalize sim/build/hdmi-library-full] [current_project]
    update_ip_catalog
    add_files [glob src/vision/*.v]
    source sim/scripts/create_hdmi_bd.tcl
    set bd [get_files */vision.bd]
    generate_target all $bd
    # Upstream debug=false still packages unused legacy ILA constraints.
    # Disable only those debug-only files, preserve actual RX clock/IO constraints.
    foreach f [get_files -all -filter {NAME =~ *rx_0*ila*.xdc}] {
        set_property USED_IN_SYNTHESIS false $f
        set_property USED_IN_IMPLEMENTATION false $f
    }
    add_files [make_wrapper -files $bd -top]
    add_files -fileset constrs_1 sim/build/hdmi-source/hdmi_pins.xdc
    add_files -fileset constrs_1 src/vision/config_cdc.xdc
    set_property USED_IN_SYNTHESIS false [get_files config_cdc.xdc]
    set_property PROCESSING_ORDER LATE [get_files config_cdc.xdc]
    set_property top vision_wrapper [current_fileset]
    update_compile_order -fileset sources_1
    launch_runs synth_1 -jobs 2
    wait_on_run synth_1
    if {[get_property PROGRESS [get_runs synth_1]] ne "100%"} { error "HDMI synthesis failed" }
    launch_runs impl_1 -to_step route_design -jobs 2
    wait_on_run impl_1
    if {[get_property PROGRESS [get_runs impl_1]] ne "100%"} { error "HDMI implementation failed" }
    open_run impl_1
    set rep data/logs/2026-10-02-vision-offboard/hdmi
    if {[info exists ::env(VISION_HDMI_EVDIR)]} {set rep $::env(VISION_HDMI_EVDIR)}
    file mkdir $rep
    report_utilization -file $rep/utilization.rpt
    report_cdc -details -file $rep/cdc.rpt
    report_drc -file $rep/drc.rpt
    set timing [report_timing_summary -report_unconstrained -return_string -file $rep/timing.rpt]
    if {![string match {*All user specified timing constraints are met.*} $timing]} { error "HDMI timing failed" }
    foreach violation [get_drc_violations] {
        if {[get_property SEVERITY $violation] in {Error {Critical Warning}}} { error "blocking HDMI DRC $violation" }
    }
    foreach port [get_ports -filter {NAME !~ DDR* && NAME !~ FIXED_IO*}] {
        if {[get_property PACKAGE_PIN $port] eq ""} { error "missing physical pin $port" }
    }
    # bit 必须落在工程 run 目录 write_hw_platform 才取得到（2026-10-02 教训：
    # write_bitstream 写自定义路径后导出报 Common 17-69）；bitgen 经 launch_runs
    # 入 run 目录，再复制一份到 $out 供 PYNQ 直取。
    close_design
    launch_runs impl_1 -to_step write_bitstream -jobs 2
    wait_on_run impl_1
    if {[get_property PROGRESS [get_runs impl_1]] ne "100%"} { error "HDMI bitstream failed" }
    set runbit [file join [get_property DIRECTORY [get_runs impl_1]] [get_property TOP [current_fileset]].bit]
    file copy -force $runbit $out/vision.bit
    write_hw_platform -fixed -include_bit -force -file $out/vision.xsa
    puts "PASS: PYNQ-Z2 HDMI physical route and bitstream (offline; board validation pending)"
} reason]} {
    puts stderr "ERROR: $reason"
    exit 1
}
