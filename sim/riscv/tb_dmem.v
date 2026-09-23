`timescale 1ns / 1ps
// tb_dmem.v —— 验证 32KB 数据存储器的异步读、字节写和高地址索引
module tb_dmem;
    reg clk = 1'b0;
    reg we = 1'b0;
    reg [3:0] be = 4'b0000;
    reg [31:0] addr = 32'h8000_0000;
    reg [31:0] wdata = 32'h0000_0000;
    wire [31:0] rdata;

    always #5 clk = ~clk;

    dmem dut (
        .clk(clk), .we(we), .be(be), .addr(addr),
        .wdata(wdata), .rdata(rdata)
    );

    initial begin
        #1;
        if (rdata !== 32'h0000_0000)
            $fatal(1, "initial value is not zero: %h", rdata);

        // 低地址整字写。
        wdata = 32'hAABB_CCDD; be = 4'b1111; we = 1'b1;
        @(posedge clk); #1; we = 1'b0;
        if (rdata !== 32'hAABB_CCDD)
            $fatal(1, "word write failed: %h", rdata);

        // 地址变化后同拍读出高半区，且不能别名到低地址。
        addr = 32'h8000_4000; #1;
        if (rdata !== 32'h0000_0000)
            $fatal(1, "async read/high address alias failed: %h", rdata);

        // 分两拍更新高地址的四个字节车道。
        wdata = 32'h1122_3344; be = 4'b0101; we = 1'b1;
        @(posedge clk); #1;
        wdata = 32'hABCD_0000; be = 4'b1100;
        @(posedge clk); #1; we = 1'b0;
        if (rdata !== 32'hABCD_0044)
            $fatal(1, "byte enable write failed: %h", rdata);

        // we=0 时即使 be 全开也不能改写。
        wdata = 32'hFFFF_FFFF; be = 4'b1111;
        @(posedge clk); #1;
        if (rdata !== 32'hABCD_0044)
            $fatal(1, "write disable failed: %h", rdata);

        addr = 32'h8000_0000; #1;
        if (rdata !== 32'hAABB_CCDD)
            $fatal(1, "low word corrupted: %h", rdata);

        $display("PASS: dmem async read, byte writes and addr[14:2] indexing");
        $finish;
    end
endmodule
