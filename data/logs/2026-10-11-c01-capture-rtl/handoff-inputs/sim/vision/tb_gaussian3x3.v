`timescale 1ns/1ps
// gaussian_3x3 专项 tb：对拍 data/golden/vision/gaussian3x3 黄金参考（gen_gaussian3x3.py 生成）
// 帧时序遵循模块流约定：vs 单拍 -> 8 行（16 de + 3 空拍 + hs + 1 空拍）-> vblank(>=WIDTH+8) 末行冲刷
module tb_gaussian3x3;
    reg clk, rst_n, in_vs, in_hs, in_de;
    reg [7:0] in_y;
    wire out_de;
    wire [7:0] out_g;
    integer checked, errors, l, c;
    reg [7:0] gray [0:127];
    reg [7:0] exp  [0:127];

    gaussian_3x3 #(.WIDTH(16), .HEIGHT(8)) dut (
        .clk(clk), .rst_n(rst_n),
        .in_vs(in_vs), .in_hs(in_hs), .in_de(in_de), .in_y(in_y),
        .out_de(out_de), .out_g(out_g)
    );
    always #5 clk = ~clk;

    always @(posedge clk) begin
        if (rst_n && out_de) begin
            if (out_g !== exp[checked]) begin
                errors = errors + 1;
                $display("FAIL: out[%0d]=%02x exp=%02x", checked, out_g, exp[checked]);
                if (errors > 8) $fatal(1);
            end
            checked = checked + 1;
        end
    end

    initial begin
        clk = 0; rst_n = 0; in_vs = 0; in_hs = 0; in_de = 0; in_y = 0;
        checked = 0; errors = 0;
        $readmemh("../data/golden/vision/gaussian3x3/input_gray.hex", gray);
        $readmemh("../data/golden/vision/gaussian3x3/expected_y.hex", exp);
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
        repeat (40) @(negedge clk);   // vblank：末行冲刷（约定 >= WIDTH+8 拍）
        if (checked !== 128 || errors !== 0) begin
            $display("FAIL: collected=%0d errors=%0d (expect 128/0)", checked, errors);
            $fatal(1);
        end
        $display("PASS: gaussian3x3 128 px, 0 errors");
        $finish;
    end
endmodule
