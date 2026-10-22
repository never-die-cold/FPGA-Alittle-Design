# Full PYNQ-Z2 PS + AXI DMA + RISC-V/CNN implementation gate. Windows Vivado only.
# Prerequisite: pinned sim/build/hdmi-source/ps7_config.tcl and freshly rebuilt cop_job.hex.
if {[catch {
    set script_dir [file normalize [file dirname [info script]]]
    set root [file normalize [file join $script_dir ..]]
    set run_dir [file join $script_dir run pynq_cop_40mhz]
    set rep_dir [file join $script_dir reports pynq_cop_40mhz]
    set project_dir [file join $run_dir project]
    file mkdir $run_dir; file mkdir $rep_dir; cd $root
    if {![file isfile sim/build/hdmi-source/ps7_config.tcl]} {
        error "Missing pinned PYNQ PS preset; run sim/scripts/prepare_hdmi_sources.py first"
    }
    foreach source {src/riscv_fw/cop_job.c src/riscv_fw/cop_work_order.h src/riscv_fw/start.S} {
        if {[file mtime src/riscv_fw/cop_job.hex] < [file mtime $source]} {
            error "cop_job.hex is stale; rebuild it with the selected RISC-V toolchain"
        }
    }
    create_project -force pynq_cop_40mhz $project_dir -part xc7z020clg400-1
    set_property target_language Verilog [current_project]
    add_files [concat [glob src/riscv/*.v] [glob src/coprocessor/*.v]]
    source build/create_pynq_cop_bd.tcl
    set bd [get_files */cop_system.bd]
    generate_target all $bd
    add_files [make_wrapper -files $bd -top]
    add_files -fileset constrs_1 build/constraints/pynq_cop_board.xdc
    set_property PROCESSING_ORDER LATE [get_files pynq_cop_board.xdc]
    set_property top cop_system_wrapper [current_fileset]
    update_compile_order -fileset sources_1
    launch_runs synth_1 -jobs 2
    wait_on_run synth_1
    if {[get_property PROGRESS [get_runs synth_1]] ne "100%"} {error "Whole-system synthesis failed"}
    open_run synth_1
    report_utilization -file [file join $rep_dir utilization_synth.rpt]
    report_cdc -details -file [file join $rep_dir cdc_synth.rpt]
    close_design
    launch_runs impl_1 -to_step route_design -jobs 2
    wait_on_run impl_1
    if {[get_property PROGRESS [get_runs impl_1]] ne "100%"} {error "Whole-system implementation failed"}
    open_run impl_1
    report_utilization -file [file join $rep_dir utilization_impl.rpt]
    report_clock_utilization -file [file join $rep_dir clock_utilization_impl.rpt]
    set timing [report_timing_summary -delay_type min_max -report_unconstrained \
        -check_timing_verbose -return_string -file [file join $rep_dir timing_impl.rpt]]
    set cdc [report_cdc -details -return_string -file [file join $rep_dir cdc_impl.rpt]]
    report_drc -file [file join $rep_dir drc_impl.rpt]
    set checks {no_clock constant_clock unconstrained_internal_endpoints generated_clocks}
    set checked [check_timing -override_defaults $checks -verbose -return_string]
    set fh [open [file join $rep_dir check_timing.rpt] w]; puts $fh $checked; close $fh
    foreach check $checks {
        if {![regexp [format {checking %s \(0\)} $check] $checked]} {error "Timing check failed: $check"}
    }
    set path [get_timing_paths -delay_type max -max_paths 1]
    if {[llength $path] != 1} {error "No setup path found"}
    set wns [get_property SLACK [lindex $path 0]]
    if {![string is double -strict $wns] || $wns < 0} {error "Setup timing failed: WNS=$wns ns"}
    set dsp [llength [get_cells -hier -filter {REF_NAME =~ DSP48*}]]
    set ram36 [llength [get_cells -hier -filter {REF_NAME =~ RAMB36*}]]
    set ram18 [llength [get_cells -hier -filter {REF_NAME =~ RAMB18*}]]
    set bram36 [expr {$ram36+0.5*$ram18}]
    if {$dsp>220 || $bram36>140} {error "Resource gate failed: DSP=$dsp BRAM36=$bram36"}
    set syncs [get_cells -hier -filter {ASYNC_REG == 1}]
    if {[llength $syncs] < 20} {error "CDC structural gate failed: only [llength $syncs] ASYNC_REG cells"}
    set unsafe -1; set unknown -1
    foreach pattern {{Unsafe[^0-9\n]*([0-9]+)} {Unsafe[^\n]*\|[ ]*([0-9]+)}} {
        if {[regexp -nocase $pattern $cdc -> unsafe]} {break}
    }
    foreach pattern {{Unknown[^0-9\n]*([0-9]+)} {Unknown[^\n]*\|[ ]*([0-9]+)}} {
        if {[regexp -nocase $pattern $cdc -> unknown]} {break}
    }
    if {$unsafe<0 || $unknown<0} {error "CDC summary format unrecognized; refusing to waive review"}
    if {$unsafe!=0 || $unknown!=0} {error "CDC gate failed: unsafe=$unsafe unknown=$unknown"}
    set bad_drc [get_drc_violations -quiet -filter {SEVERITY == Error || SEVERITY == "Critical Warning"}]
    if {[llength $bad_drc]} {error "DRC errors or critical warnings: $bad_drc"}
    set summary [open [file join $rep_dir gate_summary.txt] w]
    puts $summary "VIVADO=[version -short]\nWNS_NS=$wns\nDSP=$dsp\nBRAM36=$bram36\nCDC_UNSAFE=$unsafe\nCDC_UNKNOWN=$unknown\nDRC_BLOCKING=0"
    close $summary
    close_design
    launch_runs impl_1 -to_step write_bitstream -jobs 2
    wait_on_run impl_1
    if {[get_property PROGRESS [get_runs impl_1]] ne "100%"} {error "Bitstream generation failed"}
    set bit [file join [get_property DIRECTORY [get_runs impl_1]] cop_system_wrapper.bit]
    set hwh [lindex [get_files */hw_handoff/cop_system.hwh] 0]
    if {![file isfile $bit] || ![file isfile $hwh]} {error "Gate passed but bitstream/hwh is missing"}
    file copy -force $bit [file join $run_dir pynq_cop_40mhz.bit]
    file copy -force $hwh [file join $run_dir pynq_cop_40mhz.hwh]
    write_hw_platform -fixed -include_bit -force -file [file join $run_dir pynq_cop_40mhz.xsa]
    puts "PYNQ COP WHOLE-SYSTEM GATE PASSED: WNS=$wns DSP=$dsp BRAM36=$bram36 CDC=0 DRC=0"
    puts "ARTIFACTS: $run_dir/pynq_cop_40mhz.bit $run_dir/pynq_cop_40mhz.hwh"
} reason]} {puts stderr "PYNQ COP WHOLE-SYSTEM GATE FAILED: $reason"; exit 1}
