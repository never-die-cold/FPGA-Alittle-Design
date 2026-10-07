# Complete timing/DRC evidence from the already routed, post-optimization checkpoints.
# vivado -mode batch -source sim/scripts/audit_module1_ooc.tcl -tclargs <new-log-directory>
if {$argc != 1} {error "Expected new evidence directory"}
set root [file normalize [file join [file dirname [info script]] ../..]]
set out [file normalize [lindex $argv 0]]
if {[file exists $out]} {error "Refusing to overwrite evidence: $out"}
file mkdir $out
set vf [open [file join $out vivado_version.txt] w]
puts $vf [version]
close $vf
foreach label {v1_nofwd_10ns_postopt v1_fwd_10ns_postopt v1_bht1_10ns_postopt v1_bht2_10ns_postopt v1_bht2_11p52_postopt} {
    open_checkpoint [file join $root build run fmax $label post_route.dcp]
    set dir [file join $out $label]
    file mkdir $dir
    report_timing_summary -delay_type min_max -check_timing_verbose -file [file join $dir timing.rpt]
    report_clock_utilization -file [file join $dir clocks.rpt]
    report_drc -file [file join $dir drc.rpt]
    set checks {no_clock constant_clock unconstrained_internal_endpoints generated_clocks loops}
    set fh [open [file join $dir check_timing.rpt] w]
    puts $fh [check_timing -override_defaults $checks -verbose -return_string]
    close $fh
    set bad [get_drc_violations -quiet -filter {SEVERITY == Error || SEVERITY == "Critical Warning"}]
    if {[llength $bad]} {error "Critical DRC in $label: $bad"}
    set setup [get_property SLACK [get_timing_paths -delay_type max -max_paths 1]]
    set hold [get_property SLACK [get_timing_paths -delay_type min -max_paths 1]]
    if {$hold < 0} {error "Hold failure in $label: $hold"}
    if {$label eq "v1_bht2_11p52_postopt" && $setup < 0} {error "BHT2 minimum timing gate failed"}
    puts "AUDIT: $label setup=$setup hold=$hold critical_drc=0"
    close_design
}
puts "PASS: five OOC checkpoints hold/DRC audit; BHT2 11.520ns setup gate"
# Establish a passing point for the default forwarding and 1-bit profiles too.
# Fixed route from the 10ns run: re-run STA at 11.520ns, without resynthesis/reroute.
foreach label {v1_fwd_10ns_postopt v1_bht1_10ns_postopt} {
    open_checkpoint [file join $root build run fmax $label post_route.dcp]
    create_clock -name sys_clk -period 11.520 [get_ports clk]
    set name [string map {10ns 11p52_fixedroute} $label]
    set dir [file join $out $name]
    file mkdir $dir
    report_timing_summary -delay_type min_max -check_timing_verbose -file [file join $dir timing.rpt]
    report_clock_utilization -file [file join $dir clocks.rpt]
    report_drc -file [file join $dir drc.rpt]
    set setup [get_property SLACK [get_timing_paths -delay_type max -max_paths 1]]
    set hold [get_property SLACK [get_timing_paths -delay_type min -max_paths 1]]
    if {$setup < 0 || $hold < 0} {error "Timing gate failed: $name"}
    puts "FIXED_ROUTE: $name setup=$setup hold=$hold period=11.520"
    close_design
}
puts "PASS: forwarding and BHT1 fixed-route 11.520ns STA gates"
