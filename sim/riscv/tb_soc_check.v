`timescale 1ns / 1ps
// tb_soc_check.v —— 真实固件路径验证 DMEM 预载与 SoC 计时器。
module tb_soc_check;
    localparam integer RUN_CYCLES = 3000;
    localparam [12:0] TOHOST_INDEX = 13'h0FFC;
    localparam [12:0] TOEXIT_INDEX = 13'h0FFD;
    localparam [31:0] PASS_VALUE = 32'h534F_4301;

    reg clk = 1'b0;
    reg rst_n = 1'b0;
    reg [31:0] mem0_before;
    wire [3:0] led;

    always #5 clk = ~clk;

    soc_top #(
        .IMEM_INIT_FILE("../src/riscv_fw/soc_check.hex"),
        .DMEM_INIT_FILE("../src/riscv_fw/soc_check.hex")
    ) dut (
        .clk(clk), .rst_n(rst_n), .led(led)
    );

    initial begin
        $dumpfile("tb_soc_check.vcd");
        $dumpvars(0, tb_soc_check);

        mem0_before = dut.u_dmem.mem[0];
        repeat (8) @(posedge clk);
        @(negedge clk);
        rst_n = 1'b1;
        repeat (RUN_CYCLES) @(posedge clk);
        #1;

        if (dut.u_dmem.mem[TOHOST_INDEX] !== PASS_VALUE)
            $fatal(1, "soc_check tohost failed: value=%h",
                   dut.u_dmem.mem[TOHOST_INDEX]);
        if (dut.u_dmem.mem[TOEXIT_INDEX] !== 32'd0)
            $fatal(1, "soc_check exit failed: value=%0d",
                   dut.u_dmem.mem[TOEXIT_INDEX]);
        if (dut.u_dmem.mem[0] !== mem0_before)
            $fatal(1, "timer store leaked into DMEM[0]: before=%h after=%h",
                   mem0_before, dut.u_dmem.mem[0]);
        if (dut.cycle_cnt !== RUN_CYCLES)
            $fatal(1, "timer count failed: value=%0d", dut.cycle_cnt);
        if (led !== PASS_VALUE[3:0])
            $fatal(1, "soc_check LED failed: led=%b", led);

        $display("PASS: soc_check preload/timer/read-write path tohost=%h cycles=%0d",
                 dut.u_dmem.mem[TOHOST_INDEX], dut.cycle_cnt);
        $finish;
    end
endmodule
