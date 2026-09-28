`timescale 1ns/1ps
// 链式冒烟 tb：rgb2gray -> gaussian_3x3 级联
// 级间约定：rgb2gray 的 de 延迟 1 拍，vs/hs 标记同步延迟 1 拍再进下级（真实
// vision_top 中标记随像素流同拍传播，本级 tb 用寄存器模拟该延迟）。
// 判据：中间级对拍 gray 黄金参考，末端对拍 gaussian 黄金参考（复用现有 golden）。
module tb_chain;
    reg clk, rst_n, in_vs, in_hs, in_de;
    reg [23:0] in_rgb;
    wire       g_de, s_de;
    wire [7:0] g_y, s_g;
    reg vs_d, hs_d;
    integer g_checked, g_errors, s_checked, s_errors, i, l, c;
    reg [23:0] rgb      [0:127];
    reg [7:0]  exp_gray [0:127];
    reg [7:0]  exp_gauss[0:127];

    rgb2gray u_gray (
        .clk(clk), .in_de(in_de), .in_rgb(in_rgb),
        .out_de(g_de), .out_y(g_y)
    );
    gaussian_3x3 #(.WIDTH(16), .HEIGHT(8)) u_gauss (
        .clk(clk), .rst_n(rst_n),
        .in_vs(vs_d), .in_hs(hs_d), .in_de(g_de), .in_y(g_y),
        .out_de(s_de), .out_g(s_g)
    );
    always #5 clk = ~clk;

    // 标记与像素同步延迟 1 拍
    always @(posedge clk) begin
        vs_d <= in_vs;
        hs_d <= in_hs;
    end

    always @(posedge clk) begin
        if (rst_n && g_de) begin
            if (g_y !== exp_gray[g_checked]) begin
                g_errors = g_errors + 1;
                $display("FAIL: gray[%0d]=%02x exp=%02x", g_checked, g_y, exp_gray[g_checked]);
                if (g_errors > 8) $fatal(1);
            end
            g_checked = g_checked + 1;
        end
    end

    always @(posedge clk) begin
        if (rst_n && s_de) begin
            if (s_g !== exp_gauss[s_checked]) begin
                s_errors = s_errors + 1;
                $display("FAIL: gauss[%0d]=%02x exp=%02x", s_checked, s_g, exp_gauss[s_checked]);
                if (s_errors > 8) $fatal(1);
            end
            s_checked = s_checked + 1;
        end
    end

    initial begin
        clk = 0; rst_n = 0; in_vs = 0; in_hs = 0; in_de = 0; in_rgb = 0;
        vs_d = 0; hs_d = 0;
        g_checked = 0; g_errors = 0; s_checked = 0; s_errors = 0;
        $readmemh("../data/golden/vision/rgb2gray/input_rgb.hex", rgb);
        $readmemh("../data/golden/vision/rgb2gray/expected_y.hex", exp_gray);
        $readmemh("../data/golden/vision/gaussian3x3/expected_y.hex", exp_gauss);
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
        repeat (40) @(negedge clk);
        if (g_checked !== 128 || g_errors !== 0 || s_checked !== 128 || s_errors !== 0) begin
            $display("FAIL: gray %0d/%0d errs, gauss %0d/%0d errs (expect 128/0 each)",
                     g_checked, g_errors, s_checked, s_errors);
            $fatal(1);
        end
        $display("PASS: chain rgb2gray->gaussian, gray 128 px + gauss 128 px, 0 errors");
        $finish;
    end
endmodule
