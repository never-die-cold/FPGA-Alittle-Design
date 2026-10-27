# Implementation hook: regular Tcl permits checked object queries and errors.
proc cop_cdc_cells {pattern} {
    set cells [get_cells -quiet -hier -regexp ".*pl/inst/$pattern"]
    if {[llength $cells] == 0} {error "CDC constraint matched no cells: $pattern"}
    return $cells
}
proc cop_cdc_bundle {source destination budget} {
    set from [cop_cdc_cells $source]
    set to [cop_cdc_cells $destination]
    set_max_delay -datapath_only $budget -from $from -to $to
    set_bus_skew $budget -from $from -to $to
}
set ps_regs [cop_cdc_cells {axil_cdc/rdata_s1_reg.*}]
set cop_regs [cop_cdc_cells {axil_cdc/rdata_hold_reg.*}]
set ps_clock [get_clocks -of_objects [get_pins -of_objects $ps_regs -filter {REF_PIN_NAME == C}]]
set cop_clock [get_clocks -of_objects [get_pins -of_objects $cop_regs -filter {REF_PIN_NAME == C}]]
if {[llength $ps_clock] != 1 || [llength $cop_clock] != 1} {
    error "CDC expected exactly one PS clock and one cop clock"
}
if {abs([get_property PERIOD $ps_clock]-10.0)>0.001 ||
    abs([get_property PERIOD $cop_clock]-25.0)>0.001} {
    error "CDC requires actual PS/cop clock periods of 10/25 ns"
}
foreach {source destination budget} {
    axil_cdc/aw_hold_reg.* axil_cdc/aw_m1_reg.* 25.0
    axil_cdc/wd_hold_reg.* axil_cdc/wd_m1_reg.* 25.0
    axil_cdc/ws_hold_reg.* axil_cdc/ws_m1_reg.* 25.0
    axil_cdc/ar_hold_reg.* axil_cdc/ar_m1_reg.* 25.0
    axil_cdc/rdata_hold_reg.* axil_cdc/rdata_s1_reg.* 10.0
    axil_cdc/bresp_hold_reg.* axil_cdc/bresp_s1_reg.* 10.0
    axil_cdc/rresp_hold_reg.* axil_cdc/rresp_s1_reg.* 10.0
    axis_cdc/wgray_reg.* axis_cdc/wgray_m1_reg.* 10.0
    axis_cdc/rgray_reg.* axis_cdc/rgray_s1_reg.* 10.0
} {cop_cdc_bundle $source $destination $budget}
set controls [cop_cdc_cells {(axil_cdc/(wack_s1|rack_s1|wreq_m1|rreq_m1)_reg.*|dma_(req_c1|kind_c1|ack_s1)_reg.*)}]
set_false_path -to [get_pins -of_objects $controls -filter {REF_PIN_NAME == D}]
set gpio_first [get_cells -quiet -hier -regexp {.*dma_control/.*/syncstages_ff_reg\[0\]}]
if {[llength $gpio_first]} {
    set_false_path -to [get_pins -of_objects $gpio_first -filter {REF_PIN_NAME == D}]
}
set_max_delay -datapath_only 25.0 -from [cop_cdc_cells {axis_cdc/mem_reg.*}] \
    -to [cop_cdc_cells {axis_cdc/out_data_reg.*}]
puts "CDC BUNDLE GATE APPLIED: PS=100 MHz cop=40 MHz; payload bounds 10/25 ns"
