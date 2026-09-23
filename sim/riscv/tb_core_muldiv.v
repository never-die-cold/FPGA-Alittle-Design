`timescale 1ns / 1ps
// tb_core_muldiv.v —— 预载 RV32IM hello.hex，验证 M 指令整核停顿与写回
module tb_core_muldiv;
    localparam integer RUN_CYCLES = 5000;
    reg clk = 0;
    reg rst_n = 0;
    reg [31:0] imem_rdata = 32'h0000_0013;
    wire [31:0] imem_addr, dmem_addr, dmem_wdata, dmem_rdata;
    wire [3:0] dmem_be;
    wire dmem_we;
    reg [31:0] imem [0:4095];
    reg [31:0] dmem [0:4095];
    integer i;

    always #5 clk = ~clk;
    always @(posedge clk) imem_rdata <= imem[imem_addr[13:2]];
    assign dmem_rdata = dmem[dmem_addr[13:2]];
    always @(posedge clk) begin
        if (dmem_we) begin
            if (dmem_be[0]) dmem[dmem_addr[13:2]][7:0]   <= dmem_wdata[7:0];
            if (dmem_be[1]) dmem[dmem_addr[13:2]][15:8]  <= dmem_wdata[15:8];
            if (dmem_be[2]) dmem[dmem_addr[13:2]][23:16] <= dmem_wdata[23:16];
            if (dmem_be[3]) dmem[dmem_addr[13:2]][31:24] <= dmem_wdata[31:24];
        end
    end

    core_top dut (
        .clk(clk), .rst_n(rst_n), .imem_addr(imem_addr), .imem_rdata(imem_rdata),
        .dmem_addr(dmem_addr), .dmem_wdata(dmem_wdata), .dmem_be(dmem_be),
        .dmem_we(dmem_we), .dmem_rdata(dmem_rdata)
    );

    initial begin
        for (i = 0; i < 4096; i = i + 1) begin
            imem[i] = 32'h0000_0013;
            dmem[i] = 32'd0;
        end
        $readmemh("../src/riscv_fw/hello.hex", imem);
        $dumpfile("tb_core_muldiv.vcd");
        $dumpvars(0, tb_core_muldiv);
        repeat (8) @(posedge clk);
        rst_n = 1'b1;
        repeat (RUN_CYCLES) @(posedge clk);
        if (dmem[4092] !== 32'd142879 || dmem[4093] !== 32'd0)
            $fatal(1, "RV32IM failed: tohost=%0d exit=%0d pc=%h",
                   dmem[4092], dmem[4093], imem_addr);
        $display("PASS: RV32IM core tohost=%0d exit=%0d", dmem[4092], dmem[4093]);
        $finish;
    end
endmodule
