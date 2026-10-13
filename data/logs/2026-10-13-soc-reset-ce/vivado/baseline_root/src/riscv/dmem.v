// dmem.v —— 8192×32 数据存储器：异步读、同步字节写
// 接口与时序见 src/riscv/design_v0.md §3.2；INIT_FILE 双口预载见 §5.8
module dmem #(
    parameter INIT_FILE = ""            // 非空时按 §8 格式预载；空 = 上电全 0
) (
    input  wire        clk,
    input  wire        we,
    input  wire [3:0]  be,
    input  wire [31:0] addr,
    input  wire [31:0] wdata,
    output wire [31:0] rdata
);

    (* ram_style = "distributed" *) reg [31:0] mem [0:8191];
    integer i;

    initial begin
        for (i = 0; i < 8192; i = i + 1)
            mem[i] = 32'h0000_0000;
        if (INIT_FILE != "")
            $readmemh(INIT_FILE, mem);
    end

    assign rdata = mem[addr[14:2]];

    always @(posedge clk) begin
        if (we) begin
            if (be[0]) mem[addr[14:2]][7:0]   <= wdata[7:0];
            if (be[1]) mem[addr[14:2]][15:8]  <= wdata[15:8];
            if (be[2]) mem[addr[14:2]][23:16] <= wdata[23:16];
            if (be[3]) mem[addr[14:2]][31:24] <= wdata[31:24];
        end
    end

endmodule
