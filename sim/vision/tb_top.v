`timescale 1ns/1ps
// vision_top 专项 tb：四帧拓扑序列 + 帧内改 R0 锁存验证
//   帧 1：R0=0（gray only）          → 对拍 gray golden（128px）
//   帧 2：R0=gauss_en                → 对拍 gaussian golden（128px）；
//         第 4 行后帧内写 R0=0       → 帧 2 输出不变（拓扑帧锁存）
//   帧 3：拓扑=gray（帧 2 所写生效）  → 对拍 gray golden（128px）
//   帧 4：R0=gauss|scaler（osd 关）   → 对拍 fullchain golden（512px）
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
    integer fidx, f, l, c, errors;
    integer fcnt [0:3];
    reg [7:0] expv;
    reg [23:0] rgb      [0:127];
    reg [7:0]  expA     [0:127];   // gray golden
    reg [7:0]  expB     [0:127];   // gaussian golden
    reg [7:0]  expD     [0:511];   // fullchain golden

    vision_top #(.SW(16), .SH(8), .DW(32), .DH(16), .NLINES(16)) dut (
        .clk(clk), .rst_n(rst_n),
        .in_vs(in_vs), .in_hs(in_hs), .in_de(in_de), .in_rgb(in_rgb),
        .awvalid(awvalid), .awready(awready), .awaddr(awaddr),
        .wvalid(wvalid), .wready(wready), .wdata(wdata), .wstrb(wstrb),
        .bvalid(bvalid), .bready(bready), .bresp(bresp),
        .arvalid(arvalid), .arready(arready), .araddr(araddr),
        .rvalid(rvalid), .rready(rready), .rdata(rdata), .rresp(rresp),
        .out_vs(out_vs), .out_hs(out_hs), .out_de(out_de), .out_y(out_y)
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
                1:    v = expB[i];
                3:    v = expD[i];
                default: v = 8'hxx;
            endcase
        end
    endtask

    always @(posedge clk) begin
        if (rst_n && out_de) begin
            exp_at(fidx, fcnt[fidx], expv);
            if (out_y !== expv) begin
                errors = errors + 1;
                $display("FAIL: f%0d px[%0d]=%02x exp=%02x", fidx, fcnt[fidx], out_y, expv);
                if (errors > 8) $fatal(1);
            end
            fcnt[fidx] = fcnt[fidx] + 1;
        end
    end

    initial begin
        clk = 0; rst_n = 0; in_vs = 0; in_hs = 0; in_de = 0; in_rgb = 0;
        awvalid = 0; wvalid = 0; arvalid = 0; bready = 0; rready = 0;
        awaddr = 0; araddr = 0; wdata = 0; wstrb = 0;
        fidx = 0; errors = 0;
        fcnt[0] = 0; fcnt[1] = 0; fcnt[2] = 0; fcnt[3] = 0;
        $readmemh("../data/golden/vision/rgb2gray/input_rgb.hex", rgb);
        $readmemh("../data/golden/vision/rgb2gray/expected_y.hex", expA);
        $readmemh("../data/golden/vision/gaussian3x3/expected_y.hex", expB);
        $readmemh("../data/golden/vision/fullchain/expected_fullchain.hex", expD);
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
        // 帧 4：gauss + scaler（osd 关）
        axi_write(7'h00, 32'h3);
        do_frame;
        repeat (2600) @(negedge clk);

        if (fcnt[0] !== 128 || fcnt[1] !== 128 || fcnt[2] !== 128 || fcnt[3] !== 512 || errors !== 0) begin
            $display("FAIL: fcnt=%0d/%0d/%0d/%0d errors=%0d (expect 128/128/128/512/0)",
                     fcnt[0], fcnt[1], fcnt[2], fcnt[3], errors);
            $fatal(1);
        end
        $display("PASS: vision_top 4 frames gray/gauss/gray/full, 896 px, 0 errors (frame-latch verified)");
        $finish;
    end
endmodule
