`timescale 1ns/1ps
// vision_top 专项 tb：六帧拓扑序列 + 双通道对拍（v0.3 双路径）+ 帧内改 R0 锁存验证
//   显示通道 out_*（全分辨率）：
//   帧 1：R0=0（gray）    → expA（128px）      帧 2：R0=gauss → expB（128px）；
//         第 4 行后帧内写 R0=0 → 帧 2 输出不变（拓扑帧锁存）
//   帧 3：拓扑=gray       → expA（128px）      帧 4：R0=gauss|scaler → 显示=expB（scaler 不上屏）
//   帧 5：R0=gauss|sobel  → expC（128px）      帧 6：R0=sobel → expE（128px）
//   快照通道 cop_*：仅帧 4 scaler 使能 → expD（512px）；其余帧 cop_de 恒 0
module tb_top;
    reg clk, rst_n, in_vs, in_hs, in_de;
    reg [23:0] in_rgb;
    reg        awvalid, wvalid, arvalid, bready, rready;
    reg [6:0]  awaddr, araddr;
    reg [31:0] wdata;
    reg [3:0]  wstrb;
    wire       awready, wready, arready, bvalid, rvalid;
    wire [1:0] bresp, rresp;
    wire [31:0] rdata;
    wire out_vs, out_hs, out_de;
    wire [7:0] out_y;
    wire cop_vs, cop_hs, cop_de;
    wire [7:0] cop_y;
    integer fidx, f, l, c, errors;
    integer fcnt [0:5];       // 显示通道逐帧计数
    integer fcnt_c;           // 快照通道计数
    // A5 逐像素延迟：首 in_de → 首 out_de 周期差（显示通道，恒定流水延迟）
    integer cyc, in_first, out_first, lat_err;
    integer lat [0:5];
    reg in_seen, out_seen;
    reg [7:0] expv;
    reg [23:0] rgb      [0:127];
    reg [7:0]  expA     [0:127];   // gray golden
    reg [7:0]  expB     [0:127];   // gaussian golden
    reg [7:0]  expD     [0:511];   // fullchain golden（快照通道）
    reg [7:0]  expC     [0:127];   // gauss|sobel golden
    reg [7:0]  expE     [0:127];   // gray|sobel golden

    vision_top #(.SW(16), .SH(8), .DW(32), .DH(16), .NLINES(16)) dut (
        .clk(clk), .s_axi_aclk(clk), .rst_n(rst_n),
        .in_vs(in_vs), .in_hs(in_hs), .in_de(in_de), .in_rgb(in_rgb),
        .awvalid(awvalid), .awready(awready), .awaddr(awaddr),
        .wvalid(wvalid), .wready(wready), .wdata(wdata), .wstrb(wstrb),
        .bvalid(bvalid), .bready(bready), .bresp(bresp),
        .arvalid(arvalid), .arready(arready), .araddr(araddr),
        .rvalid(rvalid), .rready(rready), .rdata(rdata), .rresp(rresp),
        .out_vs(out_vs), .out_hs(out_hs), .out_de(out_de), .out_y(out_y),
        .cop_vs(cop_vs), .cop_hs(cop_hs), .cop_de(cop_de), .cop_y(cop_y)
    );
    always #5 clk = ~clk;

    task axi_write;
        input [6:0]  addr;
        input [31:0] data;
        begin
            @(negedge clk);
            awaddr = addr; awvalid = 1; wdata = data; wstrb = 4'hF; wvalid = 1;
            bready = 1;
            @(posedge clk);
            @(negedge clk);
            awvalid = 0; wvalid = 0;
            @(posedge clk);
            @(negedge clk);
            bready = 0;
        end
    endtask

    task do_line;
        input integer ln;
        begin
            for (c = 0; c < 16; c = c + 1) begin
                in_de = 1; in_rgb = rgb[ln*16+c];
                @(negedge clk);
            end
            in_de = 0; in_rgb = 0;
            repeat (3) @(negedge clk);
            in_hs = 1; @(negedge clk); in_hs = 0;
            @(negedge clk);
        end
    endtask

    task do_frame;
        begin
            @(negedge clk);
            in_vs = 1; @(negedge clk); in_vs = 0; @(negedge clk);
            for (l = 0; l < 8; l = l + 1) do_line(l);
        end
    endtask

    task exp_at;
        input integer f;
        input integer i;
        output [7:0] v;
        begin
            case (f)
                0, 2: v = expA[i];
                1, 3: v = expB[i];    // 帧 4 显示通道 = 高斯（scaler 已改走快照分支）
                4:    v = expC[i];
                5:    v = expE[i];
                default: v = 8'hxx;
            endcase
        end
    endtask

    always @(posedge clk) begin
        cyc = cyc + 1;
        if (rst_n) begin
            if (in_vs) begin in_seen = 0; out_seen = 0; end
            if (in_de && !in_seen) begin in_seen = 1; in_first = cyc; end
            if (out_de && !out_seen) begin
                out_seen = 1;
                lat[fidx] = cyc - in_first;   // 首像素逐级流水延迟（拍）
            end
        end
        if (rst_n && out_de) begin
            exp_at(fidx, fcnt[fidx], expv);
            if (out_y !== expv) begin
                errors = errors + 1;
                $display("FAIL: f%0d disp px[%0d]=%02x exp=%02x", fidx, fcnt[fidx], out_y, expv);
                if (errors > 8) $fatal(1);
            end
            fcnt[fidx] = fcnt[fidx] + 1;
        end
        if (rst_n && cop_de) begin
            if (fidx !== 3) begin
                errors = errors + 1;
                $display("FAIL: cop_de active in frame %0d (scaler disabled)", fidx);
            end else if (cop_y !== expD[fcnt_c]) begin
                errors = errors + 1;
                $display("FAIL: cop px[%0d]=%02x exp=%02x", fcnt_c, cop_y, expD[fcnt_c]);
                if (errors > 8) $fatal(1);
            end
            fcnt_c = fcnt_c + 1;
        end
    end

    initial begin
        clk = 0; rst_n = 0; in_vs = 0; in_hs = 0; in_de = 0; in_rgb = 0;
        awvalid = 0; wvalid = 0; arvalid = 0; bready = 0; rready = 0;
        awaddr = 0; araddr = 0; wdata = 0; wstrb = 0;
        fidx = 0; errors = 0; fcnt_c = 0;
        cyc = 0; in_first = 0; out_first = 0; lat_err = 0;
        in_seen = 0; out_seen = 0;
        fcnt[0] = 0; fcnt[1] = 0; fcnt[2] = 0; fcnt[3] = 0;
        fcnt[4] = 0; fcnt[5] = 0;
        $readmemh("../data/golden/vision/rgb2gray/input_rgb.hex", rgb);
        $readmemh("../data/golden/vision/rgb2gray/expected_y.hex", expA);
        $readmemh("../data/golden/vision/gaussian3x3/expected_y.hex", expB);
        $readmemh("../data/golden/vision/fullchain/expected_fullchain.hex", expD);
        $readmemh("../data/golden/vision/fullchain/expected_gauss_sobel.hex", expC);
        $readmemh("../data/golden/vision/fullchain/expected_gray_sobel.hex", expE);
        repeat (4) @(negedge clk);
        rst_n = 1;

        // 帧 1：gray only
        axi_write(7'h00, 32'h0);
        do_frame;
        repeat (2000) @(negedge clk);
        fidx = 1;
        // 帧 2：gauss（帧内第 4 行后改 R0=0，帧 2 不受影响、帧 3 生效）
        axi_write(7'h00, 32'h1);
        @(negedge clk);
        in_vs = 1; @(negedge clk); in_vs = 0; @(negedge clk);
        for (l = 0; l < 8; l = l + 1) begin
            do_line(l);
            if (l == 3) axi_write(7'h00, 32'h0);
        end
        repeat (2000) @(negedge clk);
        fidx = 2;
        // 帧 3：拓扑已切回 gray
        do_frame;
        repeat (2000) @(negedge clk);
        fidx = 3;
        // 帧 4：gauss + scaler（显示=高斯全分辨率；快照通道出 fullchain 512px）
        axi_write(7'h00, 32'h3);
        do_frame;
        repeat (2600) @(negedge clk);
        if (fcnt_c !== 512) begin
            $display("FAIL: cop collected=%0d (expect 512)", fcnt_c);
            $fatal(1);
        end
        fidx = 4;
        // 帧 5：gauss + sobel（边缘接在高斯后，全分辨率）
        axi_write(7'h00, 32'h9);
        do_frame;
        repeat (2000) @(negedge clk);
        fidx = 5;
        // 帧 6：仅 sobel（bit0=0、bit3=1，对 raw gray 做边缘）
        axi_write(7'h00, 32'h8);
        do_frame;
        repeat (2000) @(negedge clk);

        if (fcnt[0] !== 128 || fcnt[1] !== 128 || fcnt[2] !== 128 || fcnt[3] !== 128
            || fcnt[4] !== 128 || fcnt[5] !== 128 || fcnt_c !== 512 || errors !== 0) begin
            $display("FAIL: disp=%0d/%0d/%0d/%0d/%0d/%0d cop=%0d errors=%0d (expect 128x6/512/0)",
                     fcnt[0], fcnt[1], fcnt[2], fcnt[3], fcnt[4], fcnt[5], fcnt_c, errors);
            $fatal(1);
        end
        // A5 帧首像素延迟模型（实测校正，2026-10-01）：窗口级有 1 行结构滞后
        //   （3×3 窗口需下一行流入才能算当前行，双行缓存设计使然），故
        //   gray = 1；gauss = 行周期+4；gauss+sobel = 2×行周期+7；gray+sobel = 行周期+4。
        //   §3.2 的"每级 3 拍"是稳态标记滞后，与帧首像素滞后是两个口径。
        lat_err = 0;
        for (f = 0; f < 6; f = f + 1) begin
            case (f)
                0, 2: if (lat[f] !== 1) lat_err = 1;
                1, 3: if (lat[f] !== 21 + 4) lat_err = 1;
                4:    if (lat[f] !== 2 * 21 + 7) lat_err = 1;
                5:    if (lat[f] !== 21 + 4) lat_err = 1;
            endcase
        end
        if (lat_err) begin
            $display("FAIL: latency f0..f5 = %0d/%0d/%0d/%0d/%0d/%0d (expect 1/25/1/25/49/25)",
                     lat[0], lat[1], lat[2], lat[3], lat[4], lat[5]);
            $fatal(1);
        end
        $display("PASS: vision_top v0.3 6 frames dual-path, display 768 px + cop 512 px, 0 errors (frame-latch verified)");
        $display("PASS: A5 latency gray=1 gauss=25 gauss+sobel=49 cycles (1-row window lag model match), scaler throughput-based");
        $finish;
    end
endmodule
