`timescale 1ns / 1ps
// tb_soc_top.v —— hello_v0 SoC 冒烟：tohost、LED 锁存与复位
module tb_soc_top;
    localparam integer RUN_CYCLES = 4000;
    localparam [12:0] TOHOST_INDEX = 13'h0FFC;
    localparam [12:0] TOEXIT_INDEX = 13'h0FFD;

    reg clk = 1'b0;
    reg rst_n = 1'b0;
    wire [3:0] led;

    always #5 clk = ~clk;

    soc_top #(
        .IMEM_INIT_FILE("../src/riscv_fw/hello_v0.hex")
    ) dut (
        .clk(clk), .rst_n(rst_n), .led(led)
    );

    initial begin
        $dumpfile("tb_soc_top.vcd");
        $dumpvars(0, tb_soc_top);

        repeat (8) @(posedge clk);
        if (led !== 4'b0000)
            $fatal(1, "LED reset failed: led=%b", led);

        @(negedge clk);
        rst_n = 1'b1;
        repeat (RUN_CYCLES) @(posedge clk);

        if (dut.u_dmem.mem[TOHOST_INDEX] !== 32'd13)
            $fatal(1, "tohost failed: value=%0d", dut.u_dmem.mem[TOHOST_INDEX]);
        if (dut.u_dmem.mem[TOEXIT_INDEX] !== 32'd0)
            $fatal(1, "tohost_exit failed: value=%0d", dut.u_dmem.mem[TOEXIT_INDEX]);
        if (led !== 4'b1101)
            $fatal(1, "LED latch failed: led=%b", led);

        @(negedge clk);
        rst_n = 1'b0;
        #1;
        if (led !== 4'b0000)
            $fatal(1, "LED re-reset failed: led=%b", led);

        $display("PASS: SoC tohost=13, tohost_exit=0, LED=1101, reset LED=0000");
        $finish;
    end
endmodule
