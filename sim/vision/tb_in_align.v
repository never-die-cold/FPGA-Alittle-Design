`timescale 1ns/1ps
// in_align 专项 tb：丑陋原始流 → §3.1 流约定归一化
//   帧 A：raw hs 搭在每行最后一个 de 拍上（最坏位置）、宽度 2 拍；raw vs 宽 3 拍位于场消隐
//   帧 B：人为制造 vs/hs 撞拍——raw vs 边沿对准第 3 行 hs 的应发拍，断言 hs 让路顺延一拍且不丢
//   帧 C：恢复正常流（验证撞拍后无残留状态）
// 断言：out_de 逐像素 = 输入图案（de/rgb 直通）；每行 hs 与最后 de 间隔 >=3、与下行首 de 间隔 >=1；
//       vs 单拍、与 hs 不同拍、先于本帧首个 de；计数 3 帧 = 384 px / 24 hs / 3 vs。
module tb_in_align;
    reg clk, rst_n, in_vs, in_hs, in_de;
    reg [23:0] in_rgb;
    wire out_vs, out_hs, out_de;
    wire [23:0] out_rgb;
    integer cyc, px_cnt, hs_cnt, vs_cnt, errors;
    integer last_de, last_hs, frame_first_de;
    integer l, c, k;
    reg hs_seen, vs_active;
    reg [23:0] pat [0:127];

    in_align #(.HS_DLY(3), .VS_POL(1'b1), .HS_POL(1'b1)) dut (
        .clk(clk), .rst_n(rst_n),
        .in_vs(in_vs), .in_hs(in_hs), .in_de(in_de), .in_rgb(in_rgb),
        .out_vs(out_vs), .out_hs(out_hs), .out_de(out_de), .out_rgb(out_rgb)
    );
    always #5 clk = ~clk;

    // ---- 检查器（blocking 计数：cyc = 当前拍序号，从 1 起） ----
    always @(posedge clk) begin
        cyc = cyc + 1;
        if (rst_n) begin
            if (out_vs) begin
                vs_cnt = vs_cnt + 1;
                if (out_hs) begin errors = errors + 1; $display("FAIL: vs/hs same cycle @%0d", cyc); end
                if (vs_active) begin errors = errors + 1; $display("FAIL: vs wider than 1 cycle @%0d", cyc); end
                vs_active = 1;
                hs_seen = 0;
                frame_first_de = 0;
            end else begin
                vs_active = 0;
            end
            if (out_de) begin
                if (out_rgb !== pat[px_cnt % 128]) begin
                    errors = errors + 1;
                    $display("FAIL: rgb px[%0d]=%06x exp=%06x @%0d", px_cnt % 128, out_rgb, pat[px_cnt % 128], cyc);
                end
                if (hs_seen && (cyc - last_hs < 1)) begin
                    errors = errors + 1; $display("FAIL: de only %0d after hs @%0d", cyc - last_hs, cyc);
                end
                if (frame_first_de == 0) begin
                    frame_first_de = cyc;
                    if (vs_cnt == 0) begin
                        errors = errors + 1; $display("FAIL: de before any vs @%0d", cyc);
                    end
                end
                px_cnt = px_cnt + 1;
                last_de = cyc;
            end
            if (out_hs) begin
                hs_cnt = hs_cnt + 1;
                if (cyc - last_de < 3) begin
                    errors = errors + 1; $display("FAIL: hs only %0d after last de @%0d", cyc - last_de, cyc);
                end
                last_hs = cyc; hs_seen = 1;
            end
        end
    end

    // ---- 驱动：一行 = 16 de + 6 消隐；raw hs 搭在行尾 de 上、宽 2 拍 ----
    task do_ugly_line;
        begin
            for (c = 0; c < 16; c = c + 1) begin
                in_de = 1; in_hs = (c == 15);       // hs 搭在最后一个 de 拍
                in_rgb = pat[(l * 16 + c) % 128];
                @(negedge clk);
            end
            in_de = 0; in_rgb = 0;
            in_hs = 1; @(negedge clk);              // hs 第 2 拍（越进行消隐）
            in_hs = 0;
            repeat (5) @(negedge clk);
        end
    endtask

    initial begin
        clk = 0; rst_n = 0; in_vs = 0; in_hs = 0; in_de = 0; in_rgb = 0;
        cyc = 0; px_cnt = 0; hs_cnt = 0; vs_cnt = 0; errors = 0;
        last_de = 0; last_hs = 0; frame_first_de = 0; hs_seen = 0; vs_active = 0;
        $readmemh("../data/golden/vision/rgb2gray/input_rgb.hex", pat);
        repeat (4) @(negedge clk);
        rst_n = 1;

        // 帧 A：正常丑流（vs 在场消隐中段，宽 3 拍）
        repeat (3) @(negedge clk);
        in_vs = 1; @(negedge clk); @(negedge clk); @(negedge clk); in_vs = 0;
        @(negedge clk);
        for (l = 0; l < 8; l = l + 1) do_ugly_line;
        repeat (8) @(negedge clk);

        // 帧 B：vs/hs 撞拍——raw vs 边沿对准第 3 行（l=2）hs 应发拍
        //   时序：l=2 的 de 于本帧起点后 2*22+16=60 拍结束（de_fall），hs 应发在 de_fall+4；
        //   驱动按拍数直接摆放（HS_DLY=3 时 raw vs 需在 hs_wait==1 那拍有效）。
        repeat (3) @(negedge clk);
        in_vs = 1; @(negedge clk); @(negedge clk); @(negedge clk); in_vs = 0;
        @(negedge clk);
        for (l = 0; l < 8; l = l + 1) begin
            if (l != 2) begin
                do_ugly_line;
            end else begin
                for (c = 0; c < 16; c = c + 1) begin
                    in_de = 1; in_hs = (c == 15); in_rgb = pat[(l * 16 + c) % 128];
                    @(negedge clk);
                end
                in_de = 0; in_rgb = 0; in_hs = 1; @(negedge clk); in_hs = 0;
                @(negedge clk);                     // de_fall+1
                in_vs = 1; @(negedge clk);          // de_fall+2：vs 边沿拍（hs_wait 计到 1 的前一拍置位）
                @(negedge clk);                     // de_fall+3
                in_vs = 0; @(negedge clk);          // de_fall+4：撞拍拍，hs 让路
                @(negedge clk);                     // de_fall+5：hs 顺延发射
                @(negedge clk);
            end
        end
        repeat (8) @(negedge clk);

        // 帧 C：恢复验证
        repeat (3) @(negedge clk);
        in_vs = 1; @(negedge clk); @(negedge clk); @(negedge clk); in_vs = 0;
        @(negedge clk);
        for (l = 0; l < 8; l = l + 1) do_ugly_line;
        repeat (8) @(negedge clk);

        // 帧 B 含 2 个 vs（帧首 + 撞拍注入），故总数 = 4；
        // hs=24（8×3）本身即证明撞拍 hs 被顺延而非丢弃（无让路逻辑会少 1 个 hs）
        if (px_cnt !== 384 || hs_cnt !== 24 || vs_cnt !== 4 || errors !== 0) begin
            $display("FAIL: px=%0d hs=%0d vs=%0d errors=%0d (expect 384/24/4/0)",
                     px_cnt, hs_cnt, vs_cnt, errors);
            $fatal(1);
        end
        $display("PASS: in_align 3 frames, 384 px passthrough, 24 hs/4 vs, spacing OK (vs/hs collision deferred)");
        $finish;
    end
endmodule
