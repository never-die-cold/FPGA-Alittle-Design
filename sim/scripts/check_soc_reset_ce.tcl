# Reproducible 40 MHz BHT2 SoC A/B implementation; no bitstream or board access.
# vivado -mode batch -source sim/scripts/check_soc_reset_ce.tcl -tclargs <snapshot-root> <output-dir>
# Snapshot layout: src/riscv/*.v, src/riscv_fw/hello_v0.hex, build/constraints/pynq_z2_soc.xdc.
if {$argc != 2} {error "Usage: check_soc_reset_ce.tcl <snapshot-root> <output-dir>"}
set repo [file normalize [file join [file dirname [info script]] ../..]]
set snapshot [file normalize [lindex $argv 0]]
set output [file normalize [lindex $argv 1]]
foreach path [list $snapshot $output] {
    if {[string first [string tolower "$repo/"] [string tolower "$path/"]] != 0} {
        error "Input and output must remain inside the repository: $path"
    }
}
file mkdir $output
set rtl [lsort [glob [file join $snapshot src riscv *.v]]]
set xdc [file join $snapshot build constraints pynq_z2_soc.xdc]
if {![file isfile $xdc] || ![file isfile [file join $snapshot src riscv_fw hello_v0.hex]]} {
    error "Incomplete source snapshot: $snapshot"
}
set metadata [open [file join $output invocation.txt] w]
puts $metadata "Vivado: [version -short]\nSnapshot: $snapshot\nOutput: $output"
puts $metadata "Top: pynq_z2_top; part: xc7z020clg400-1; clock: 25.000 ns; forwarding: 1; BHT_MODE: 2"
puts $metadata "RTL: $rtl\nXDC: $xdc\nFlow: synth, opt, place Explore, phys_opt Explore, route Explore, phys_opt Explore"
close $metadata

# Follow all net segments so hierarchy does not hide a constant or a driver.
proc pin_driver {pin} {
    set nets [get_nets -quiet -segments -of_objects $pin]
    set drivers [get_pins -quiet -leaf -of_objects $nets -filter {DIRECTION == OUT}]
    set classes {}
    foreach driver $drivers {
        lappend classes [get_property REF_NAME [get_cells -quiet -of_objects $driver]]
    }
    if {[lsearch -exact $classes VCC] >= 0} {return [list const1 $drivers]}
    if {[lsearch -exact $classes GND] >= 0} {return [list const0 $drivers]}
    if {[llength $drivers] == 0} {return [list unconnected $drivers]}
    return [list dynamic $drivers]
}

proc audit_structure {output phase} {
    set detail [open [file join $output ${phase}_structure.txt] w]
    set counts [dict create]
    set flops [get_cells -quiet -hierarchical -filter {NAME =~ *u_mem_wb* && REF_NAME =~ FD*}]
    dict set counts mem_wb_ff [llength $flops]
    foreach cell [lsort $flops] {
        foreach pin [get_pins -quiet -of_objects $cell] {
            set role [get_property REF_PIN_NAME $pin]
            if {$role ni {CE R S CLR PRE}} {continue}
            lassign [pin_driver $pin] kind drivers
            dict incr counts ${role}_${kind}
            puts $detail "CONTROL $pin $kind drivers={$drivers}"
        }
    }
    set addresses [get_cells -quiet -hierarchical -filter {NAME =~ *u_mem_wb*mem_addr_reg* && REF_NAME =~ FD*}]
    dict set counts address_ff [llength $addresses]
    dict set counts address_named_replicas 0
    dict set counts address_direct_dmem_loads 0
    dict set counts address_direct_ram_loads 0
    foreach cell [lsort $addresses] {
        if {[string match *_rep* $cell]} {dict incr counts address_named_replicas}
        set q [get_pins -quiet -of_objects $cell -filter {REF_PIN_NAME == Q}]
        set nets [get_nets -quiet -segments -of_objects $q]
        set loads [get_pins -quiet -leaf -of_objects $nets -filter {DIRECTION == IN}]
        puts $detail "ADDRESS $cell direct_loads=[llength $loads]"
        foreach load [lsort $loads] {
            set ref [get_property REF_NAME [get_cells -quiet -of_objects $load]]
            if {[string match *u_dmem* $load]} {dict incr counts address_direct_dmem_loads}
            if {[string match RAM* $ref]} {dict incr counts address_direct_ram_loads}
            puts $detail "  LOAD $load ($ref)"
        }
    }
    set reset_cells [get_cells -quiet -hierarchical -filter {NAME =~ reset_pipe_reg*}]
    foreach cell [lsort $reset_cells] {
        set q [get_pins -quiet -of_objects $cell -filter {REF_PIN_NAME == Q}]
        set endpoints [all_fanout -quiet -flat -endpoints_only -from $q]
        puts $detail "RESET $cell endpoints=[llength $endpoints]"
        foreach endpoint [lsort $endpoints] {puts $detail "  ENDPOINT $endpoint"}
    }
    close $detail
    set summary [open [file join $output ${phase}_structure_summary.txt] w]
    foreach key [lsort [dict keys $counts]] {puts $summary "$key=[dict get $counts $key]"}
    close $summary
    report_utilization -file [file join $output ${phase}_utilization.rpt]
    report_control_sets -verbose -file [file join $output ${phase}_control_sets.rpt]
}

