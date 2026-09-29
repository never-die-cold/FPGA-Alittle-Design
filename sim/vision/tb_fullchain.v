`timescale 1ns/1ps
// 全链冒烟 tb：rgb2gray -> gaussian_3x3 -> scaler（16x8 -> 32x16）
// 级间全部使用各级自产的 out_vs/out_hs/out_de 标记（含 gaussian 末行冲刷的合成 hs），
// tb 只驱动 rgb 源帧——验证真实 vision_top 的级联形态。
// 判据：三级中间流分别对拍单级 golden，末端对拍 expected_fullchain.hex。
module tb_fullchain;
    reg clk, rst_n, in_vs, in_hs, in_de;
    reg [23:0] in_rgb;
    wire g_vs, g_hs, g_de, s_vs, s_hs, s_de, c_vs, c_hs, c_de;
    wire [7:0] g_y, s_g, c_y;
    integer g_checked, g_errors, s_checked, s_errors, c_checked, c_errors, l, c;
    reg [23:0] rgb       [0:127];
    reg [7:0]  exp_gray  [0:127];
    reg [7:0]  exp_gauss [0:127];
    reg [7:0]  exp_chain [0:511];

    rgb2gray u_gray (
        .clk(clk), .in_vs(in_vs), .in_hs(in_hs), .in_de(in_de), .in_rgb(in_rgb),
        .out_vs(g_vs), .out_hs(g_hs), .out_de(g_de), .out_y(g_y)
    );
    gaussian_3x3 #(.WIDTH(16), .HEIGHT(8)) u_gauss (
        .clk(clk), .rst_n(rst_n),
        .in_vs(g_vs), .in_hs(g_hs), .in_de(g_de), .in_y(g_y),
        .out_vs(s_vs), .out_hs(s_hs), .out_de(s_de), .out_g(s_g)
    );
    scaler #(.SW(16), .SH(8), .DW(32), .DH(16), .NLINES(16)) u_scaler (
        .clk(clk), .rst_n(rst_n),
        .in_vs(s_vs), .in_hs(s_hs), .in_de(s_de), .in_y(s_g),
        .out_vs(c_vs), .out_hs(c_hs), .out_de(c_de), .out_y(c_y)
    );
    always #5 clk = ~clk;

    always @(posedge clk) begin
        if (rst_n && g_de) begin
            if (g_y !== exp_gray[g_checked]) begin
                g_errors = g_errors + 1;
                $display("FAIL: gray[%0d]=%02x exp=%02x", g_checked, g_y, exp_gray[g_checked]);
                if (g_errors > 4) $fatal(1);
            end
            g_checked = g_checked + 1;
        end
    end

    always @(posedge clk) begin
        if (rst_n && s_de) begin
            if (s_g !== exp_gauss[s_checked]) begin
                s_errors = s_errors + 1;
                $display("FAIL: gauss[%0d]=%02x exp=%02x", s_checked, s_g, exp_gauss[s_checked]);
                if (s_errors > 4) $fatal(1);
            end
            s_checked = s_checked + 1;
        end
    end

    always @(posedge clk) begin
        if (rst_n && c_de) begin
            if (c_y !== exp_chain[c_checked]) begin
                c_errors = c_errors + 1;
                $display("FAIL: chain[%0d]=%02x exp=%02x", c_checked, c_y, exp_chain[c_checked]);
                if (c_errors > 4) $fatal(1);
            end
            c_checked = c_checked + 1;
        end
    end

    initial begin
        clk = 0; rst_n = 0; in_vs = 0; in_hs = 0; in_de = 0; in_rgb = 0;
        g_checked = 0; g_errors = 0; s_checked = 0; s_errors = 0;
        c_checked = 0; c_errors = 0;
        $readmemh("../data/golden/vision/rgb2gray/input_rgb.hex", rgb);
        $readmemh("../data/golden/vision/rgb2gray/expected_y.hex", exp_gray);
        $readmemh("../data/golden/vision/gaussian3x3/expected_y.hex", exp_gauss);
        $readmemh("../data/golden/vision/fullchain/expected_fullchain.hex", exp_chain);
        repeat (4) @(negedge clk);
        rst_n = 1;
        in_vs = 1; @(negedge clk); in_vs = 0; @(negedge clk);
        for (l = 0; l < 8; l = l + 1) begin
            for (c = 0; c < 16; c = c + 1) begin
                in_de = 1; in_rgb = rgb[l*16+c];
                @(negedge clk);
            end
            in_de = 0; in_rgb = 0;
            repeat (3) @(negedge clk);
            in_hs = 1; @(negedge clk); in_hs = 0;
            @(negedge clk);
        end
        repeat (1400) @(negedge clk);   // vblank：gaussian 冲刷 + scaler 发射追赶
        if (g_checked !== 128 || g_errors !== 0 ||
            s_checked !== 128 || s_errors !== 0 ||
            c_checked !== 512 || c_errors !== 0) begin
            $display("FAIL: gray %0d/%0d, gauss %0d/%0d, chain %0d/%0d (expect 128/0, 128/0, 512/0)",
                     g_checked, g_errors, s_checked, s_errors, c_checked, c_errors);
            $fatal(1);
        end
        $display("PASS: fullchain gray 128 + gauss 128 + scaler 512 px, 0 errors");
        $finish;
    end
endmodule
