# Structural assertions belong in Tcl, not the restricted XDC command set.
proc vision_check_cdc {with_capture} {
    set config_first [get_pins -hier -filter {NAME =~ *req_meta_reg/D || NAME =~ *ack_meta_reg/D}]
    if {[llength $config_first] != 2} {error "expected two config handshake first-stage inputs"}
    foreach pattern {*u_config/hold_data_reg* *u_config/hold_id_reg* *u_config/dst_data_reg* *u_config/dst_id_reg*} {
        if {![llength [get_cells -hier -filter "NAME =~ $pattern"]]} {error "missing config CDC bundle: $pattern"}
    }
    if {$with_capture} {
        set capture_first [get_pins -hier -regexp {.*capture_status.*/(lock_sync_reg\[0\]|fault_bridge/(ack_sync_reg\[0\]|pending_sync_reg\[0\]))/D}]
        if {[llength $capture_first] != 3} {error "expected three capture CDC first-stage inputs, got [llength $capture_first]"}
        foreach pin $capture_first {
            if {![get_property ASYNC_REG [get_cells -of_objects $pin]]} {error "capture synchronizer missing ASYNC_REG: $pin"}
        }
        puts "PASS: CDC structural assertions (config first-stage=2, capture first-stage=3)"
    } else {puts "PASS: CDC structural assertions (config first-stage=2)"}
}
