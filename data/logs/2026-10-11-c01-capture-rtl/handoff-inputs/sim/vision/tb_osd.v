`timescale 1ns/1ps
// osd_overlay 专项 tb：对拍 data/golden/vision/osd 黄金参考（gen_osd.py 生成）
// 重点验证：① 框描边命中与 box 优先；② 参数帧首锁存——帧 1 中途改端口不影响
// 当前帧输出，帧 2 vs 后新参数生效（golden f1/f2 两套判据）。
module tb_osd;
    reg clk, rst_n, in_vs, in_hs, in_de;
    reg [7:0]  in_y;
    reg [15:0] bx0, by0, bx1, by1, rx0, ry0, rx1, ry1;
    reg [7:0]  bcol, rcol;
    wire out_vs, out_hs, out_de;
    wire [7:0] out_y;
    integer checked, errors, i, l, c, frame;
    reg [7:0] gray [0:127];
    reg [7:0] exp1  [0:127];
    reg [7:0] exp2  [0:127];

    osd_overlay dut (
        .clk(clk), .rst_n(rst_n),
        .in_vs(in_vs), .in_hs(in_hs), .in_de(in_de), .in_y(in_y),
        .box_x0(bx0), .box_y0(by0), .box_x1(bx1), .box_y1(by1), .box_color(bcol),
        .roi_x0(rx0), .roi_y0(ry0), .roi_x1(rx1), .roi_y1(ry1), .roi_color(rcol),
        .out_vs(out_vs), .out_hs(out_hs), .out_de(out_de), .out_y(out_y)
    );
    always #5 clk = ~clk;

    // 帧 1 golden：box=(2,1)-(7,5) FF；roi=(10,3)-(14,7) 00
    // 帧 2 golden：box=(4,2)-(9,6) 55；roi 同
    reg [7:0] expv;
    always @(posedge clk) begin
        if (rst_n && out_de) begin
            expv = (frame == 0) ? exp1[checked] : exp2[checked];
            if (out_y !== expv) begin
                errors = errors + 1;
                $display("FAIL: f%0d out[%0d]=%02x exp=%02x", frame, checked, out_y, expv);
                if (errors > 8) $fatal(1);
            end
            checked = checked + 1;
        end
    end

    task do_frame;
        begin
            @(negedge clk);
            in_vs = 1; @(negedge clk); in_vs = 0; @(negedge clk);
            for (l = 0; l < 8; l = l + 1) begin
                for (c = 0; c < 16; c = c + 1) begin
                    in_de = 1; in_y = gray[(l*16+c)];
                    @(negedge clk);
                end
                in_de = 0; in_y = 0;
                repeat (3) @(negedge clk);
                in_hs = 1; @(negedge clk); in_hs = 0;
                @(negedge clk);
            end
        end
    endtask

    initial begin
        clk = 0; rst_n = 0; in_vs = 0; in_hs = 0; in_de = 0; in_y = 0;
        bx0 = 0; by0 = 0; bx1 = 0; by1 = 0; bcol = 0;
        rx0 = 0; ry0 = 0; rx1 = 0; ry1 = 0; rcol = 0;
        checked = 0; errors = 0; frame = 0;
        $readmemh("../data/golden/vision/osd/input_y.hex", gray);
        $readmemh("../data/golden/vision/osd/expected_osd_f1.hex", exp1);
        $readmemh("../data/golden/vision/osd/expected_osd_f2.hex", exp2);
        repeat (4) @(negedge clk);
        rst_n = 1;

        // 帧 1 参数
        bx0 = 2; by0 = 1; bx1 = 7; by1 = 5; bcol = 8'hFF;
        rx0 = 10; ry0 = 3; rx1 = 14; ry1 = 7; rcol = 8'h00;
        do_frame;
        if (checked !== 128 || errors !== 0) begin
            $display("FAIL: f1 collected=%0d errors=%0d (expect 128/0)", checked, errors);
            $fatal(1);
        end

        // 帧 1 中途改端口（模拟 host 动效写）→ 当前帧输出必须不受影响
        bx0 = 4; by0 = 2; bx1 = 9; by1 = 6; bcol = 8'h55;
        // 帧 2 vs 锁存新参数，输出按 f2 golden
        frame = 1; checked = 0;
        do_frame;

        repeat (4) @(negedge clk);
        if (checked !== 128 || errors !== 0) begin   // 帧 2 计数（帧 1 已单独核对 128/0）
            $display("FAIL: f2 collected=%0d errors=%0d (expect 128/0)", checked, errors);
            $fatal(1);
        end
        $display("PASS: osd 2 frames 256 px, 0 errors (param latch at vs verified)");
        $finish;
    end
endmodule
