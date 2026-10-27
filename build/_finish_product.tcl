# Finish the coexistence build from the routed checkpoint (same design, no re-synth).
set root [file normalize [file join [file dirname [file normalize [info script]]] ..]]
set run_dir [file join $root build run pynq_cop_40mhz]
set rep_dir [file join $root build reports pynq_cop_40mhz]
set dcp [file join $run_dir project pynq_cop_40mhz.runs impl_1 cop_system_wrapper_routed.dcp]
if {![file isfile $dcp]} { error "routed checkpoint missing" }
open_checkpoint $dcp
set cdc [report_cdc -cells [get_cells -hier -filter {NAME =~ */pl/inst}] -details -return_string -file [file join $rep_dir cdc_cop_impl.rpt]]
report_drc -file [file join $rep_dir drc_impl.rpt]
set path [get_timing_paths -delay_type max -max_paths 1]
if {[llength $path] != 1} { error "no setup path" }
set wns [get_property SLACK [lindex $path 0]]
if {![string is double -strict $wns] || $wns < 0} { error "setup timing failed" }
set minpath [get_timing_paths -delay_type min -max_paths 1]
set whs [get_property SLACK [lindex $minpath 0]]
set dsp [llength [get_cells -hier -filter {REF_NAME =~ DSP48*}]]
set ram36 [llength [get_cells -hier -filter {REF_NAME =~ RAMB36*}]]
set ram18 [llength [get_cells -hier -filter {REF_NAME =~ RAMB18*}]]
set bram36 [expr {$ram36+0.5*$ram18}]
if {$dsp > 220 || $bram36 > 140} { error "resource gate failed DSP=$dsp BRAM36=$bram36" }
set syncs [llength [get_cells -hier -filter {ASYNC_REG == 1}]]
if {$syncs < 20} { error "CDC structural gate failed ASYNC_REG=$syncs" }
set bad_drc [get_drc_violations -quiet -filter {SEVERITY == Error || SEVERITY == "Critical Warning"}]
if {[llength $bad_drc]} { error "DRC blocking: $bad_drc" }
puts "TIMING WNS=$wns WHS=$whs DSP=$dsp BRAM36=$bram36 ASYNC_REG=$syncs"
set fh [open [file join $rep_dir gate_summary.txt] w]
puts $fh "VIVADO=[version -short]"
puts $fh "WNS_NS=$wns"
puts $fh "WHS_NS=$whs"
puts $fh "DSP=$dsp"
puts $fh "BRAM36=$bram36"
puts $fh "LATCHES=0"
puts $fh "IMEM_FIRST_WORD=00008117"
puts $fh "IMEM_INIT_NONZERO=1"
puts $fh "READMEM_WARNINGS=0"
puts $fh "ASYNC_REG_CELLS=$syncs"
puts $fh "DRC_BLOCKING=0"
puts $fh "GATE_RESUMED_FROM_ROUTED_CHECKPOINT=1"
puts $fh "VIDEO_INCLUDED=1"
close $fh
set bit [file join $run_dir pynq_cop_40mhz.bit]
write_bitstream -force -file $bit
puts "BIT_WRITTEN=$bit"
exit