`timescale 1ns/1ps
// cop_buf —— 快照帧乒乓缓冲（模块二→模块三衔接，design_v0.md §7）
// 职责：scaler 快照流（DW×DH 帧）写入双帧 BRAM 乒乓；读侧以 1 像素/拍重放为
//       vs/hs/de 灰度流交 cop_top——**接口占位**：cop_ready 反压控制整帧启动，
//       契约定稿后按 §7 回写（valid/de vs AXI-Stream 仅改封装不改存储）。
// 写侧：in_de 写 {行,列}；in_hs 提交行，末行提交 = 帧完成（frame_done 脉冲 +
//       buf_valid 置位），写缓冲翻转。
// 读侧：优先非写银行的完整帧，否则选空闲写银行的完整帧；整帧原子启动，启动后
//       一帧发完不中断）；帧间距满足行尾 hs 间隔（de→hs 4 拍、hs→de 1 拍）。
// 覆盖保护：正在回放或本拍开始回放的银行都禁止成为写银行。
// 新帧覆盖待消费帧时 drop_count++；回放携带对应银行的帧号/配置号。
// 复位后必须先有完整帧首，半帧不写入也不发布。
// BRAM 结构（Vivado 推断要求，2026-10-01 顶层 OOC 实测教训）：每个阵列独立
//       always 块、1 写口 + 1 读口、读写地址寄存、读数据输出寄存——mux 阵列写
//       （if wr_sel mem1 else mem0）会推断失败（Synth 8-3391）。读缓冲恒 ≠ 写
//       缓冲（覆盖保护不变式），同拍读写无冲突，不需 read-during-write 语义。
module cop_buf #(
    parameter DW = 8,             // 帧宽（= scaler 输出宽）
    parameter DH = 4,             // 帧高
    parameter AWX = $clog2(DW),
    parameter AWY = $clog2(DH)
)(
    input  wire       clk,
    input  wire       rst_n,
    // scaler 快照流（同 pclk 域；M3 跨域时在写口前加异步 FIFO，本模块不动）
    input  wire       in_vs,
    input  wire       in_hs,
    input  wire       in_de,
    input  wire [7:0] in_y,
    // cop 消费侧
    input  wire       cop_ready,   // =1 允许启动下一帧回放（帧内不中断）
    output reg        out_vs,      // 帧首单拍
    output reg        out_hs,      // 行尾单拍（末 de 后 4 拍）
    output reg        out_de,
    output reg  [7:0] out_y,
    output reg        frame_done,  // 一帧写完（单拍）——M3 可作中断源
    output wire       buf_full,
    input wire [31:0] in_frame_id,in_config_id,
    output reg [31:0] out_frame_id,out_config_id,drop_count
);
    localparam FRAME_PX = DW * DH;

    reg [7:0] mem0 [0:FRAME_PX-1];
    reg [7:0] mem1 [0:FRAME_PX-1];

    // ---- 写侧 ----
    reg                   wr_sel;
    reg [AWY-1:0]         wr_row;
    reg [AWX-1:0]         wr_col;
    reg [1:0]             buf_valid;
    reg                   writing;
    reg [31:0] bank_frame[0:1],bank_config[0:1];
    wire [AWX+AWY-1:0]    wr_addr = wr_row * DW + wr_col;
    wire                  we0 = rst_n && writing && in_de && !wr_sel;
    wire                  we1 = rst_n && writing && in_de &&  wr_sel;

    // ---- 读侧（回放引擎） ----
    reg                   replay;
    reg                   rd_buf;
    reg [AWX+AWY-1:0]     raddr;
    reg [2:0]             hgap;
    reg                   finishing;   // 末像素已发，走完最后一个行尾 hs 再收
    reg [7:0]             rd0, rd1;    // 两阵列同址读，输出寄存（BRAM 推断要求）
    reg                   vs_int, de_int, hs_int;  // 决策级（滞后一拍与 rd 对齐）
    assign buf_full = (buf_valid == 2'b11) && !replay;
    wire choose_rd = buf_valid[~wr_sel] ? ~wr_sel : wr_sel;
    wire start_replay = !replay && cop_ready && buf_valid[choose_rd] &&
                       !((writing || in_vs) && choose_rd == wr_sel);

    // 阵列 0/1：独立 1W1R 块（写使能互斥；读缓冲恒 ≠ 写缓冲，无同口冲突）
    always @(posedge clk) begin
        if (we0) mem0[wr_addr] <= in_y;
        rd0 <= mem0[raddr];
    end
    always @(posedge clk) begin
        if (we1) mem1[wr_addr] <= in_y;
        rd1 <= mem1[raddr];
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            wr_sel <= 0; wr_row <= 0; wr_col <= 0; buf_valid <= 0;
            writing <= 0;
            bank_frame[0]<=0;bank_frame[1]<=0;bank_config[0]<=0;bank_config[1]<=0;
            out_frame_id<=0;out_config_id<=0;drop_count<=0;
            replay <= 0; rd_buf <= 0; raddr <= 0; hgap <= 0; finishing <= 0;
            vs_int <= 0; de_int <= 0; hs_int <= 0;
            out_vs <= 0; out_hs <= 0; out_de <= 0; frame_done <= 0;
        end else begin
            frame_done <= 0;
            vs_int <= 0;

            // ---- 写侧：流计数 + 帧提交 ----
            if (in_vs) begin
                wr_row <= 0; wr_col <= 0;
                writing <= 1;
                bank_frame[wr_sel]<=in_frame_id;bank_config[wr_sel]<=in_config_id;
                if(buf_valid[wr_sel]) drop_count<=drop_count+1;
                buf_valid[wr_sel] <= 0; // 覆写待消费帧前撤销有效位，半帧不得回放
            end else if (in_de) begin
                wr_col <= wr_col + 1;
            end
            if (in_hs && writing) begin
                if (wr_row == DH-1) begin
                    buf_valid[wr_sel] <= 1;
                    frame_done <= 1;
                    writing <= 0;
                    // 翻转写缓冲；读忙且目标=读缓冲时原地覆写（保读安全，丢帧）
                    if (!((replay && rd_buf == ~wr_sel) ||
                          (start_replay && choose_rd == ~wr_sel))) wr_sel <= ~wr_sel;
                    wr_row <= 0;
                end else begin
                    wr_row <= wr_row + 1;
                end
                wr_col <= 0;
            end

            // ---- 读侧决策：rd0/rd1 滞后 raddr 一拍，标记经 *_int 再滞后一拍对齐 ----
            if (!replay) begin
                de_int <= 0; hs_int <= 0;
                if (start_replay) begin
                    replay <= 1; rd_buf <= choose_rd;
                    out_frame_id<=bank_frame[choose_rd];out_config_id<=bank_config[choose_rd];
                    buf_valid[choose_rd] <= 0;
                    if (choose_rd == wr_sel) wr_sel <= ~wr_sel;
                    raddr <= 0; hgap <= 0;
                    vs_int <= 1;                 // 帧首脉冲，首个 de 晚两拍
                end
            end else if (hgap == 0) begin
                de_int <= 1; hs_int <= 0;
                if ((raddr % DW) == DW-1) begin
                    hgap <= 4;                   // 行尾空白：de→hs 3 拍、hs→de 1 拍
                    if (raddr == FRAME_PX-1)
                        finishing <= 1;          // 末像素兼行尾：hs 走完再收
                end
                raddr <= raddr + 1;
            end else begin
                de_int <= 0;
                hgap <= hgap - 1;
                hs_int <= (hgap == 2);           // 决策滞后一拍后仍在末 de 后 3 拍
                if (finishing && hgap == 1) begin
                    replay <= 0;
                    finishing <= 0;
                end
            end

            // ---- 输出寄存（与 rd 数据同拍） ----
            out_vs <= vs_int;
            out_hs <= hs_int;
            out_de <= de_int;
            out_y  <= rd_buf ? rd1 : rd0;
        end
    end
endmodule
