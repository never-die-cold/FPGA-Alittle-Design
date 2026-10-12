# Read local Vivado capture capabilities; never opens a hardware target.
if {[catch {
    set build_dir [file normalize "sim/build/c01-capture-[clock microseconds]"]
    create_project c01_capture $build_dir -part xc7z020clg400-1
    puts "BUILD_DIR: $build_dir"
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
    puts "PASS: capture IP catalog present; widths above are defaults, not an integrated design"
} reason]} {
    puts stderr "ERROR: $reason"
    exit 1
}
