# 并行像素边界 OOC post-route；不生成 bitstream、不操作板卡。
set rep data/logs/2026-10-02-vision-offboard/route
file mkdir $rep
foreach f [glob src/vision/*.v] { read_verilog $f }
synth_design -top video_pipeline -part xc7z020clg400-1 -mode out_of_context
create_clock -name pclk -period 13.468 [get_ports pclk]
create_clock -name axi_clk -period 10.0 [get_ports s_axi_aclk]
set_clock_uncertainty 0.150 [get_clocks *]
# 不用全局异步 clock group：只例外首级同步 D，稳定数据总线仍有延迟约束。
set sync_first [get_pins -hier -filter {NAME =~ *req_meta_reg/D || NAME =~ *ack_meta_reg/D}]
if {[llength $sync_first] != 2} { error "expected exactly two handshake synchronizer inputs" }
set_false_path -to $sync_first
set_false_path -from [get_ports rst_n]
set source_bundle [get_cells -hier -filter {NAME =~ *u_config/hold_data_reg* || NAME =~ *u_config/hold_id_reg*}]
set dest_bundle [get_cells -hier -filter {NAME =~ *u_config/dst_data_reg* || NAME =~ *u_config/dst_id_reg*}]
if {[llength $source_bundle] == 0 || [llength $dest_bundle] == 0} { error "missing stable bundle endpoints" }
set_max_delay -datapath_only 10.0 -from $source_bundle -to $dest_bundle
report_cdc -details -file $rep/cdc_synth.rpt
opt_design
place_design
phys_opt_design
route_design
report_utilization -file $rep/utilization.rpt
report_timing_summary -report_unconstrained -file $rep/timing.rpt
report_timing -max_paths 10 -file $rep/worst_paths.rpt
report_clock_utilization -file $rep/clocks.rpt
check_timing -verbose -file $rep/check_timing.rpt
report_drc -file $rep/drc.rpt
report_cdc -details -file $rep/cdc_route.rpt
set fp [open $rep/cdc_route.rpt r]
set cdc_text [read $fp]
close $fp
foreach line [split $cdc_text \n] {
    if {[regexp {^\s*[0-9]+\s+CDC-[0-9]+\s+(Critical|Error|Warning)} $line]} {
        if {![regexp {CDC-15\s+Warning.*Max Delay Datapath Only.*u_config/hold_(data|id)_reg.*u_config/dst_(data|id)_reg} $line]} {
            error "unexpected CDC finding: $line"
        }
    }
}
set fp [open $rep/check_timing.rpt r]
set timing_text [read $fp]
close $fp
foreach category {no_clock unconstrained_internal_endpoints multiple_clock loops latch_loops} {
    if {![regexp "checking $category \\(0\\)" $timing_text]} { error "timing coverage failed: $category" }
}
set setup_paths [get_timing_paths -delay_type max -max_paths 1]
set hold_paths [get_timing_paths -delay_type min -max_paths 1]
if {[llength $setup_paths] == 0 || [llength $hold_paths] == 0} { error "missing timed paths" }
set wns [get_property SLACK [lindex $setup_paths 0]]
set whs [get_property SLACK [lindex $hold_paths 0]]
set fp [open $rep/result.txt w]
puts $fp "OOC_POST_ROUTE top=video_pipeline pixel_period=13.468 axi_period=10.0 WNS=$wns WHS=$whs"
puts $fp "Vivado=[version -short] source_bundle=[llength $source_bundle] dest_bundle=[llength $dest_bundle]"
close $fp
foreach violation [get_drc_violations] {
    set severity [get_property SEVERITY $violation]
    if {$severity eq "Error" || $severity eq "Critical Warning"} { error "blocking DRC $violation: $severity" }
}
if {$wns < 0 || $whs < 0} { error "post-route timing failed WNS=$wns WHS=$whs" }
puts "PASS: vision OOC post-route WNS=$wns WHS=$whs (parallel pixel boundary, not physical HDMI)"
