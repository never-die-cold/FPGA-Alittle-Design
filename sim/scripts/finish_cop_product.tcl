# Resume a routed product DCP into a new directory; never rebuild or overwrite.
# vivado -mode batch -source <this> -tclargs <routed.dcp> <imem.hex> <output-dir>
if {[catch {
    if {[llength $argv] != 3} {error "need routed.dcp imem.hex output-dir"}
    lassign $argv dcp imem out
    if {[file exists $out]} {error "output already exists: $out"}
    file mkdir $out
    open_checkpoint $dcp
    source sim/scripts/validate_vision_cdc.tcl
    vision_check_cdc 1 raw_capture
    set fh [open $imem r]; set words [split [string trim [read $fh]] \n]; close $fh
    if {[llength $words] != 8192} {error "expected materialized 8192-word IMEM"}
    set lanes [get_cells -quiet -hier -filter {REF_NAME == RAMB36E1 && NAME =~ */soc/u_imem/rdata_reg_*}]
    if {[llength $lanes] != 8} {error "IMEM must have eight RAMB36 lanes"}
    foreach cell $lanes {
        if {![regexp {rdata_reg_([0-7])$} $cell -> lane]} {error "unknown IMEM lane: $cell"}
        for {set block 0} {$block < 128} {incr block} {
            set raw [get_property [format INIT_%02X $block] $cell]
            if {![regexp -nocase {'h([0-9a-f]+)$} $raw -> digits]} {error "unknown INIT encoding"}
            set digits [format %064s $digits]
            for {set nibble 0} {$nibble < 64} {incr nibble} {
                set index [expr {$block*64+$nibble}]
                set expected [string index [string trim [lindex $words $index]] [expr {7-$lane}]]
                if {![string equal -nocase $expected [string index $digits [expr {63-$nibble}]]]} {
                    error "IMEM differs from build input at word $index lane $lane"
                }
            }
        }
    }
    puts "IMEM EXACT MATCH: all 8192 words match materialized build input"
    set cop_cells [get_cells -quiet -hier -filter {NAME =~ */pl/inst}]
    if {[llength $cop_cells] != 1} {error "cop hierarchy absent"}
    set cdc [report_cdc -cells $cop_cells -details -return_string -file $out/cdc_cop.rpt]
    if {[regexp -line {^[[:space:]]*CDC-[0-9]+[[:space:]]+Critical[[:space:]]+[1-9]} $cdc]} {
        error "critical cop CDC finding"
    }
    foreach {a b budget} {
        aw_hold aw_m1 25 wd_hold wd_m1 25 ws_hold ws_m1 25 ar_hold ar_m1 25
        rdata_hold rdata_s1 10 bresp_hold bresp_s1 10 rresp_hold rresp_s1 10
    } {
        set from [get_cells -quiet -hier -regexp ".*pl/inst/axil_cdc/${a}_reg.*"]
        set to [get_cells -quiet -hier -regexp ".*pl/inst/axil_cdc/${b}_reg.*"]
        if {![llength $from] || ![llength $to]} {error "CDC bundle absent: $a $b"}
        set paths [get_timing_paths -quiet -from $from -to $to -max_paths 1]
        if {![llength $paths]} {error "CDC payload is cut: $a"}
        set p [lindex $paths 0]
        if {[get_property REQUIREMENT $p]>$budget+0.001 || [get_property SLACK $p]<0} {
            error "CDC payload timing failed: $a"
        }
    }
    report_bus_skew -file $out/bus_skew.rpt
    report_timing_summary -delay_type min_max -report_unconstrained -file $out/timing.rpt
    set wns [get_property SLACK [get_timing_paths -delay_type max -max_paths 1]]
    set whs [get_property SLACK [get_timing_paths -delay_type min -max_paths 1]]
    if {$wns<0 || $whs<0} {error "setup/hold timing failed: $wns/$whs"}
    set latches [get_cells -quiet -hier -filter {REF_NAME =~ LDCE || REF_NAME =~ LDPE}]
    if {[llength $latches]} {error "latches present"}
    report_utilization -file $out/utilization.rpt
    report_drc -file $out/drc.rpt
    set bad [get_drc_violations -quiet -filter {SEVERITY == Error || SEVERITY == "Critical Warning"}]
    if {[llength $bad]} {error "blocking DRC: $bad"}
    set fh [open $out/gate_summary.txt w]
    puts $fh "DCP=[file normalize $dcp]\nWNS_NS=$wns\nWHS_NS=$whs\nIMEM_EXACT_WORDS=8192\nVISION_PROFILE=raw_capture\nLATCHES=0\nDRC_BLOCKING=0"
    close $fh
    write_bitstream -file $out/pynq_cop_40mhz.bit
    puts "PRODUCT BIT WRITTEN: $out/pynq_cop_40mhz.bit"
} reason]} {puts stderr "PRODUCT RESUME FAILED: $reason"; exit 1}
exit 0
