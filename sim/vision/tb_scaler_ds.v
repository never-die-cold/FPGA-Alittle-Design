`timescale 1ns/1ps
// scaler 缩小档专项 tb（需求单第二尺寸档）：32x16 -> 8x4，NLINES=8
// 与放大档 tb_scaler 的差异：SH/DH=4 > 1 触发行槽滑动**复用**（同一槽先后承载不同
// 源行）——真实 720p->CNN 输入的工作模式；放大档不覆盖该路径。
// 断言：golden 逐像素（data/golden/vision/scaler_ds）、vs 每帧 1 次、hs 每输出行 1 次（4 行）。
module tb_scaler_ds;
    reg clk, rst_n, in_vs, in_hs, in_de;
    reg [7:0] in_y;
    wire out_de;
    wire s_vs, s_hs;
    wire [7:0] out_y;
    integer checked, errors, l, c, vs_cnt, hs_cnt;
    reg seen_vs;
    reg [7:0] gray [0:511];
    reg [7:0] exp  [0:31];

    scaler #(.SW(32), .SH(16), .DW(8), .DH(4), .NLINES(8)) dut (
        .clk(clk), .rst_n(rst_n),
        .in_vs(in_vs), .in_hs(in_hs), .in_de(in_de), .in_y(in_y),
        .out_vs(s_vs), .out_hs(s_hs), .out_de(out_de), .out_y(out_y)
    );
    always #5 clk = ~clk;

    always @(posedge clk) begin
        if (rst_n) begin
            if (s_vs) begin vs_cnt = vs_cnt + 1; seen_vs = 1; end
            if (s_hs) hs_cnt = hs_cnt + 1;
        end
    end

    always @(posedge clk) begin
        if (rst_n && out_de) begin
            if (!seen_vs) begin
                errors = errors + 1;
                $display("FAIL: out_de before out_vs");
            end
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
        checked = 0; errors = 0; vs_cnt = 0; hs_cnt = 0; seen_vs = 0;
        $readmemh("../data/golden/vision/scaler_ds/input_gray.hex", gray);
        $readmemh("../data/golden/vision/scaler_ds/expected_y.hex", exp);
        repeat (4) @(negedge clk);
        rst_n = 1;
        in_vs = 1; @(negedge clk); in_vs = 0; @(negedge clk);
        for (l = 0; l < 16; l = l + 1) begin
            for (c = 0; c < 32; c = c + 1) begin
                in_de = 1; in_y = gray[l*32+c];
                @(negedge clk);
            end
            in_de = 0; in_y = 0;
            repeat (3) @(negedge clk);
            in_hs = 1; @(negedge clk); in_hs = 0;
            @(negedge clk);
        end
        repeat (1300) @(negedge clk);   // vblank：发射追赶（32 px * 2 拍 + 余量）
        if (checked !== 32 || errors !== 0 || vs_cnt !== 1 || hs_cnt !== 4) begin
            $display("FAIL: collected=%0d errors=%0d vs=%0d hs=%0d (expect 32/0/1/4)",
                     checked, errors, vs_cnt, hs_cnt);
            $fatal(1);
        end
        $display("PASS: scaler_ds 32x16->8x4 downscale, 32 px, 0 errors (slot reuse exercised)");
        $finish;
    end
endmodule
