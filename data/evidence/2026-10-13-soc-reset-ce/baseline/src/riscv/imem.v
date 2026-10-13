// imem.v —— 8192×32 指令存储器：hex 预载、同步读
// 接口与时序见 src/riscv/design_v0.md §3.1
module imem #(
    parameter INIT_FILE = "src/riscv_fw/hello.hex"
) (
    input  wire        clk,
    input  wire [31:0] addr,
    output reg  [31:0] rdata
);

    localparam [31:0] NOP = 32'h0000_0013;
    (* ram_style = "block" *) reg [31:0] mem [0:8191];
    integer i;

    initial begin
        rdata = NOP;
        for (i = 0; i < 8192; i = i + 1)
            mem[i] = NOP;
        $readmemh(INIT_FILE, mem);
    end

    always @(posedge clk)
        rdata <= mem[addr[14:2]];

endmodule