cd $snapshot
set core_clk_divide 25
set core_clk_name core_clk_40
# Match build/build_soc.tcl, including Verilog-2001 parser and optimization order.
read_verilog $rtl
read_xdc $xdc
synth_design -top pynq_z2_top -part xc7z020clg400-1 \
    -generic {CORE_CLK_DIVIDE=25 ENABLE_FORWARDING=1 BHT_MODE=2}
foreach {name period} {sys_clk_125 8.000 core_clk_40 25.000} {
    set clock [get_clocks -quiet $name]
    if {[llength $clock] != 1 || abs([get_property PERIOD $clock] - $period) > 0.001} {
        error "Missing or incorrect clock $name"
    }
}
write_checkpoint -force [file join $output post_synth.dcp]
audit_structure $output synth
opt_design
place_design -directive Explore
phys_opt_design -directive Explore
route_design -directive Explore
phys_opt_design -directive Explore
write_checkpoint -force [file join $output post_route.dcp]
audit_structure $output route
report_timing_summary -delay_type min_max -report_unconstrained -check_timing_verbose \
    -file [file join $output timing_summary.rpt]
report_timing -delay_type max -max_paths 20 -sort_by group -file [file join $output timing_worst_paths.rpt]
report_drc -file [file join $output drc.rpt]
set checks {no_clock constant_clock unconstrained_internal_endpoints generated_clocks}
set checked [check_timing -override_defaults $checks -verbose -return_string]
set check_file [open [file join $output check_timing.rpt] w]
puts $check_file $checked
close $check_file
set failures {}
foreach check $checks {
    if {![regexp [format {checking %s \(0\)} $check] $checked]} {lappend failures $check}
}
set setup [get_timing_paths -delay_type max -max_paths 1]
set hold [get_timing_paths -delay_type min -max_paths 1]
if {[llength $setup] != 1 || [llength $hold] != 1} {error "Missing setup or hold timing path"}
set wns [get_property SLACK $setup]
set whs [get_property SLACK $hold]
set severe [get_drc_violations -quiet -filter {SEVERITY == Error || SEVERITY == "Critical Warning"}]
if {$wns < 0} {lappend failures setup}
if {$whs < 0} {lappend failures hold}
if {[llength $severe]} {lappend failures severe_drc}
set result [open [file join $output result.txt] w]
puts $result "WNS=$wns\nWHS=$whs\nSEVERE_DRC=[llength $severe]\nCHECK_FAILURES=$failures"
close $result
if {[llength $failures]} {error "SoC A/B checks failed: $failures"}
puts "SOC_RESET_CE_PASS: WNS=$wns WHS=$whs SEVERE_DRC=0 output=$output"
