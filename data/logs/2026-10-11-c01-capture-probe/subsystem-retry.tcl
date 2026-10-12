# Offline C01 capture subsystem validation; no hardware target or bitstream.
if {[catch {
    create_project -in_memory -part xc7z020clg400-1
    create_bd_design capture_subsystem
    proc cip {name vlnv} { create_bd_cell -type ip -vlnv $vlnv $name }
    proc cnet {args} { set pins {}; foreach p $args { lappend pins [get_bd_pins $p] }; connect_bd_net {*}$pins }
    set ps [cip ps7 xilinx.com:ip:processing_system7:5.5]
    source sim/build/hdmi-source/ps7_config.tcl
    set_property -dict [list CONFIG.PCW_USE_S_AXI_HP0 1 CONFIG.PCW_S_AXI_HP0_DATA_WIDTH 64 \
        CONFIG.PCW_USE_S_AXI_HP1 0 CONFIG.PCW_USE_S_AXI_HP2 0 CONFIG.PCW_USE_S_AXI_HP3 0 \
        CONFIG.PCW_USE_FABRIC_INTERRUPT 1 CONFIG.PCW_USE_M_AXI_GP1 0 CONFIG.PCW_USE_S_AXI_GP0 0 
        CONFIG.PCW_USE_S_AXI_GP1 0 CONFIG.PCW_EN_EMIO_GPIO 0 CONFIG.PCW_GPIO_EMIO_GPIO_ENABLE 0 
        CONFIG.PCW_I2C1_PERIPHERAL_ENABLE 0] $ps
    foreach p {DDR FIXED_IO} { make_bd_intf_pins_external [get_bd_intf_pins ps7/$p] }
    set vdma [cip capture_dma xilinx.com:ip:axi_vdma:6.3]
    set_property -dict [list CONFIG.c_include_mm2s 0 CONFIG.c_include_s2mm 1 \
        CONFIG.c_num_fstores 4 CONFIG.c_m_axi_s2mm_data_width 64 CONFIG.c_include_s2mm_dre 1 \
        CONFIG.c_include_internal_genlock 0 CONFIG.c_use_s2mm_fsync 2] $vdma
    set vin [cip capture_input xilinx.com:ip:v_vid_in_axi4s:5.0]
    set_property -dict [list CONFIG.C_HAS_ASYNC_CLK 1 CONFIG.C_M_AXIS_VIDEO_FORMAT 0 \
        CONFIG.C_NATIVE_COMPONENT_WIDTH 8 CONFIG.C_M_AXIS_VIDEO_DATA_WIDTH 8 \
        CONFIG.C_PIXELS_PER_CLOCK 1] $vin
    set control [cip control_converter xilinx.com:ip:axi_protocol_converter:2.1]
    set_property -dict [list CONFIG.SI_PROTOCOL AXI3 CONFIG.MI_PROTOCOL AXI4LITE] $control
    set memory [cip memory_converter xilinx.com:ip:axi_protocol_converter:2.1]
    set_property -dict [list CONFIG.SI_PROTOCOL AXI4 CONFIG.MI_PROTOCOL AXI3] $memory
    foreach {a b} {ps7/M_AXI_GP0 control_converter/S_AXI control_converter/M_AXI capture_dma/S_AXI_LITE \
        capture_dma/M_AXI_S2MM memory_converter/S_AXI memory_converter/M_AXI ps7/S_AXI_HP0 \
        capture_input/video_out capture_dma/S_AXIS_S2MM} {
        connect_bd_intf_net [get_bd_intf_pins $a] [get_bd_intf_pins $b]
    }
    set reset [cip reset xilinx.com:ip:proc_sys_reset:5.0]
    set high [cip high xilinx.com:ip:xlconstant:1.1]
    set low [cip low xilinx.com:ip:xlconstant:1.1]
    set_property CONFIG.CONST_VAL 0 $low
    cnet ps7/FCLK_CLK0 ps7/M_AXI_GP0_ACLK ps7/S_AXI_HP0_ACLK reset/slowest_sync_clk \
        control_converter/aclk memory_converter/aclk capture_dma/s_axi_lite_aclk \
        capture_dma/m_axi_s2mm_aclk capture_dma/s_axis_s2mm_aclk capture_input/aclk
    cnet ps7/FCLK_RESET0_N reset/ext_reset_in
    cnet high/dout reset/dcm_locked capture_input/aclken capture_input/axis_enable capture_input/vid_io_in_ce
    cnet low/dout reset/aux_reset_in reset/mb_debug_sys_rst
    cnet reset/peripheral_aresetn control_converter/aresetn memory_converter/aresetn capture_dma/axi_resetn capture_input/aresetn
    make_bd_intf_pins_external [get_bd_intf_pins capture_input/vid_io_in]
    set pixel [create_bd_port -dir I -type clk -freq_hz 74250000 pixel_clock]
    set_property CONFIG.FREQ_HZ 74250000 $pixel
    connect_bd_net $pixel [get_bd_pins capture_input/vid_io_in_clk]
    set pixel_reset [create_bd_port -dir I -type rst pixel_reset]
    set_property CONFIG.POLARITY ACTIVE_HIGH $pixel_reset
    connect_bd_net $pixel_reset [get_bd_pins capture_input/vid_io_in_reset]
    set interrupt [cip interrupt xilinx.com:ip:xlconcat:2.1]
    set_property -dict [list CONFIG.NUM_PORTS 2 CONFIG.IN0_WIDTH 1 CONFIG.IN1_WIDTH 15] $interrupt
    set padding [cip padding xilinx.com:ip:xlconstant:1.1]
    set_property -dict [list CONFIG.CONST_WIDTH 15 CONFIG.CONST_VAL 0] $padding
    cnet capture_dma/s2mm_introut interrupt/In0
    cnet padding/dout interrupt/In1
    cnet interrupt/dout ps7/IRQ_F2P
    foreach p {overflow underflow} { make_bd_pins_external [get_bd_pins capture_input/$p] }
    assign_bd_address
    assign_bd_address -offset 0x43000000 -range 64K -target_address_space [get_bd_addr_spaces ps7/Data] \
        [get_bd_addr_segs capture_dma/S_AXI_LITE/Reg] -force
    validate_bd_design
    set bits [expr {[get_property LEFT [get_bd_pins capture_dma/s_axis_s2mm_tdata]] + 1}]
    if {$bits != 24 || [get_property CONFIG.c_num_fstores $vdma] != 4 || \
        [get_property CONFIG.c_include_mm2s $vdma] != 0 || 
        [get_property CONFIG.C_EXT_RESET_HIGH $reset] != 0} { error "capture width/frame-store readback mismatch" }
    puts "CAPTURE_CONTRACT: stream=$bits memory=64 frame_stores=4 control=0x43000000 HP0 interrupt=0"
    puts "PASS: C01 capture subsystem BD validation (offline only; overflow ownership and full integration pending)"
} reason]} {
    puts stderr "ERROR: $reason"
    exit 1
}
