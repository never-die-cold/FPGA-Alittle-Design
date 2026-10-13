# Usage: ... -tclargs validate|bitstream [this script's completed-synthesis .xpr]
# Fresh unique projects/reports. Existing HDMI projects and board are untouched.
if {[catch {
    set stage [lindex $argv 0]
    if {$stage ni {validate bitstream}} {error "stage must be validate or bitstream"}
    set tag [clock microseconds]
    set out [file normalize "sim/build/c01-hdmi-$tag"]
    set rep [file normalize "data/logs/2026-10-11-c01-hdmi-$tag"]
    file mkdir $rep
    set reuse [expr {[llength $argv] == 2}]
    if {$reuse} {
        if {$stage ne "bitstream"} {error "reuse requires bitstream stage"}
        set saved [file normalize [lindex $argv 1]]
        set allowed [file normalize sim/build]
        if {![string match "$allowed/c01-hdmi-*/c01_hdmi.xpr" $saved] || ![file isfile $saved]} {
            error "reuse path must be an existing C01 project in sim/build"
        }
        open_project $saved
        if {[get_property NAME [current_project]] ne "c01_hdmi" ||
            [get_property PROGRESS [get_runs synth_1]] ne "100%"} {error "reuse needs completed C01 synthesis"}
        set out [get_property DIRECTORY [current_project]]
        reset_run impl_1
    } else {
    create_project c01_hdmi $out -part xc7z020clg400-1
    set_property target_language Verilog [current_project]
    set_property ip_repo_paths [file normalize sim/build/hdmi-library-full] [current_project]
    update_ip_catalog
    add_files [glob src/vision/*.v]
    }
    puts "BUILD_DIR: $out"
    puts "REPORT_DIR: $rep"
    if {!$reuse} {source sim/scripts/create_capture_hdmi_bd.tcl}
    if {$stage eq "bitstream"} {
        if {!$reuse} {
        set bd [get_files */vision.bd]
        generate_target all $bd
        foreach f [get_files -all -filter {NAME =~ *rx_0*ila*.xdc}] {
            set_property USED_IN_SYNTHESIS false $f
            set_property USED_IN_IMPLEMENTATION false $f
        }
        add_files [make_wrapper -files $bd -top]
        add_files -fileset constrs_1 sim/build/hdmi-source/hdmi_pins.xdc
        foreach xdc {config_cdc capture_cdc} {
            add_files -fileset constrs_1 src/vision/$xdc.xdc
            set_property USED_IN_SYNTHESIS false [get_files $xdc.xdc]
            set_property PROCESSING_ORDER LATE [get_files $xdc.xdc]
        }
        set_property top vision_wrapper [current_fileset]
        update_compile_order -fileset sources_1
        launch_runs synth_1 -jobs 2
        wait_on_run synth_1
        }
        if {[get_property PROGRESS [get_runs synth_1]] ne "100%"} {error "capture HDMI synthesis failed"}
        open_run synth_1
        source sim/scripts/validate_vision_cdc.tcl
        vision_check_cdc 1
        close_design
        launch_runs impl_1 -to_step route_design -jobs 2
        wait_on_run impl_1
        if {[get_property PROGRESS [get_runs impl_1]] ne "100%"} {error "capture HDMI implementation failed"}
        open_run impl_1
        vision_check_cdc 1
        report_utilization -file $rep/utilization.rpt
        report_cdc -details -file $rep/cdc.rpt
        report_drc -file $rep/drc.rpt
        set timing [report_timing_summary -report_unconstrained -return_string -file $rep/timing.rpt]
        if {![string match {*All user specified timing constraints are met.*} $timing]} {error "capture HDMI timing failed"}
        foreach violation [get_drc_violations] {
            if {[get_property SEVERITY $violation] in {Error {Critical Warning}}} {error "blocking DRC $violation"}
        }
        foreach port [get_ports -filter {NAME !~ DDR* && NAME !~ FIXED_IO*}] {
            if {[get_property PACKAGE_PIN $port] eq ""} {error "missing physical pin $port"}
        }
        close_design
        launch_runs impl_1 -to_step write_bitstream -jobs 2
        wait_on_run impl_1
        if {[get_property PROGRESS [get_runs impl_1]] ne "100%"} {error "capture HDMI bitstream failed"}
        set runbit [file join [get_property DIRECTORY [get_runs impl_1]] vision_wrapper.bit]
        file copy $runbit $out/capture-$tag.bit
        set handoff [lindex [get_files */hw_handoff/vision.hwh] 0]
        if {$handoff eq ""} {set handoff [file join $out c01_hdmi.gen sources_1 bd vision hw_handoff vision.hwh]}
        file copy $handoff $out/capture-$tag.hwh
        write_hw_platform -fixed -include_bit -file $out/capture-$tag.xsa
        puts "PASS: C01 display/capture offline bitstream; PS ownership and board acceptance pending"
    }
} reason]} {puts stderr "ERROR: $reason"; exit 1}
