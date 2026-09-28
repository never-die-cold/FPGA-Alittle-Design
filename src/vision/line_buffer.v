`timescale 1ns/1ps
// line_buffer —— 单行 BRAM 行缓存（模块二窗口类滤波共用）
// 语义：同步读（raddr 采样后下一拍 rdata 有效）；同地址先读后写（同拍读写返回旧值），
//       gaussian 依赖该语义从"正在被写入的行"读到上一轮内容。
// 深度 = WIDTH；读写地址由上层窗口控制器产生，本模块不含位置计数。
module line_buffer #(
    parameter WIDTH = 16,
    parameter DW    = 8,
    parameter AW    = $clog2(WIDTH)
)(
    input  wire         clk,
    input  wire         we,
    input  wire [AW-1:0] waddr,
    input  wire [DW-1:0] wdata,
    input  wire [AW-1:0] raddr,
    output reg  [DW-1:0] rdata
);
    reg [DW-1:0] mem [0:WIDTH-1];
    always @(posedge clk) begin
        if (we) mem[waddr] <= wdata;
        rdata <= mem[raddr];
    end
endmodule
