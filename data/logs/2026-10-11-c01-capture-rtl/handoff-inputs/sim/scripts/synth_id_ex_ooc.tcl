# Vivado OOC synthesis gate for the Part B ID+EX block.
# Default read_verilog intentionally enforces Verilog-2001 parsing.
set script_dir [file dirname [file normalize [info script]]]
set root [file normalize [file join $script_dir .. ..]]
set out_dir [file join $root data logs id_ex_ooc]
file mkdir $out_dir
cd $root

set rtl_files [list \
    [file join $root src riscv alu.v] \
    [file join $root src riscv decode.v] \
    [file join $root src riscv id_ex_stage.v]]
read_verilog $rtl_files
synth_design -top id_ex_stage -part xc7z020clg400-1 -mode out_of_context

report_utilization -file [file join $out_dir utilization.rpt]
write_checkpoint -force [file join $out_dir id_ex_stage_synth.dcp]
puts "OOC SYNTH PASS: id_ex_stage (Verilog-2001, xc7z020clg400-1)"
