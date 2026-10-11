# Read a completed routed checkpoint; never modifies the project or board.
if {[catch {
    if {[llength $argv] != 2} {error "usage: routed.dcp report-file"}
    set checkpoint [file normalize [lindex $argv 0]]
    set report [file normalize [lindex $argv 1]]
    set root [file normalize sim/build]
    set logs [file normalize data/logs]
    if {![string match "$root/c01-hdmi-*/c01_hdmi.runs/impl_1/*_routed.dcp" $checkpoint] || ![file isfile $checkpoint]} {error "checkpoint must be a routed C01 build"}
    if {![string match "$logs/*" $report] || [file exists $report]} {error "report must be a new repository log"}
    open_checkpoint $checkpoint
    report_bus_skew -file $report
    puts "PASS: bus skew report generated; review slack before acceptance"
} reason]} {puts stderr "ERROR: $reason"; exit 1}