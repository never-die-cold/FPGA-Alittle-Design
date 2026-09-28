`timescale 1ns / 1ps
// tb_soc_top.v —— hello_v0 SoC 冒烟：tohost、LED 锁存与复位
module tb_soc_top;
    localparam integer RUN_CYCLES = 4000;
    localparam [31:0] TIMER_ADDR = 32'h8000_8000;
    localparam [12:0] TOHOST_INDEX = 13'h0FFC;
    localparam [12:0] TOEXIT_INDEX = 13'h0FFD;

    reg clk = 1'b0;
    reg rst_n = 1'b0;
    reg [31:0] mem0_before;
    wire [3:0] led;

    always #5 clk = ~clk;

    soc_top #(
        .IMEM_INIT_FILE("../src/riscv_fw/hello_v0.hex"),
        .DMEM_INIT_FILE("../src/riscv_fw/hello_v0.hex")
    ) dut (
        .clk(clk), .rst_n(rst_n), .led(led)
    );

    initial begin
        $dumpfile("tb_soc_top.vcd");
        $dumpvars(0, tb_soc_top);

        repeat (8) @(posedge clk);
        if (led !== 4'b0000)
            $fatal(1, "LED reset failed: led=%b", led);
        if (dut.cycle_cnt !== 32'd0)
            $fatal(1, "timer reset failed: cycle_cnt=%0d", dut.cycle_cnt);

        @(negedge clk);
        rst_n = 1'b1;
        repeat (3) @(posedge clk);
        #1;
        if (dut.cycle_cnt !== 32'd3)
            $fatal(1, "timer increment failed: cycle_cnt=%0d", dut.cycle_cnt);
        repeat (RUN_CYCLES - 3) @(posedge clk);
        #1;

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
        if (dut.cycle_cnt !== 32'd0)
            $fatal(1, "timer re-reset failed: cycle_cnt=%0d", dut.cycle_cnt);

        mem0_before = dut.u_dmem.mem[0];
        force dut.dmem_addr = TIMER_ADDR;
        force dut.dmem_wdata = 32'hDEAD_BEEF;
        force dut.dmem_be = 4'hF;
        force dut.dmem_we = 1'b1;
        #1;
        if (dut.dmem_rdata !== 32'd0)
            $fatal(1, "timer read failed in reset: rdata=%0d", dut.dmem_rdata);
        @(posedge clk);
        #1;
        if (dut.u_dmem.mem[0] !== mem0_before)
            $fatal(1, "timer write leaked into DMEM[0]: value=%h",
                   dut.u_dmem.mem[0]);
        release dut.dmem_addr;
        release dut.dmem_wdata;
        release dut.dmem_be;
        release dut.dmem_we;

        @(negedge clk);
        rst_n = 1'b1;
        repeat (RUN_CYCLES) @(posedge clk);
        #1;

        if (dut.u_dmem.mem[TOHOST_INDEX] !== 32'd65)
            $fatal(1, "second-run tohost failed: value=%0d",
                   dut.u_dmem.mem[TOHOST_INDEX]);
        if (led !== 4'b0001)
            $fatal(1, "second-run LED failed: led=%b", led);

        $display("PASS: SoC first-run=13/1101, timer reset/increment/write-ignore, second-run=65/0001");
        $finish;
    end
endmodule
