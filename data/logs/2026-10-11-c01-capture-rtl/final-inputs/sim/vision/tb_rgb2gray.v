`timescale 1ns/1ps
// rgb2gray 专项 tb：对拍 data/golden/vision/rgb2gray 黄金参考（gen_rgb2gray.py 生成）
module tb_rgb2gray;
    reg clk, in_de;
    reg [23:0] in_rgb;
    wire out_de;
    wire [7:0] out_y;
    integer i, checked, errors;
    reg [23:0] inp [0:127];
    reg [7:0]  exp [0:127];

    rgb2gray dut (
        .clk(clk), .in_de(in_de), .in_rgb(in_rgb),
        .out_de(out_de), .out_y(out_y)
    );
    always #5 clk = ~clk;

    always @(posedge clk) begin
        if (out_de) begin
            if (out_y !== exp[checked]) begin
                errors = errors + 1;
                $display("FAIL: out[%0d]=%02x exp=%02x", checked, out_y, exp[checked]);
                if (errors > 8) $fatal(1);
            end
            checked = checked + 1;
        end
    end

    initial begin
        clk = 0; in_de = 0; in_rgb = 0; checked = 0; errors = 0;
        $readmemh("../data/golden/vision/rgb2gray/input_rgb.hex", inp);
        $readmemh("../data/golden/vision/rgb2gray/expected_y.hex", exp);
        repeat (2) @(negedge clk);
        for (i = 0; i < 128; i = i + 1) begin
            in_de = 1; in_rgb = inp[i]; @(negedge clk);
        end
        in_de = 0;
        repeat (4) @(negedge clk);
        if (checked !== 128 || errors !== 0) begin
            $display("FAIL: collected=%0d errors=%0d (expect 128/0)", checked, errors);
            $fatal(1);
        end
        $display("PASS: rgb2gray 128 px, 0 errors");
        $finish;
    end
endmodule
