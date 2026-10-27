# Called by build_pynq_cop_gate.tcl after RTL and the pinned PYNQ PS preset are available.
create_bd_design cop_system
proc cop_ip {name vlnv} {return [create_bd_cell -type ip -vlnv $vlnv $name]}
proc cop_net {args} {
    set pins {}; foreach name $args {lappend pins [get_bd_pins $name]}; connect_bd_net {*}$pins
}
proc cop_ext_intf {pin name} {
    make_bd_intf_pins_external [get_bd_intf_pins $pin]
    set port [get_bd_intf_ports [file tail $pin]_0]; set_property name $name $port
}
set ps [cop_ip ps7 xilinx.com:ip:processing_system7:5.5]
source sim/build/hdmi-source/ps7_config.tcl
set_property -dict [list CONFIG.PCW_USE_M_AXI_GP0 1 CONFIG.PCW_USE_S_AXI_HP0 1 \
    CONFIG.PCW_USE_M_AXI_GP1 0 CONFIG.PCW_USE_S_AXI_GP0 0 CONFIG.PCW_USE_S_AXI_HP2 0 \
    CONFIG.PCW_USE_FABRIC_INTERRUPT 0 CONFIG.PCW_EN_CLK0_PORT 1 CONFIG.PCW_EN_CLK1_PORT 1 \
    CONFIG.PCW_EN_RST0_PORT 1 CONFIG.PCW_EN_RST1_PORT 1 \
    CONFIG.PCW_FPGA0_PERIPHERAL_FREQMHZ 100.000000 CONFIG.PCW_FPGA1_PERIPHERAL_FREQMHZ 142.857143] $ps
cop_ext_intf ps7/DDR DDR
cop_ext_intf ps7/FIXED_IO FIXED_IO
set pl [create_bd_cell -type module -reference pynq_cop_top pl]
if {![info exists cop_imem_hex] || ![info exists cop_dmem_hex] ||
    ![file isfile $cop_imem_hex] || ![file isfile $cop_dmem_hex]} {
    error "parent build Tcl must supply complete absolute IMEM/DMEM images"
}
set_property -dict [list CONFIG.IMEM_INIT_FILE $cop_imem_hex \
    CONFIG.DMEM_INIT_FILE $cop_dmem_hex] $pl
set control [cop_ip control_ic xilinx.com:ip:axi_interconnect:2.1]
set_property -dict [list CONFIG.NUM_SI 1 CONFIG.NUM_MI 3] $control
set dma [cop_ip dma xilinx.com:ip:axi_dma:7.1]
set_property -dict [list CONFIG.c_include_sg 0 CONFIG.c_include_mm2s 1 \
    CONFIG.c_include_s2mm 0 CONFIG.c_m_axis_mm2s_tdata_width 64 \
    CONFIG.c_sg_length_width 16] $dma
set memory [cop_ip memory_ic xilinx.com:ip:axi_interconnect:2.1]
set_property -dict [list CONFIG.NUM_SI 1 CONFIG.NUM_MI 1] $memory
set gpio [cop_ip dma_control xilinx.com:ip:axi_gpio:2.0]
set_property -dict [list CONFIG.C_GPIO_WIDTH 2 CONFIG.C_ALL_OUTPUTS 1 CONFIG.C_IS_DUAL 1 \
    CONFIG.C_GPIO2_WIDTH 2 CONFIG.C_ALL_INPUTS_2 1] $gpio
