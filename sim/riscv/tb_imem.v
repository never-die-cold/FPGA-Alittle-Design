`timescale 1ns / 1ps
// tb_imem.v —— 验证 32KB 指令存储器的同步读、预载与高地址索引
module tb_imem;
    reg clk = 1'b0;
    reg [31:0] addr = 32'h8000_0000;
    wire [31:0] rdata;

    always #5 clk = ~clk;

    imem #(
        .INIT_FILE("../src/riscv_fw/hello.hex")
    ) dut (
        .clk(clk),
        .addr(addr),
        .rdata(rdata)
    );

    initial begin
        // 输出初值为 NOP；首个上升沿后才返回地址 0 的预载指令。
        #1;
        if (rdata !== 32'h0000_0013)
            $fatal(1, "initial rdata is not NOP: %h", rdata);
        @(posedge clk); #1;
        if (rdata !== 32'h0000_8117)
            $fatal(1, "preload/base read failed: %h", rdata);

        // 改地址不能同拍改变输出；下一上升沿才读出高半区的 NOP。
        @(negedge clk);
        addr = 32'h8000_4000;
        #1;
        if (rdata !== 32'h0000_8117)
            $fatal(1, "read is not synchronous: %h", rdata);
        @(posedge clk); #1;
        if (rdata !== 32'h0000_0013)
            $fatal(1, "high address aliased to low half: %h", rdata);

        @(negedge clk);
        addr = 32'h8000_0004;
        @(posedge clk); #1;
        if (rdata !== 32'h0001_0113)
            $fatal(1, "second preload word failed: %h", rdata);

        $display("PASS: imem preload, synchronous read and addr[14:2] indexing");
        $finish;
    end
endmodule
