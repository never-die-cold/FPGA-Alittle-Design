# Reproducible default-Verilog OOC check of the CNN operator controller.
set root [file normalize [file join [file dirname [info script]] ../..]]
if {$argc != 2 && $argc != 3} { error "usage: output-directory source-snapshot-directory ?repository-root?" }
if {$argc == 3} { set root [file normalize [lindex $argv 2]] }
set out [file normalize [lindex $argv 0]]
set sources [file normalize [lindex $argv 1]]
foreach path [list $out $sources] {
    if {![string match -nocase "$root/*" $path]} { error "path outside repository" }
}
if {[file exists $out] && [llength [glob -nocomplain -directory $out *]]} {
    error "output must be new/empty; preserve previous reports"
}
file mkdir $out
puts "VIVADO=[version -short] SOURCES=$sources"
read_verilog [glob -directory $sources *.v]
synth_design -top cnn_sequencer -part xc7z020clg400-1 -mode out_of_context
create_clock -name cnn_clk -period 10.000 [get_ports clk]
set_input_delay -clock cnn_clk 1.000 [get_ports -filter {DIRECTION == IN && NAME != clk && NAME != rst_n}]
set_output_delay -clock cnn_clk 1.000 [all_outputs]
set_false_path -from [get_ports rst_n]
opt_design
place_design
phys_opt_design
route_design
report_utilization -file [file join $out utilization.rpt]
report_timing_summary -warn_on_violation -file [file join $out timing.rpt]
report_timing -max_paths 10 -file [file join $out worst_paths.rpt]
report_drc -file [file join $out drc.rpt]
check_timing -verbose
write_checkpoint [file join $out cnn_ooc.dcp]
set paths [get_timing_paths -delay_type max -max_paths 1]
if {![llength $paths]} { error "no setup timing path" }
set slack [get_property SLACK [lindex $paths 0]]
set hold_paths [get_timing_paths -delay_type min -max_paths 1]
if {![llength $hold_paths]} { error "no hold timing path" }
set hold_slack [get_property SLACK [lindex $hold_paths 0]]
set dsp [llength [get_cells -hierarchical -filter {REF_NAME =~ DSP48*}]]
set severe [get_drc_violations -filter {SEVERITY == Error || SEVERITY == "Critical Warning"}]
puts "CNN_OOC_RESULT WNS=$slack WHS=$hold_slack DSP=$dsp SEVERE_DRC=[llength $severe]"
if {$slack < 0 || $hold_slack < 0 || $dsp > 220 || [llength $severe]} { error "CNN OOC timing/resource/DRC gate failed; preserve reports" }
puts "PASS: CNN operator OOC setup/hold timing, DSP resource and severe DRC gate"
