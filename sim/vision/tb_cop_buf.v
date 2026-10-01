`timescale 1ns/1ps
// cop_buf 专项 tb：3 帧乒乓 + ready 反压 + 读时并发写
// 源流 = scaler_ds 黄金期望帧（8x4，32 px）连喂 3 帧（帧间隔拉大保证确定性）：
//   断言：回放流逐像素 = golden × 3 帧；vs/hs 计数 3/12；frame_done 3 次；
//         cop_ready=0 期间回放不启动，置 1 后恢复；全程 0 错误。
module tb_cop_buf;
    reg clk, rst_n, in_vs, in_hs, in_de, cop_ready;
    reg [7:0] in_y;
    wire out_vs, out_hs, out_de, frame_done, buf_full;
    wire [7:0] out_y;
    integer checked, errors, vs_cnt, hs_cnt, done_cnt, l, c, f;
    reg [7:0] exp [0:31];

    cop_buf #(.DW(8), .DH(4)) dut (
        .clk(clk), .rst_n(rst_n),
        .in_vs(in_vs), .in_hs(in_hs), .in_de(in_de), .in_y(in_y),
        .cop_ready(cop_ready),
        .out_vs(out_vs), .out_hs(out_hs), .out_de(out_de), .out_y(out_y),
        .frame_done(frame_done), .buf_full(buf_full)
    );
    always #5 clk = ~clk;

    always @(posedge clk) begin
        if (rst_n) begin
            if (out_vs) vs_cnt = vs_cnt + 1;
            if (out_hs) hs_cnt = hs_cnt + 1;
            if (frame_done) done_cnt = done_cnt + 1;
            if (out_de) begin
                if (out_y !== exp[checked % 32]) begin
                    errors = errors + 1;
                    $display("FAIL: cop[%0d]=%02x exp=%02x", checked % 32, out_y, exp[checked % 32]);
                    if (errors > 8) $fatal(1);
                end
                checked = checked + 1;
            end
        end
    end

    task feed_frame;
        begin
            @(negedge clk);
            in_vs = 1; @(negedge clk); in_vs = 0; @(negedge clk);
            for (l = 0; l < 4; l = l + 1) begin
                for (c = 0; c < 8; c = c + 1) begin
                    in_de = 1; in_y = exp[l*8+c];
                    @(negedge clk);
                end
                in_de = 0; in_y = 0;
                repeat (8) @(negedge clk);      // 帧间隔拉大 > 回放耗时（确定性）
                in_hs = 1; @(negedge clk); in_hs = 0;
                @(negedge clk);
            end
            repeat (20) @(negedge clk);
        end
    endtask

    initial begin
        clk = 0; rst_n = 0; in_vs = 0; in_hs = 0; in_de = 0; in_y = 0;
        cop_ready = 0;
        checked = 0; errors = 0; vs_cnt = 0; hs_cnt = 0; done_cnt = 0;
        $readmemh("../data/golden/vision/scaler_ds/expected_y.hex", exp);
        repeat (4) @(negedge clk);
        rst_n = 1;

        // 帧 1：先喂，cop_ready=0——写完成但回放不得启动
        feed_frame;
        repeat (50) @(negedge clk);
        if (checked !== 0) begin
            $display("FAIL: replay started with cop_ready=0 (%0d px)", checked);
            $fatal(1);
        end
        if (done_cnt !== 1) begin
            $display("FAIL: frame_done=%0d (expect 1)", done_cnt);
            $fatal(1);
        end
        // 帧 2 写入期间开闸——帧 1 回放（与写并发）
        cop_ready = 1;
        feed_frame;
        // 帧 3 常规乒乓
        feed_frame;
        repeat (200) @(negedge clk);

        if (checked !== 96 || errors !== 0 || vs_cnt !== 3 || hs_cnt !== 12 || done_cnt !== 3) begin
            $display("FAIL: px=%0d vs=%0d hs=%0d done=%0d errors=%0d (expect 96/3/12/3/0)",
                     checked, vs_cnt, hs_cnt, done_cnt, errors);
            $fatal(1);
        end
        $display("PASS: cop_buf 3 frames ping-pong, 96 px replay = golden, ready-gate + concurrent write verified");
        $finish;
    end
endmodule
