# Full PYNQ-Z2 PS + AXI DMA + RISC-V/CNN implementation gate. Windows Vivado only.
# Prerequisite: pinned sim/build/hdmi-source/ps7_config.tcl and freshly rebuilt cop_job.hex.
if {[catch {
    proc reject_latches {stage} {
        set latches [get_cells -quiet -hier -filter \
            {REF_NAME =~ LDCE || REF_NAME =~ LDPE || REF_NAME =~ LDC || REF_NAME =~ LDP || REF_NAME =~ *LATCH*}]
        if {[llength $latches] != 0} {
            error "$stage latch gate failed: count=[llength $latches] sample=[lrange $latches 0 9]"
        }
    }
    proc gate_cdc_report {text} {
        set rules [list \
            [list single_sync CDC-3 Info 11 \
                {pl/inst/(axil_cdc/(wack_s1|rack_s1|wreq_m1|rreq_m1)_reg|axis_cdc/(rgray_s1|wgray_m1)_reg|dma_(req_c1|kind_c1|ack_s1)_reg)} \
                {named two-stage ASYNC_REG single-bit synchronizers}] \
            [list axil_payload CDC-6 Warning 7 \
                {pl/inst/axil_cdc/(ar_m1|aw_m1|wd_m1|ws_m1)_reg} \
                {source-held AXI-Lite payload sampled after synchronized toggle}] \
            [list fifo_rgray CDC-6 Warning 5 \
                {pl/inst/axis_cdc/rgray_s1_reg} \
                {Gray read pointer two-stage synchronization}] \
            [list fifo_read CDC-15 Warning 73 \
                {pl/inst/axis_cdc/mem_reg.*?/C.*pl/inst/axis_cdc/out_data_reg.*?/D} \
                {73-bit FIFO read port gated by synchronized empty state}]]
        array set id_max {CDC-3 11 CDC-6 7 CDC-15 73}
        array set id_severity {CDC-3 Info CDC-6 Warning CDC-15 Warning}
        array set summary_count {}; array set summary_severity {}; array set detail_count {}; array set hits {}
        foreach rule $rules {set hits([lindex $rule 0]) 0}
        set summary_rows 0; set detail_rows 0
        foreach raw [split $text "\n"] {
            set line [string trim $raw]
            if {[regexp {^(CDC-[0-9]+)[[:space:]]+(Info|Warning|Critical)[[:space:]]+([0-9]+)[[:space:]]+} \
                    $line -> id severity count]} {
                if {[info exists summary_count($id)]} {error "duplicate CDC summary row: $id"}
                set summary_count($id) $count; set summary_severity($id) $severity; incr summary_rows
                continue
            }
            if {![regexp {^[0-9]+[[:space:]]+(CDC-[0-9]+)[[:space:]]+(Info|Warning|Critical)[[:space:]]+} \
                    $line -> id severity]} {continue}
            incr detail_rows; if {![info exists detail_count($id)]} {set detail_count($id) 0}; incr detail_count($id)
            if {$severity eq "Critical"} {error "critical CDC finding: $line"}
            set matched 0
            foreach rule $rules {
                lassign $rule name allowed_id allowed_severity limit path reason
                if {$id eq $allowed_id && $severity eq $allowed_severity && [regexp $path $line]} {
                    incr hits($name); incr matched
                }
            }
            if {$matched != 1} {error "CDC detail is absent from, or ambiguous in, allowlist: $line"}
        }
        if {$summary_rows == 0 || $detail_rows == 0} {error "CDC ID/Severity/Count or detail table not parsed"}
        foreach id [array names summary_count] {
            if {![info exists id_max($id)]} {error "CDC ID not allowlisted: $id"}
            if {$summary_severity($id) ne $id_severity($id)} {error "CDC severity changed: $id=$summary_severity($id)"}
            if {$summary_count($id) > $id_max($id)} {error "CDC count exceeds limit: $id=$summary_count($id)>$id_max($id)"}
            if {![info exists detail_count($id)] || $detail_count($id) != $summary_count($id)} {
                error "CDC summary/detail mismatch: $id"
            }
        }
        foreach id [array names detail_count] {
            if {![info exists summary_count($id)]} {error "CDC detail lacks summary row: $id"}
        }
        foreach rule $rules {
            lassign $rule name allowed_id allowed_severity limit path reason
            if {$hits($name) > $limit} {error "CDC allowlist entry $name exceeds $limit: $hits($name)"}
        }
        set result {}; foreach id [lsort [array names summary_count]] {lappend result "$id=$summary_count($id)"}
        return [join $result ,]
    }
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
    reject_latches SYNTHESIS
    report_utilization -file [file join $rep_dir utilization_synth.rpt]
    report_cdc -details -file [file join $rep_dir cdc_synth.rpt]
    close_design
    launch_runs impl_1 -to_step route_design -jobs 2
    wait_on_run impl_1
    if {[get_property PROGRESS [get_runs impl_1]] ne "100%"} {error "Whole-system implementation failed"}
    open_run impl_1
    reject_latches IMPLEMENTATION
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
    set cdc_counts [gate_cdc_report $cdc]
    set bad_drc [get_drc_violations -quiet -filter {SEVERITY == Error || SEVERITY == "Critical Warning"}]
    if {[llength $bad_drc]} {error "DRC errors or critical warnings: $bad_drc"}
    set summary [open [file join $rep_dir gate_summary.txt] w]
    puts $summary "VIVADO=[version -short]\nWNS_NS=$wns\nDSP=$dsp\nBRAM36=$bram36\nLATCHES=0\nCDC_RULE_COUNTS=$cdc_counts\nCDC_ALLOWLIST_ENTRIES=4\nDRC_BLOCKING=0"
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
    puts "PYNQ COP WHOLE-SYSTEM GATE PASSED: WNS=$wns DSP=$dsp BRAM36=$bram36 CDC_ALLOWLIST=$cdc_counts DRC=0"
    puts "ARTIFACTS: $run_dir/pynq_cop_40mhz.bit $run_dir/pynq_cop_40mhz.hwh"
} reason]} {puts stderr "PYNQ COP WHOLE-SYSTEM GATE FAILED: $reason"; exit 1}
