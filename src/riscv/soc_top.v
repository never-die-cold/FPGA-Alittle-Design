// soc_top.v —— PL 侧 SoC 顶层外壳：核 + 指令 BRAM + 数据 RAM + LED 驱动
// 接口与上板冒烟契约见 src/riscv/design_v0.md §5.8
module soc_top #(
    parameter IMEM_INIT_FILE = "src/riscv_fw/hello_v0.hex"
) (
    input  wire       clk,
    input  wire       rst_n,
    output wire [3:0] led
);

    wire [31:0] imem_addr;
    wire [31:0] imem_rdata;
    wire [31:0] dmem_addr;
    wire [31:0] dmem_wdata;
    wire [31:0] dmem_rdata;
    wire [3:0]  dmem_be;
    wire        dmem_we;
    reg  [3:0]  led_q;

    assign led = led_q;

    core_top u_core (
        .clk(clk), .rst_n(rst_n),
        .imem_addr(imem_addr), .imem_rdata(imem_rdata),
        .dmem_addr(dmem_addr), .dmem_wdata(dmem_wdata),
        .dmem_be(dmem_be), .dmem_we(dmem_we), .dmem_rdata(dmem_rdata)
    );

    imem #(.INIT_FILE(IMEM_INIT_FILE)) u_imem (
        .clk(clk), .addr(imem_addr), .rdata(imem_rdata)
    );

    dmem u_dmem (
        .clk(clk), .we(dmem_we), .be(dmem_be),
        .addr(dmem_addr), .wdata(dmem_wdata), .rdata(dmem_rdata)
    );

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            led_q <= 4'b0000;
        else if (dmem_we && (dmem_addr == 32'h8000_3FF0))
            led_q <= dmem_wdata[3:0];
    end

endmodule
