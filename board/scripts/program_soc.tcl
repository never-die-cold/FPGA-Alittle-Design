# 将 Part A SoC bitstream 通过 JTAG 下载到唯一的 XC7Z020 PL。
# 可选参数：bitstream 完整路径；省略时使用 build/run/soc/pynq_z2_soc.bit。
set script_dir [file normalize [file dirname [info script]]]
set root [file normalize [file join $script_dir .. ..]]

if {[llength $argv] > 1} {error "Usage: program_soc.tcl ?bitstream?"}
if {[llength $argv] == 1} {
    set bitstream [file normalize [lindex $argv 0]]
} else {
    set bitstream [file join $root build run soc pynq_z2_soc.bit]
}
if {![file isfile $bitstream] || [file size $bitstream] == 0} {
    error "Bitstream missing or empty: $bitstream"
}

if {[catch {
    open_hw_manager
    connect_hw_server
    open_hw_target

    set matches {}
    foreach device [get_hw_devices] {
        set part [get_property -quiet PART $device]
        puts "FOUND: $device PART=$part"
        if {[string match -nocase "xc7z020*" $part]} {
            lappend matches $device
        }
    }
    if {[llength $matches] != 1} {
        error "Expected exactly one XC7Z020, found [llength $matches]"
    }

    set device [lindex $matches 0]
    current_hw_device $device
    refresh_hw_device -update_hw_probes false $device
    set_property PROGRAM.FILE $bitstream $device
    puts "PROGRAMMING: $device"
    program_hw_devices $device
    puts "PROGRAM PASSED: $device <- $bitstream"
} message options]} {
    puts stderr "PROGRAM FAILED: $message"
    if {[dict exists $options -errorinfo]} {
        puts stderr [dict get $options -errorinfo]
    }
    catch {close_hw_manager}
    exit 1
}

close_hw_manager
exit 0
