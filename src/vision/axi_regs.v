`timescale 1ns/1ps
// axi_regs —— AXI-Lite 从机参数寄存器堆（模块二，A1 参数化基础）
// 实现口径 v0.1（单元级，10/5 评审后冻结）：
//   * 单时钟域（单元级 axi 时钟 = 像素时钟；真实 PS↔PL 跨时钟由 vision_top 评审定，
//     预计 2FF 同步器 + 寄存器快照，不在本单元内）；
//   * 无突发（AXI-Lite 固定单拍）；读写各通道序列化：上一事务完成前 ready 拉低，
//     保证响应/读数据不丢（简单正确优先，PS 侧访问频率远低于单像素时钟）；
//   * wstrb 字节使能生效；越界地址：写丢弃、读返回 0，响应均为 OKAY（口径注明）；
//   * 寄存器映射 v0.1（字节地址 = 4*index）：
//       R0  control：bit0 gray_en / bit1 gauss_en / bit2 scaler_en / bit3 sobel_en
//       R1..R4  box1 x0/y0/x1/y1（低 16 位有效）
//       R5      box1 color[7:0]
//       R6..R9  roi x0/y0/x1/y1
//       R10     roi color[7:0]
//       R11..R15 保留（读 0，写忽略）
module axi_regs #(
    parameter NREG = 16,
    parameter AW   = 7,         // 字节地址位宽；须满足 2^AW > NREG*4，留出越界判别空间
    parameter RESV_BASE = 11    // R11..R15 保留：写忽略、读 0
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
    output wire [NREG*32-1:0] regs_flat
);
    reg [31:0] mem [0:NREG-1];
    wire       wr_pending = bvalid && !bready;
    wire       rd_pending = rvalid && !rready;

    assign awready = !wr_pending;
    assign wready  = !wr_pending;
    assign bresp   = 2'b00;                 // OKAY（越界/保留写也 OKAY，见头注释口径）
    assign rresp   = 2'b00;
    assign arready = !rd_pending;

    wire        wr_fire = awvalid && awready && wvalid && wready;
    wire [AW-3:0] widx  = awaddr[AW-1:2];
    wire        w_hit   = (widx < NREG) && (widx < RESV_BASE);   // 保留区写忽略

    integer bi, ri;
    // 复位全零：control 默认全关（安全旁路），参数寄存器未写时为 0 而非 X，
    // 防止未初始化值经 osd/scaler 参数路径传播
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (ri = 0; ri < NREG; ri = ri + 1) mem[ri] <= 32'h0;
        end
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            bvalid <= 0;
        end else if (wr_fire) begin
            bvalid <= 1;
            if (w_hit)
                for (bi = 0; bi < 4; bi = bi + 1)
                    if (wstrb[bi]) mem[widx][bi*8 +: 8] <= wdata[bi*8 +: 8];
        end else if (bready) begin
            bvalid <= 0;
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
