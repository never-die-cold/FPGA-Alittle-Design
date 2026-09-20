# Run in Windows Vivado; never opens Hardware Manager or programs a board.
set smoke_dir [file normalize [file join [file dirname [info script]] ..]]

proc require_complete {run_name expected_status} {
    set run [get_runs $run_name]
    set status [get_property STATUS $run]
    if {$status ne $expected_status || [get_property PROGRESS $run] ne "100%"} {
        error "$run_name failed or incomplete: $status"
    }
}

proc check_ports {} {
    # Verify exact port set AND exact official mapping, not merely nonempty LOC.
    set mapping [list clk H16 btn0 D19 {led[0]} R14 {led[1]} P14 {led[2]} N16 {led[3]} M14]
    if {[llength [get_ports]] != 6} {error "Expected exactly six top-level port bits"}
    foreach {name pin} $mapping {
        set port [get_ports -quiet [list $name]]
        if {[llength $port] != 1} {error "Missing port: $name"}
        if {[get_property PACKAGE_PIN $port] ne $pin ||
            [get_property IOSTANDARD $port] ne "LVCMOS33"} {
            error "Missing or incorrect pin/IOSTANDARD constraint: $name"
        }
    }
    set clocks [get_clocks -quiet -of_objects [get_ports clk]]
    if {[llength $clocks] != 1} {error "clk must have exactly one clock constraint"}
    if {abs([get_property PERIOD $clocks] - 8.0) > 0.000001} {
        error "Expected official 125 MHz / 8 ns clock"
    }
    if {[llength [all_registers]] != [llength [all_registers -clock $clocks]]} {
        error "Found registers not timed by the board clock"
    }
}

if {[catch {
    if {$::tcl_platform(platform) ne "windows"} {
        error "This build requires Windows; output root is C:/fpga_build/pynq_z2_smoke"
    }
    set build_root C:/fpga_build/pynq_z2_smoke
    # A new subdirectory on every invocation avoids overwriting earlier builds.
    set run_dir [file join $build_root [format "run_%s_%s" [clock format [clock seconds] -format %Y%m%d_%H%M%S] [pid]]]
    if {[file exists $run_dir]} {error "Build directory already exists: $run_dir"}
    create_project pynq_z2_smoke $run_dir -part xc7z020clg400-1
    set_property target_language Verilog [current_project]
    add_files -norecurse [file join $smoke_dir rtl pynq_z2_smoke_top.v]
    set_property file_type Verilog [get_files *pynq_z2_smoke_top.v]
    add_files -fileset constrs_1 -norecurse [file join $smoke_dir constraints pynq_z2_smoke.xdc]
    set_property top pynq_z2_smoke_top [get_filesets sources_1]
    update_compile_order -fileset sources_1
    launch_runs synth_1 -jobs 2
    wait_on_run synth_1
    require_complete synth_1 "synth_design Complete!"
    open_run synth_1
    check_ports
    close_design

    # Stop at routing so timing and constraints are checked BEFORE bitstream.
    launch_runs impl_1 -to_step route_design -jobs 2
    wait_on_run impl_1
    require_complete impl_1 "route_design Complete!"
    open_run impl_1
    check_ports
    report_utilization -file [file join $run_dir utilization.rpt]
    set summary [report_timing_summary -delay_type min_max -report_unconstrained \
        -check_timing_verbose -return_string -file [file join $run_dir timing.rpt]]
    # The summary includes setup, hold and pulse-width constraints.
    # Missing/unrecognized pass text is a failure, never an assumed pass.
    if {![string match {*All user specified timing constraints are met.*} $summary]} {
        error "Timing did not pass; inspect $run_dir/timing.rpt"
    }
    foreach delay {max min} {
        set paths [get_timing_paths -delay_type $delay -max_paths 1]
        if {[llength $paths] == 0} {error "No $delay timing paths found"}
        set slack [get_property SLACK [lindex $paths 0]]
        if {![string is double -strict $slack] || $slack < 0} {
            error "Timing failure: $delay slack=$slack"
        }
    }
    report_drc -file [file join $run_dir drc.rpt]
    set violations [get_drc_violations -quiet -filter {SEVERITY == Error || SEVERITY == "Critical Warning"}]
    if {[llength $violations] != 0} {error "DRC errors/critical warnings: $violations"}
    # write_bitstream performs its own final DRC; no severity downgrades.
    set bitstream [file normalize [file join $run_dir pynq_z2_smoke.bit]]
    write_bitstream $bitstream
    if {![file isfile $bitstream] || [file size $bitstream] == 0} {
        error "Bitstream missing or empty"
    }
    puts "BUILD PASSED"
    puts "BITSTREAM: $bitstream"
    close_project
} message options]} {
    puts stderr "BUILD FAILED: $message"
    if {[dict exists $options -errorinfo]} {puts stderr [dict get $options -errorinfo]}
    exit 1
}
