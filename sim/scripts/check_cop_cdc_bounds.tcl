# Read-only signoff of the constraints embedded in a routed checkpoint.
if {[catch {
    if {$argc != 2} {error "usage: checkpoint.dcp report-directory"}
    open_checkpoint [lindex $argv 0]
    set reports [file normalize [lindex $argv 1]]
    file mkdir $reports
    set report [open [file join $reports cdc_bounds.txt] w]
    foreach {source destination budget} {
        aw_hold aw_m1 25.0 wd_hold wd_m1 25.0 ws_hold ws_m1 25.0 ar_hold ar_m1 25.0
        rdata_hold rdata_s1 10.0 bresp_hold bresp_s1 10.0 rresp_hold rresp_s1 10.0
    } {
        set from [get_cells -quiet -hier -regexp ".*pl/inst/axil_cdc/${source}_reg.*"]
        set to [get_cells -quiet -hier -regexp ".*pl/inst/axil_cdc/${destination}_reg.*"]
        if {![llength $from] || ![llength $to]} {error "Missing held payload $source/$destination"}
        set path [get_timing_paths -from $from -to $to -max_paths 1]
        if {[llength $path] != 1} {error "Held payload is falsely cut: $source/$destination"}
        set requirement [get_property REQUIREMENT $path]
        set slack [get_property SLACK $path]
        if {$requirement > $budget+0.001 || $slack < 0} {
            error "Held payload timing failed: $source req=$requirement budget=$budget slack=$slack"
        }
        puts $report "$source->$destination requirement=$requirement budget=$budget slack=$slack"
    }
    close $report
    set skew [report_bus_skew -return_string -file [file join $reports cdc_bus_skew.rpt]]
    if {[regexp {VIOLATED} $skew]} {error "CDC bus skew requirement violated"}
    if {![regexp {MET} $skew]} {error "CDC bus skew report contains no passing path"}
    puts "CDC BOUNDS SIGNOFF PASSED: seven held payload groups timed; bus skew MET"
    close_design
} reason]} {puts stderr "CDC BOUNDS SIGNOFF FAILED: $reason"; exit 1}
exit 0
