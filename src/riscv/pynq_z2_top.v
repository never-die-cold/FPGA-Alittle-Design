// pynq_z2_top.v —— PYNQ-Z2 板级顶层：125 MHz -> MMCM -> RISC-V SoC
// 板级时钟与复位契约见 src/riscv/design_v0.md §5.8
module pynq_z2_top #(
    parameter integer CORE_CLK_DIVIDE = 25,
    parameter IMEM_INIT_FILE = "src/riscv_fw/hello_v0.hex",
    parameter DMEM_INIT_FILE = "src/riscv_fw/hello_v0.hex"
) (
    input  wire       clk,
    input  wire       btn0,
    output wire [3:0] led
);

    wire clk_feedback_raw;
    wire clk_feedback;
    wire core_clk_raw;
    wire core_clk;
    wire mmcm_locked;

    // VCO 固定为 125 MHz * 8 = 1000 MHz；输出频率由 CORE_CLK_DIVIDE 选择。
    MMCME2_BASE #(
        .BANDWIDTH("OPTIMIZED"),
        .CLKIN1_PERIOD(8.000),
        .DIVCLK_DIVIDE(1),
        .CLKFBOUT_MULT_F(8.000),
        .CLKOUT0_DIVIDE_F(CORE_CLK_DIVIDE),
        .STARTUP_WAIT("FALSE")
    ) u_mmcm (
        .CLKIN1(clk),
        .CLKFBIN(clk_feedback),
        .RST(btn0),
        .PWRDWN(1'b0),
        .CLKFBOUT(clk_feedback_raw),
        .CLKOUT0(core_clk_raw),
        .LOCKED(mmcm_locked)
    );

    BUFG u_feedback_bufg (
        .I(clk_feedback_raw),
        .O(clk_feedback)
    );

    BUFG u_core_clk_bufg (
        .I(core_clk_raw),
        .O(core_clk)
    );

    // BTN0 或 MMCM 未锁定时异步复位；锁定后在核时钟域两拍释放。
    wire reset_async = btn0 | ~mmcm_locked;
    (* ASYNC_REG = "TRUE", SHREG_EXTRACT = "NO" *) reg [1:0] reset_pipe = 2'b11;

    always @(posedge core_clk or posedge reset_async) begin
        if (reset_async)
            reset_pipe <= 2'b11;
        else
            reset_pipe <= {reset_pipe[0], 1'b0};
    end

    soc_top #(
        .IMEM_INIT_FILE(IMEM_INIT_FILE),
        .DMEM_INIT_FILE(DMEM_INIT_FILE)
    ) u_soc (
        .clk(core_clk),
        .rst_n(~reset_pipe[1]),
        .led(led)
    );

endmodule
