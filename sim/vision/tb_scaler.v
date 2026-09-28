`timescale 1ns/1ps
// scaler 专项 tb：对拍 data/golden/vision/scaler 黄金参考（gen_scaler.py 生成）
// 帧时序遵循模块流约定；发射落后于源写入，vblank 给足 1300 拍（约定 >= WIDTH+8）
module tb_scaler;
    reg clk, rst_n, in_vs, in_hs, in_de;
    reg [7:0] in_y;
    wire out_de;
    wire [7:0] out_y;
    integer checked, errors, l, c;
    reg [7:0] gray [0:127];
    reg [7:0] exp  [0:511];

    scaler #(.SW(16), .SH(8), .DW(32), .DH(16), .NLINES(16)) dut (
        .clk(clk), .rst_n(rst_n),
        .in_vs(in_vs), .in_hs(in_hs), .in_de(in_de), .in_y(in_y),
        .out_de(out_de), .out_y(out_y)
    );
    always #5 clk = ~clk;

    always @(posedge clk) begin
        if (rst_n && out_de) begin
            if (out_y !== exp[checked]) begin
                errors = errors + 1;
                $display("FAIL: out[%0d]=%02x exp=%02x", checked, out_y, exp[checked]);
                if (errors > 8) $fatal(1);
            end
            checked = checked + 1;
        end
    end

    initial begin
        clk = 0; rst_n = 0; in_vs = 0; in_hs = 0; in_de = 0; in_y = 0;
        checked = 0; errors = 0;
        $readmemh("../data/golden/vision/scaler/input_gray.hex", gray);
        $readmemh("../data/golden/vision/scaler/expected_y.hex", exp);
        repeat (4) @(negedge clk);
        rst_n = 1;
        in_vs = 1; @(negedge clk); in_vs = 0; @(negedge clk);
        for (l = 0; l < 8; l = l + 1) begin
            for (c = 0; c < 16; c = c + 1) begin
                in_de = 1; in_y = gray[l*16+c];
                @(negedge clk);
            end
            in_de = 0; in_y = 0;
            repeat (3) @(negedge clk);
            in_hs = 1; @(negedge clk); in_hs = 0;
            @(negedge clk);
        end
        repeat (1300) @(negedge clk);   // vblank：发射追赶（512 px * 2 拍 + 余量）
        if (checked !== 512 || errors !== 0) begin
            $display("FAIL: collected=%0d errors=%0d (expect 512/0)", checked, errors);
            $fatal(1);
        end
        $display("PASS: scaler 16x8->32x16, 512 px, 0 errors");
        $finish;
    end
endmodule
