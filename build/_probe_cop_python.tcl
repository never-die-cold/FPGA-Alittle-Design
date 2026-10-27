puts "ENV_EXISTS=[info exists ::env(COP_PYTHON)]"
if {[info exists ::env(COP_PYTHON)]} { puts "ENV_VAL=$::env(COP_PYTHON)"; puts "ENV_ISFILE=[file isfile $::env(COP_PYTHON)]" }
puts "HARD_ISFILE=[file isfile {C:/Users/ASUS/AppData/Local/Programs/Python/Python312/python.exe}]"
puts "WHICH_PY=[auto_execok python]"
puts "WHICH_PY3=[auto_execok python3]"
if {[file isfile {C:/Users/ASUS/AppData/Local/Programs/Python/Python312/python.exe}]} {
  puts "VER=[exec {C:/Users/ASUS/AppData/Local/Programs/Python/Python312/python.exe} -c {import sys;print(sys.version)}]"
}
exit
