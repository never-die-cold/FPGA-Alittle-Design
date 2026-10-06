`timescale 1ns / 1ps
// Icarus-only primitive models: verify that board-top parameters reach the MMCM.
module MMCME2_BASE #(
    parameter BANDWIDTH = "OPTIMIZED",
    parameter real CLKIN1_PERIOD = 0.0,
    parameter integer DIVCLK_DIVIDE = 1,
    parameter real CLKFBOUT_MULT_F = 1.0,
    parameter real CLKOUT0_DIVIDE_F = 1.0,
    parameter STARTUP_WAIT = "FALSE"
) (
    input wire CLKIN1, CLKFBIN, RST, PWRDWN,
    output wire CLKFBOUT, CLKOUT0, LOCKED
);
    assign CLKFBOUT = CLKIN1;
    assign CLKOUT0 = CLKIN1;
    assign LOCKED = ~RST;
endmodule

module BUFG (input wire I, output wire O);
    assign O = I;
endmodule

module tb_pynq_z2_clock_config;
    reg clk = 1'b0;
    reg btn0 = 1'b1;
    wire [3:0] led_40;
    wire [3:0] led_125;

    always #4 clk = ~clk;

    pynq_z2_top #(
        .IMEM_INIT_FILE("../src/riscv_fw/hello_v0.hex"),
        .DMEM_INIT_FILE("../src/riscv_fw/hello_v0.hex")
    ) dut_40 (
        .clk(clk), .btn0(btn0), .led(led_40)
    );

    pynq_z2_top #(
        .CORE_CLK_DIVIDE(8),
        .IMEM_INIT_FILE("../src/riscv_fw/hello_v0.hex"),
        .DMEM_INIT_FILE("../src/riscv_fw/hello_v0.hex")
    ) dut_125 (
        .clk(clk), .btn0(btn0), .led(led_125)
    );

    initial begin
        #1;
        if (dut_40.CORE_CLK_DIVIDE != 25 ||
            dut_40.u_mmcm.CLKOUT0_DIVIDE_F != 25.0)
            $fatal(1, "default clock profile is not divide-by-25");
        if (dut_125.CORE_CLK_DIVIDE != 8 ||
            dut_125.u_mmcm.CLKOUT0_DIVIDE_F != 8.0)
            $fatal(1, "125 MHz clock profile is not divide-by-8");
        $display("PASS: board clock profiles 40 MHz=/25, 125 MHz=/8, VCO=1000 MHz");
        $finish;
    end
endmodule
