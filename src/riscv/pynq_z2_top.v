// pynq_z2_top.v —— PYNQ-Z2 板级顶层：125 MHz -> 40 MHz -> v0 SoC
// 板级时钟与复位契约见 src/riscv/design_v0.md §5.8
module pynq_z2_top (
    input  wire       clk,
    input  wire       btn0,
    output wire [3:0] led
);

    wire clk_feedback_raw;
    wire clk_feedback;
    wire clk_40_raw;
    wire clk_40;
    wire mmcm_locked;

    // 125 MHz * 8 / 25 = 40 MHz；VCO = 1000 MHz。
    MMCME2_BASE #(
        .BANDWIDTH("OPTIMIZED"),
        .CLKIN1_PERIOD(8.000),
        .DIVCLK_DIVIDE(1),
        .CLKFBOUT_MULT_F(8.000),
        .CLKOUT0_DIVIDE_F(25.000),
        .STARTUP_WAIT("FALSE")
    ) u_mmcm (
        .CLKIN1(clk),
        .CLKFBIN(clk_feedback),
        .RST(btn0),
        .PWRDWN(1'b0),
        .CLKFBOUT(clk_feedback_raw),
        .CLKOUT0(clk_40_raw),
        .LOCKED(mmcm_locked)
    );

    BUFG u_feedback_bufg (
        .I(clk_feedback_raw),
        .O(clk_feedback)
    );

    BUFG u_core_clk_bufg (
        .I(clk_40_raw),
        .O(clk_40)
    );

    // BTN0 或 MMCM 未锁定时异步复位；锁定后在 40 MHz 域两拍释放。
    wire reset_async = btn0 | ~mmcm_locked;
    (* ASYNC_REG = "TRUE", SHREG_EXTRACT = "NO" *) reg [1:0] reset_pipe = 2'b11;

    always @(posedge clk_40 or posedge reset_async) begin
        if (reset_async)
            reset_pipe <= 2'b11;
        else
            reset_pipe <= {reset_pipe[0], 1'b0};
    end

    soc_top u_soc (
        .clk(clk_40),
        .rst_n(~reset_pipe[1]),
        .led(led)
    );

endmodule
