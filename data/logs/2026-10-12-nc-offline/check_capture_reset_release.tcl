# Read the actual BD properties/nets; no hardware target is opened.
proc capture_check_reset_release {reset high low} {
    foreach property {CONFIG.C_EXT_RESET_HIGH CONFIG.C_AUX_RESET_HIGH} {
        if {[get_property $property [get_bd_cells $reset]] != 0} {
            error "capture reset polarity mismatch: $property"
        }
    }
    foreach {cell value} [list $high 1 $low 0] {
        if {[get_property CONFIG.CONST_VAL [get_bd_cells $cell]] != $value} {
            error "capture reset constant mismatch: $cell"
        }
    }
    foreach {pin source} [list ext_reset_in ps7/FCLK_RESET0_N \
            aux_reset_in $high/dout dcm_locked $high/dout mb_debug_sys_rst $low/dout] {
        set actual [get_bd_nets -of_objects [get_bd_pins $reset/$pin]]
        set expected [get_bd_nets -of_objects [get_bd_pins $source]]
        if {[llength $actual] != 1 || $actual ne $expected} {
            error "capture reset release mismatch: $pin must connect to $source"
        }
    }
    puts "PASS: actual BD reset polarity/constants and ext/aux/debug/lock release nets"
}

proc capture_test_reset_release {} {
    foreach {cell property bad good} {
        reset CONFIG.C_AUX_RESET_HIGH 1 0
        reset CONFIG.C_EXT_RESET_HIGH 1 0
        high CONFIG.CONST_VAL 0 1
        low CONFIG.CONST_VAL 1 0
    } {
        set_property $property $bad [get_bd_cells $cell]
        set rejected [catch {capture_check_reset_release reset high low} reason]
        set_property $property $good [get_bd_cells $cell]
        if {!$rejected} {error "reset guard accepted $cell/$property=$bad"}
        puts "PASS: reset guard rejects $cell/$property=$bad: $reason"
    }
    foreach {pin wrong right} {aux_reset_in low high mb_debug_sys_rst high low} {
        disconnect_bd_net [get_bd_nets -of_objects [get_bd_pins reset/$pin]] [get_bd_pins reset/$pin]
        connect_bd_net [get_bd_pins $wrong/dout] [get_bd_pins reset/$pin]
        set rejected [catch {capture_check_reset_release reset high low} reason]
        disconnect_bd_net [get_bd_nets -of_objects [get_bd_pins reset/$pin]] [get_bd_pins reset/$pin]
        connect_bd_net [get_bd_pins $right/dout] [get_bd_pins reset/$pin]
        if {!$rejected} {error "reset guard accepted wrong net for $pin"}
        puts "PASS: reset guard rejects wrong net for $pin: $reason"
    }
    capture_check_reset_release reset high low
}