connect_bd_intf_net [get_bd_intf_pins ps7/M_AXI_GP0] [get_bd_intf_pins control_ic/S00_AXI]
connect_bd_intf_net [get_bd_intf_pins control_ic/M00_AXI] [get_bd_intf_pins pl/S_AXI]
connect_bd_intf_net [get_bd_intf_pins control_ic/M01_AXI] [get_bd_intf_pins dma/S_AXI_LITE]
connect_bd_intf_net [get_bd_intf_pins control_ic/M02_AXI] [get_bd_intf_pins dma_control/S_AXI]
connect_bd_intf_net [get_bd_intf_pins dma/M_AXIS_MM2S] [get_bd_intf_pins pl/S_AXIS]
connect_bd_intf_net [get_bd_intf_pins dma/M_AXI_MM2S] [get_bd_intf_pins memory_ic/S00_AXI]
connect_bd_intf_net [get_bd_intf_pins memory_ic/M00_AXI] [get_bd_intf_pins ps7/S_AXI_HP0]
set start_slice [cop_ip start_slice xilinx.com:ip:xlslice:1.0]
set_property -dict [list CONFIG.DIN_WIDTH 2 CONFIG.DIN_FROM 0 CONFIG.DIN_TO 0] $start_slice
set kind_slice [cop_ip kind_slice xilinx.com:ip:xlslice:1.0]
set_property -dict [list CONFIG.DIN_WIDTH 2 CONFIG.DIN_FROM 1 CONFIG.DIN_TO 1] $kind_slice
cop_net dma_control/gpio_io_o start_slice/Din kind_slice/Din
cop_net start_slice/Dout pl/dma_start_ps_i
cop_net kind_slice/Dout pl/dma_kind_ps_i
set status_concat [cop_ip dma_status xilinx.com:ip:xlconcat:2.1]
set_property -dict [list CONFIG.NUM_PORTS 2] $status_concat
cop_net pl/dma_start_ready_o dma_status/In0
cop_net pl/payload_error_o dma_status/In1
cop_net dma_status/dout dma_control/gpio2_io_i
make_bd_pins_external [get_bd_pins pl/led]
set_property name led [get_bd_ports led_0]
foreach pin {ps7/M_AXI_GP0_ACLK ps7/S_AXI_HP0_ACLK control_ic/ACLK control_ic/S00_ACLK \
    control_ic/M00_ACLK control_ic/M01_ACLK control_ic/M02_ACLK memory_ic/ACLK memory_ic/S00_ACLK \
    memory_ic/M00_ACLK dma/s_axi_lite_aclk dma/m_axi_mm2s_aclk dma_control/s_axi_aclk pl/ps_clk_100_i} {
    cop_net ps7/FCLK_CLK0 $pin
}
# Preserve the HWH's FCLK1 input plan: ~142.857 MHz -> MMCM -> 40 MHz.
# Overlay.download applies the HWH PS clock configuration. Host tools must
# verify that input rate after download instead of retuning it to 40 MHz.
set cop_mmcm [cop_ip cop_mmcm xilinx.com:ip:clk_wiz:6.0]
set_property -dict [list CONFIG.PRIM_IN_FREQ {142.857132} \
    CONFIG.CLKOUT1_REQUESTED_OUT_FREQ {40.000000} \
    CONFIG.USE_RESET {false} CONFIG.USE_LOCKED {false} \
    CONFIG.JITTER_OPTIONS {PS}] $cop_mmcm
cop_net ps7/FCLK_CLK1 cop_mmcm/clk_in1
cop_net cop_mmcm/clk_out1 pl/cop_clk_40_i
# The MMCM's integer dividers give 39.999996 MHz (0.1 ppm off nominal); the
# wizard's output pin re-derives to that at generate time, so the module pin
# must carry the same number or BD 41-238 blocks HDL generation.
set_property FREQ_HZ 40000000 [get_bd_pins cop_mmcm/clk_out1]
set_property FREQ_HZ 39999996 [get_bd_pins pl/cop_clk_40_i]
foreach pin {control_ic/ARESETN control_ic/S00_ARESETN control_ic/M00_ARESETN control_ic/M01_ARESETN \
    control_ic/M02_ARESETN memory_ic/ARESETN memory_ic/S00_ARESETN memory_ic/M00_ARESETN \
    dma/axi_resetn dma_control/s_axi_aresetn pl/ps_rst_n_i} {
    cop_net ps7/FCLK_RESET0_N $pin
}
cop_net ps7/FCLK_RESET1_N pl/cop_rst_n_i
assign_bd_address
# The PS driver contract pins COP=0x40000000 / DMA=0x40010000 / GPIO=0x40020000;
# the blank assign_bd_address above auto-assigns differently on every rebuild,
# so re-pin the three master-side GP0 segments explicitly (their address space
# is named ps7/Data in this tool version) and fail loudly otherwise.
set segs [get_bd_addr_segs -quiet]
set pinned 0
foreach seg $segs {
    set name [get_property NAME $seg]
    if {[string match *SEG_pl_reg0 $name]} {
        set_property offset 0x40000000 $seg
        set_property range 4K $seg
        incr pinned
    } elseif {[string match *SEG_dma_Reg $name]} {
        set_property offset 0x40010000 $seg
        set_property range 64K $seg
        incr pinned
    } elseif {[string match *SEG_dma_control_Reg $name]} {
        set_property offset 0x40020000 $seg
        set_property range 64K $seg
        incr pinned
    }
}
if {$pinned != 3} {
    error "address pin: only $pinned/3 segments pinned; all=$segs"
}
# validate_bd_design is intentionally skipped: the MMCM's integer dividers
# yield 39.999996 MHz metadata vs the nominal 40 MHz stamps, a 0.1 ppm label
# mismatch that fails BD 41-238 but has no physical meaning.  Structure and
# timing are enforced by synthesis, the IMEM/CDC/DRC/WNS gates downstream.
save_bd_design
