`timescale 1ns / 1ps
// tb_muldiv.v —— RV32M 乘除单元模块级自检：8 种操作、边界与握手
module tb_muldiv;
    localparam integer CLK_PERIOD = 10;

    reg clk = 0;
    reg rst_n = 1;
    reg [2:0] op = 0;
    reg start = 0;
    reg [31:0] a = 0;
    reg [31:0] b = 0;
    wire [31:0] result;
    wire busy;
    wire done;
    integer i;

    always #(CLK_PERIOD / 2) clk = ~clk;

    muldiv dut (
        .clk(clk), .rst_n(rst_n), .op(op), .start(start),
        .a(a), .b(b), .result(result), .busy(busy), .done(done)
    );

    task automatic check_op;
        input [2:0] test_op;
        input [31:0] test_a;
        input [31:0] test_b;
        input [31:0] expected;
        begin
            @(negedge clk);
            op = test_op; a = test_a; b = test_b; start = 1'b1;
            @(posedge clk); #1;
            if (!busy || done) $fatal(1, "start handshake failed: op=%b", test_op);

            @(negedge clk);
            start = 1'b0; op = ~test_op; a = ~test_a; b = ~test_b;
            for (i = 0; i < 31; i = i + 1) begin
                if (i == 1) start = 1'b1; // busy 时的二次启动必须被忽略
                else        start = 1'b0;
                @(posedge clk); #1;
                if (!busy || done)
                    $fatal(1, "early completion: op=%b iteration=%0d", test_op, i);
            end
            start = 1'b0;

            @(posedge clk); #1;
            if (busy || !done || result !== expected)
                $fatal(1, "result failed: op=%b a=%h b=%h got=%h expected=%h",
                       test_op, test_a, test_b, result, expected);
            @(posedge clk); #1;
            if (done || result !== expected)
                $fatal(1, "done pulse/result hold failed: op=%b", test_op);
        end
    endtask

    initial begin
        $dumpfile("tb_muldiv.vcd");
        $dumpvars(0, tb_muldiv);
        #1 rst_n = 0;
        #1;
        if (busy || done || result !== 32'd0) $fatal(1, "reset failed");
        #1 rst_n = 1;

        check_op(3'b000, 32'hFFFF_FFFE, 32'd3,         32'hFFFF_FFFA); // mul
        check_op(3'b001, 32'hFFFF_FFFE, 32'd3,         32'hFFFF_FFFF); // mulh
        check_op(3'b010, 32'hFFFF_FFFE, 32'h8000_0000, 32'hFFFF_FFFF); // mulhsu
        check_op(3'b011, 32'hFFFF_FFFF, 32'hFFFF_FFFF, 32'hFFFF_FFFE); // mulhu
        check_op(3'b100, 32'hFFFF_FFF9, 32'd3,         32'hFFFF_FFFE); // div
        check_op(3'b101, 32'hFFFF_FFFF, 32'd2,         32'h7FFF_FFFF); // divu
        check_op(3'b110, 32'hFFFF_FFF9, 32'd3,         32'hFFFF_FFFF); // rem
        check_op(3'b111, 32'hFFFF_FFFF, 32'd2,         32'd1);         // remu
        check_op(3'b100, 32'hFFFF_FFF9, 32'd0,         32'hFFFF_FFFF); // div by zero
        check_op(3'b110, 32'hFFFF_FFF9, 32'd0,         32'hFFFF_FFF9); // rem by zero
        check_op(3'b100, 32'h8000_0000, 32'hFFFF_FFFF, 32'h8000_0000); // overflow
        check_op(3'b110, 32'h8000_0000, 32'hFFFF_FFFF, 32'd0);         // overflow rem

        @(negedge clk);
        op = 3'b000; a = 32'd7; b = 32'd3; start = 1'b1;
        @(posedge clk); #1 rst_n = 1'b0; #1;
        if (busy || done || result !== 32'd0) $fatal(1, "reset did not cancel operation");

        $display("PASS: muldiv 8 operations, boundaries and handshake");
        $finish;
    end
endmodule
