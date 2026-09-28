`timescale 1ns/1ps
// scaler —— 双线性缩放（模块二）
// 契约（与 data/golden/vision/scaler/gen_scaler.py 逐位一致）：
//   x_src(d) = (2d+1)*SW/(2*DW) - 0.5，clamp 到 [0,SW-1]；y 同。
//   x0=floor(clamp)，x1=min(x0+1,SW-1)，fx/fy 取 16.16 小数高 8 位；
//   out = lerp8(lerp8(P00,P01,fx), lerp8(P10,P11,fx), fy)。
// 实现口径 v0.1（单元级，10/5 评审后冻结）：
//   * NLINES 个行槽（2 的幂）滑动缓存源行，写侧按行号取模入槽；
//     行步进 SH/DH <= NLINES-2 时读槽不被写覆盖（tb 断言，RTL 不含检查）；
//   * 2 拍/像素：ph0 读 x0 列、ph1 读 x1 列（两槽同址），下一 ph0 末出数；
//     吞吐 = 1 像素/2 拍——缩小档吞吐充足，放大档受帧预算约束（design_v0.md §3.1）；
//   * 读地址由坐标累加器组合产生（x1_of 函数），行切换无滞后读；
//   * 发射与源写入解耦：行尾若下一行源未就绪则挂起，hs 提交后续发。
module scaler #(
    parameter SW = 16,            // 源宽
    parameter SH = 8,             // 源高
    parameter DW = 32,            // 目标宽
    parameter DH = 16,            // 目标高
    parameter NLINES = 16,        // 行槽数（2 的幂，>= 4）
    parameter AW  = $clog2(SW),
    parameter AWY = $clog2(NLINES),
    parameter RW  = $clog2(SH+1),
    parameter FR  = 16,           // 坐标定点小数位
    parameter FXH = 8             // 插值小数位
)(
    input  wire       clk,
    input  wire       rst_n,
    input  wire       in_vs,
    input  wire       in_hs,
    input  wire       in_de,
    input  wire [7:0] in_y,
    output reg        out_de,
    output reg  [7:0] out_y
);
    localparam STEP_X = (SW * (1 << FR)) / DW;
    localparam INIT_X = ((SW - DW) * (1 << (FR-1))) / DW;   // Verilog 整除向零截断，golden 同
    localparam STEP_Y = (SH * (1 << FR)) / DH;
    localparam INIT_Y = ((SH - DH) * (1 << (FR-1))) / DH;

    // ---- 写侧：源行滑槽 ----
    reg [AW-1:0] wx;
    reg [RW-1:0] w_row;
    wire [AWY-1:0] w_slot = w_row[AWY-1:0];

    // ---- 发射状态 ----
    reg                   emitting;
    reg                   ph;          // 0: 读 x0 列; 1: 读 x1 列
    reg [31:0]            xd;          // 输出列
    reg [31:0]            out_row;     // 输出行
    reg signed [31:0]     x_acc, y_acc;
    reg [FXH-1:0]         fx8_r, fy8_r;
    reg [AWY-1:0]         y0_slot, y1_slot;
    reg [7:0]             p00r, p10r;
    reg                   data_ready;
    // 行坐标跨像素流水：末像素的插值发生在行尾后一拍，行坐标先装 pending、
    // 末像素算完（下一 ph0 末）再提交，避免末像素用错下一行的 fy/槽
    reg                   pend_valid, last_pending;
    reg [AWY-1:0]         pend_y0, pend_y1;
    reg [FXH-1:0]         pend_fy;

    // 像素坐标（组合，ph0/ph1 期间 x_acc 均为当前像素；先于行槽例化声明）
    wire signed [31:0] xs_shift = x_acc >>> FR;
    wire [AW-1:0] xs_c  = (x_acc < 0) ? 0 :
                          (xs_shift > SW-1) ? (SW-1) : xs_shift[AW-1:0];
    wire [AW-1:0] xs_x1 = (xs_c == SW-1) ? xs_c : (xs_c + 1);
    wire [FXH-1:0] xs_f = (x_acc < 0) ? 0 : x_acc[FR-1 -: FXH];
    wire [AW-1:0] rd_addr = ph ? xs_x1 : xs_c;

    wire [7:0] slot_rd [0:NLINES-1];
    genvar g;
    generate
        for (g = 0; g < NLINES; g = g + 1) begin : gen_slot
            line_buffer #(.WIDTH(SW), .DW(8)) lb (
                .clk(clk),
                .we(in_de && (w_slot == g)),
                .waddr(wx),
                .wdata(in_y),
                .raddr(rd_addr),
                .rdata(slot_rd[g])
            );
        end
    endgenerate

    // 槽选择：两输出行各自所在槽的当前读数（组合）
    reg [7:0] p_row0, p_row1;
    integer jj;
    always @* begin
        p_row0 = 8'h00; p_row1 = 8'h00;
        for (jj = 0; jj < NLINES; jj = jj + 1) begin
            if (jj == y0_slot) p_row0 = slot_rd[jj];
            if (jj == y1_slot) p_row1 = slot_rd[jj];
        end
    end

    // ---- 写侧时序 ----
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            wx <= 0; w_row <= 0;
        end else begin
            if (in_vs || in_hs) wx <= 0;
            else if (in_de)     wx <= wx + 1;
            if (in_vs)                          w_row <= 0;
            else if (in_hs && (w_row < SH-1))   w_row <= w_row + 1;
        end
    end

    // ---- 行坐标 ----
    // 已完成写入的行数（寄存 sticky）：hs 提交当前行；vblank 期间保持，供末行发射判据
    reg [RW-1:0] committed;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)     committed <= 0;
        else if (in_hs) committed <= w_row + 1;
    end
    wire row_end   = emitting && ph && (xd == DW-1);
    wire more_rows = (out_row < DH-1);
    wire signed [31:0] cont_acc   = y_acc + STEP_Y;              // 行尾续发的下一行
    wire signed [31:0] pend_acc   = y_acc;                       // 空闲挂起的待发行
    wire signed [31:0] idle_acc   = y_acc;                       // 空闲触发用
    wire signed [31:0] idle_shift = idle_acc >>> FR;
    wire signed [31:0] cont_shift = cont_acc >>> FR;
    wire [RW-1:0] idle_y0 = (idle_acc < 0) ? 0 :
                            (idle_shift > SH-1) ? (SH-1) : idle_shift[RW-1:0];
    wire [RW-1:0] cont_y0 = (cont_acc < 0) ? 0 :
                            (cont_shift > SH-1) ? (SH-1) : cont_shift[RW-1:0];
    wire [RW-1:0] idle_y1 = (idle_y0 == SH-1) ? idle_y0 : (idle_y0 + 1);
    wire [RW-1:0] cont_y1 = (cont_y0 == SH-1) ? cont_y0 : (cont_y0 + 1);
    wire [FXH-1:0] idle_fy = (idle_acc < 0) ? 0 : idle_acc[FR-1 -: FXH];
    wire [FXH-1:0] cont_fy = (cont_acc < 0) ? 0 : cont_acc[FR-1 -: FXH];
    wire idle_ready  = (idle_y1 < committed);   // 就绪行号 0..committed-1，y1 须落在其中
    wire cont_ready  = (cont_y1 < committed);
    wire start_idle  = !emitting && !in_vs && idle_ready && (out_row < DH);
    wire start_cont  = row_end && more_rows && cont_ready;

    // 两级 8bit lerp：ph0 末用捕获的 x0 列与当前 x1 列(rdata) 插值
    wire [15:0] top = (256 - fx8_r) * p00r + fx8_r * p_row0;
    wire [15:0] bot = (256 - fx8_r) * p10r + fx8_r * p_row1;
    wire [15:0] val = (256 - fy8_r) * top[15:8] + fy8_r * bot[15:8];

    // 行坐标装载（两处调用）
    task load_row;
        input [RW-1:0] y0, y1;
        input [FXH-1:0] fy;
        begin
            y0_slot <= y0[AWY-1:0];
            y1_slot <= y1[AWY-1:0];
            fy8_r   <= fy;
        end
    endtask

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            emitting <= 0; ph <= 0; xd <= 0; out_row <= 0;
            x_acc <= 0; y_acc <= INIT_Y;
            fx8_r <= 0; fy8_r <= 0;
            y0_slot <= 0; y1_slot <= 0;
            p00r <= 0; p10r <= 0; data_ready <= 0;
            pend_valid <= 0; last_pending <= 0;
            pend_y0 <= 0; pend_y1 <= 0; pend_fy <= 0;
            out_de <= 0; out_y <= 0;
        end else begin
            out_de <= 0;   // 单拍脉冲默认

            if (start_idle) begin
                emitting <= 1;
                ph       <= 0;
                xd       <= 0;
                x_acc    <= INIT_X;        // 新行从第 0 列坐标开始
                load_row(idle_y0, idle_y1, idle_fy);
            end else if (emitting) begin
                if (!ph) begin
                    fx8_r <= xs_f;
                    if (data_ready) begin
                        out_y      <= val[15:8];
                        out_de     <= 1;
                        data_ready <= 0;
                    end
                    if (pend_valid) begin
                        // 末像素已算完，提交下一行坐标
                        y0_slot   <= pend_y0;
                        y1_slot   <= pend_y1;
                        fy8_r     <= pend_fy;
                        pend_valid <= 0;
                    end
                    if (last_pending) begin
                        emitting    <= 0;
                        last_pending <= 0;
                    end
                    ph <= 1;
                end else begin
                    p00r       <= p_row0;
                    p10r       <= p_row1;
                    data_ready <= 1;
                    ph         <= 0;
                    if (row_end) begin
                        xd    <= 0;
                        x_acc <= INIT_X;
                        y_acc <= cont_acc;
                        out_row <= out_row + 1;   // 无条件推进（末行后 = DH，封死空闲重触发）
                        pend_y0 <= cont_y0;
                        pend_y1 <= cont_y1;
                        pend_fy <= cont_fy;
                        pend_valid <= 1;
                        if (!more_rows || !cont_ready) last_pending <= 1;
                    end else begin
                        xd    <= xd + 1;
                        x_acc <= x_acc + STEP_X;
                    end
                end
            end
        end
    end
endmodule
