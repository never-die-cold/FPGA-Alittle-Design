set py {C:/Users/ASUS/AppData/Local/Programs/Python/Python312/python.exe}
puts "PYTHONHOME_EXISTS=[info exists ::env(PYTHONHOME)]"
if {[info exists ::env(PYTHONHOME)]} { puts "PYTHONHOME=$::env(PYTHONHOME)" }
if {[catch {exec $py -c {import re,argparse;print("IMPORT_OK_WITH_HOME")}} msg]} { puts "FAIL1=$msg" } else { puts $msg }
unset -nocomplain ::env(PYTHONHOME)
unset -nocomplain ::env(PYTHONPATH)
if {[catch {exec $py -c {import re,argparse;print("IMPORT_OK_CLEAN")}} msg2]} { puts "FAIL2=$msg2" } else { puts $msg2 }
exit
