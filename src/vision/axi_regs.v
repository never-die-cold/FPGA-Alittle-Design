`timescale 1ns/1ps
// axi_regs —— AXI-Lite 从机参数寄存器堆（模块二，A1 参数化基础）
// 实现口径 v0.1（单元级，10/5 评审后冻结）：
//   * 本模块只在 AXI 域；整组配置 CDC 由 config_bridge 实现；
//   * 无突发（AXI-Lite 固定单拍）；读写各通道序列化：上一事务完成前 ready 拉低，
//     保证响应/读数据不丢（简单正确优先，PS 侧访问频率远低于单像素时钟）；
//   * wstrb 字节使能生效；越界地址：写丢弃、读返回 0，响应均为 OKAY（口径注明）；
//   * 寄存器映射 v0.1（字节地址 = 4*index）：
//       R0  control：bit0 gauss_en / bit1 snapshot_en / bit2 osd_en / bit3 sobel_en
//       R1..R4  box1 x0/y0/x1/y1（低 16 位有效）
//       R5      box1 color[7:0]
//       R6..R9  roi x0/y0/x1/y1
//       R10     roi color[7:0]
//       ATOMIC_CONFIG=1：R11 提交/busy，R12 已应用编号；R13..15 保留。
//       ATOMIC_CONFIG=0：R11..15 保留，兼容独立单元测试。
module axi_regs #(
    parameter NREG = 16,
    parameter AW   = 7,         // 字节地址位宽；须满足 2^AW > NREG*4，留出越界判别空间
    parameter RESV_BASE = 11,
    parameter ATOMIC_CONFIG = 0 // 顶层模式：R11 提交/忙，R12 已应用编号
)(
    input  wire       clk,
    input  wire       rst_n,
    // 写地址通道
    input  wire       awvalid,
    output wire       awready,
    input  wire [AW-1:0] awaddr,
    // 写数据通道
    input  wire       wvalid,
    output wire       wready,
    input  wire [31:0] wdata,
    input  wire [3:0]  wstrb,
    // 写响应
    output reg        bvalid,
    input  wire       bready,
    output wire [1:0] bresp,
    // 读地址通道
    input  wire       arvalid,
    output wire       arready,
    input  wire [AW-1:0] araddr,
    // 读数据通道
    output reg        rvalid,
    input  wire       rready,
    output reg [31:0] rdata,
    output wire [1:0] rresp,
    // 用户视图（扁平展开：regs_flat[i*32 +: 32] = R_i）
    output wire [NREG*32-1:0] regs_flat,
    input wire cfg_busy,
    input wire [31:0] cfg_applied,
    output reg cfg_commit
);
    reg [31:0] mem [0:NREG-1];
    reg aw_hold, w_hold;
    reg [AW-1:0] aw_q;
    reg [31:0] wd_q;
    reg [3:0] strb_q;
    wire       wr_pending = bvalid && !bready;
    wire       rd_pending = rvalid && !rready;

    assign awready = !bvalid && !aw_hold;
    assign wready  = !bvalid && !w_hold;
    reg [1:0] write_response;
    assign bresp = write_response;
    assign rresp   = 2'b00;
    assign arready = !rd_pending;

    wire wr_fire = !bvalid && (aw_hold || (awvalid && awready)) &&
                             (w_hold || (wvalid && wready));
    wire [AW-1:0] write_addr = aw_hold ? aw_q : awaddr;
    wire [31:0] write_data = w_hold ? wd_q : wdata;
    wire [3:0] write_strb = w_hold ? strb_q : wstrb;
    wire [AW-3:0] widx = write_addr[AW-1:2];
    wire        w_hit   = (widx < NREG) && (widx < RESV_BASE);   // 保留区写忽略
    wire commit_write = ATOMIC_CONFIG && widx==11 && write_strb[0] && write_data[0];

    integer bi, ri;
    // 复位全零：control 默认全关（安全旁路），参数寄存器未写时为 0 而非 X，
    // 防止未初始化值经 osd/scaler 参数路径传播
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            bvalid <= 0;
            cfg_commit <= 0; write_response <= 0;
            aw_hold <= 0; w_hold <= 0; aw_q <= 0; wd_q <= 0; strb_q <= 0;
            for (ri = 0; ri < NREG; ri = ri + 1) mem[ri] <= 32'h0;
        end else begin
            cfg_commit <= 0;
            if (awvalid && awready) begin aw_hold <= 1; aw_q <= awaddr; end
            if (wvalid && wready) begin w_hold <= 1; wd_q <= wdata; strb_q <= wstrb; end
            if (wr_fire) begin
                bvalid <= 1; aw_hold <= 0; w_hold <= 0;
                write_response <= commit_write && cfg_busy ? 2'b10 : 2'b00;
                if(commit_write && !cfg_busy) cfg_commit <= 1;
                if (w_hit)
                    for (bi = 0; bi < 4; bi = bi + 1)
                        if (write_strb[bi]) mem[widx][bi*8 +: 8] <= write_data[bi*8 +: 8];
            end else if (bready) bvalid <= 0;
        end
    end

    reg [AW-3:0] ridx_q;
    wire         rd_fire = arvalid && arready;
    wire         r_hit   = (ridx_q < NREG) && (ridx_q >= RESV_BASE) ? 1'b0
                                                                  : (ridx_q < NREG);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rvalid <= 0; ridx_q <= 0; rdata <= 0;
        end else begin
            if (rd_fire) begin
                ridx_q <= araddr[AW-1:2];
                rvalid <= 1;
                // 保留区读 0；越界读 0
                rdata  <= ((araddr[AW-1:2] < NREG) && (araddr[AW-1:2] >= RESV_BASE))
                          ? 32'h0
                          : ((araddr[AW-1:2] < NREG) ? mem[araddr[AW-1:2]] : 32'h0);
                if(ATOMIC_CONFIG && araddr[AW-1:2]==11) rdata <= {31'b0,cfg_busy};
                if(ATOMIC_CONFIG && araddr[AW-1:2]==12) rdata <= cfg_applied;
            end else if (rready) begin
                rvalid <= 0;
                rdata  <= 32'h0;
            end
        end
    end

    genvar g;
    generate
        for (g = 0; g < NREG; g = g + 1) begin : gen_flat
            assign regs_flat[g*32 +: 32] = mem[g];
        end
    endgenerate
endmodule
