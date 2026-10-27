# Diagnose project initialization without synthesizing or changing a design.
puts "PROBE_VERSION=[version -short]"
puts "PROBE_PWD=[pwd]"
if {[lsearch -exact $argv nested] >= 0} {
    set executable [file join $::env(XILINX_VIVADO) bin unwrapped win64.o vivado.exe]
    puts "NESTED_EXECUTABLE=$executable"
    puts [exec $executable -mode batch -nojournal -log data/logs/2026-10-28-multitarget-board-r6/init-child.log -source [info script] 2>@1]
    exit 0
}
foreach name {TCLLIBPATH TCL_LIBRARY PYTHONHOME PYTHONPATH XILINX_LOCAL_USER_DATA APPDATA LOCALAPPDATA TEMP} {
    if {[info exists ::env($name)]} {puts "PROBE_ENV_$name=$::env($name)"}
}
if {[catch {create_project -in_memory -part xc7z020clg400-1} message options]} {
    puts stderr "PROJECT_INIT_FAILED=$message"
    puts stderr [dict get $options -errorinfo]
    if {[llength [info procs ::tclapp::load_apps]]} {puts [info body ::tclapp::load_apps]}
    exit 1
}
puts "PROJECT_INIT_PASS"
if {[llength [info procs ::tclapp::load_apps]]} {puts [info body ::tclapp::load_apps]}
close_project
exit 0
