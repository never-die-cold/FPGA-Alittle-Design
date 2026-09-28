// soc_top.v —— PL 侧 SoC 顶层外壳：核 + 指令 BRAM + 数据 RAM + 计时计数器 + LED 驱动
// 接口与上板冒烟契约见 src/riscv/design_v0.md §5.8
module soc_top #(
    parameter IMEM_INIT_FILE = "src/riscv_fw/hello_v0.hex",
    parameter DMEM_INIT_FILE = "src/riscv_fw/hello_v0.hex"
) (
    input  wire       clk,
    input  wire       rst_n,
    output wire [3:0] led
);

    localparam [31:0] TIMER_ADDR = 32'h8000_8000;

    wire [31:0] imem_addr;
    wire [31:0] imem_rdata;
    wire [31:0] dmem_addr;
    wire [31:0] dmem_wdata;
    wire [31:0] dmem_rdata;
    wire [31:0] dmem_rdata_ram;
    wire [3:0]  dmem_be;
    wire        dmem_we;
    wire        timer_hit;
    reg  [31:0] cycle_cnt;
    reg  [3:0]  led_q;

    assign led = led_q;

    // MMIO 计时计数器（32KB 数据区间外）：同拍只读；写被忽略且不落 DMEM
    assign timer_hit  = (dmem_addr == TIMER_ADDR);
    assign dmem_rdata = timer_hit ? cycle_cnt : dmem_rdata_ram;

    core_top u_core (
        .clk(clk), .rst_n(rst_n),
        .imem_addr(imem_addr), .imem_rdata(imem_rdata),
        .dmem_addr(dmem_addr), .dmem_wdata(dmem_wdata),
        .dmem_be(dmem_be), .dmem_we(dmem_we), .dmem_rdata(dmem_rdata)
    );

    imem #(.INIT_FILE(IMEM_INIT_FILE)) u_imem (
        .clk(clk), .addr(imem_addr), .rdata(imem_rdata)
    );

    // 哈佛双口加载：DMEM 预载同一镜像（.data 初值 / .rodata），见 design_v0.md §5.8
    dmem #(.INIT_FILE(DMEM_INIT_FILE)) u_dmem (
        .clk(clk), .we(dmem_we && !timer_hit), .be(dmem_be),
        .addr(dmem_addr), .wdata(dmem_wdata), .rdata(dmem_rdata_ram)
    );

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            cycle_cnt <= 32'd0;
        else
            cycle_cnt <= cycle_cnt + 32'd1;
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            led_q <= 4'b0000;
        else if (dmem_we && (dmem_addr == 32'h8000_3FF0))
            led_q <= dmem_wdata[3:0];
    end

endmodule
