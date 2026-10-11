# Read local Vivado capture capabilities; never opens a hardware target.
if {[catch {
    create_project -in_memory -part xc7z020clg400-1
    create_bd_design capture_probe
    foreach {name pattern} {vdma xilinx.com:ip:axi_vdma:* vin xilinx.com:ip:v_vid_in_axi4s:*} {
        set defs [lsort -dictionary [get_ipdefs -all -quiet $pattern]]
        if {![llength $defs]} { error "capture IP missing: $pattern" }
        set cell [create_bd_cell -type ip -vlnv [get_property VLNV [lindex $defs end]] $name]
        puts "CAPTURE_IP: $name [get_property VLNV $cell]"
        foreach key [lsort [list_property $cell]] {
            if {[string match CONFIG.* $key]} { puts "$name $key=[get_property $key $cell]" }
        }
        puts "PINS: $name [get_bd_pins $name/*]"
        puts "INTERFACES: $name [get_bd_intf_pins $name/*]"
    }
    set_property -dict [list CONFIG.C_INCLUDE_MM2S 0 CONFIG.C_INCLUDE_S2MM 1 \
        CONFIG.C_NUM_FSTORES 4 CONFIG.C_S_AXIS_S2MM_TDATA_WIDTH 24 \
        CONFIG.C_M_AXI_S2MM_DATA_WIDTH 64 CONFIG.C_INCLUDE_S2MM_DRE 1] [get_bd_cells vdma]
    puts "PASS: capture IP catalog and 24-bit S2MM configuration accepted"
} reason]} {
    puts stderr "ERROR: $reason"
    exit 1
}
