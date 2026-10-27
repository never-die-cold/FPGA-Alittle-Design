# Local-only wrapper: Vivado exports PYTHONHOME for its bundled 3.13, which breaks
# the gate's Python 3.12 child (SRE module mismatch). Clear it, pin the host Python,
# then hand over to the committed gate script unchanged.
unset -nocomplain ::env(PYTHONHOME)
unset -nocomplain ::env(PYTHONPATH)
set ::env(COP_PYTHON) "C:/Users/ASUS/AppData/Local/Programs/Python/Python312/python.exe"
source [file join [file dirname [file normalize [info script]]] build_pynq_cop_gate.tcl]
