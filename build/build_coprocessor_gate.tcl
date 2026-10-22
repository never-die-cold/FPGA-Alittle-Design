# Coprocessor OOC synthesis/implementation gate. Windows Vivado only; no project is created.
# Usage: vivado -mode batch -source build/build_coprocessor_gate.tcl -tclargs ?40|100? ?compute|storage?
set script_dir [file normalize [file dirname [info script]]]
set root [file normalize [file join $script_dir ..]]
set part xc7z020clg400-1
set freq 40
set target compute
if {$argc >= 1} {set freq [lindex $argv 0]}
if {$argc >= 2} {set target [lindex $argv 1]}
if {$argc > 2} {error "Usage: build_coprocessor_gate.tcl ?40|100? ?compute|storage?"}
switch -- $freq {
    40  {set core_period 25.000; set cop_period 25.000}
    100 {set core_period 25.000; set cop_period 10.000}
    default {error "Unsupported coprocessor profile: $freq MHz (choose 40 or 100)"}
}
switch -- $target {
    compute {set top cop_top; set constraint coprocessor_ooc.xdc}
    storage {set top cop_bram_storage; set constraint coprocessor_storage_ooc.xdc}
    default {error "Unsupported target: $target (choose compute or storage)"}
}
set profile [file join ${freq}mhz $target]
set run_dir [file join $script_dir run coprocessor $profile]
set rep_dir [file join $script_dir reports coprocessor $profile]
file mkdir $run_dir
file mkdir $rep_dir
cd $root

foreach f [lsort [glob [file join $root src coprocessor *.v]]] {read_verilog $f}
read_xdc [file join $script_dir constraints $constraint]
synth_design -top $top -part $part -mode out_of_context
write_checkpoint -force [file join $run_dir post_synth.dcp]
report_utilization -file [file join $rep_dir utilization_synth.rpt]
report_timing_summary -delay_type min_max -report_unconstrained -check_timing_verbose \
    -file [file join $rep_dir timing_synth.rpt]
report_cdc -file [file join $rep_dir cdc_synth.rpt]

opt_design
place_design -directive Explore
phys_opt_design -directive Explore
route_design -directive Explore
write_checkpoint -force [file join $run_dir post_route.dcp]
report_utilization -file [file join $rep_dir utilization_impl.rpt]
report_clock_utilization -file [file join $rep_dir clock_utilization_impl.rpt]
report_timing_summary -delay_type min_max -report_unconstrained -check_timing_verbose \
    -file [file join $rep_dir timing_impl.rpt]
report_timing -delay_type max -max_paths 20 -sort_by group \
    -file [file join $rep_dir timing_worst_paths.rpt]
report_cdc -file [file join $rep_dir cdc_impl.rpt]
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
set bad_drc [get_drc_violations -quiet -filter {SEVERITY == Error || SEVERITY == "Critical Warning"}]
if {[llength $bad_drc]} {error "DRC errors or critical warnings: $bad_drc"}
set fh [open [file join $rep_dir vivado_version.txt] w]; puts $fh [version -short]; close $fh
puts "COPROCESSOR GATE PASSED: profile=$profile top=$top WNS=$wns reports=$rep_dir"
