`timescale 1ns / 1ps
// PYNQ-Z2 stand-alone LED smoke test. Author: Codex, 2026-09-20.
// clk: 125 MHz; btn0: active-high reset; led: active-high one-hot LEDs.
// DIV_CYCLES must be >= 1. Default: one step every 0.5 seconds.
module pynq_z2_smoke_top #(
    parameter integer DIV_CYCLES = 62500000
) (
    input wire clk,
    input wire btn0,
    output reg [3:0] led = 4'b0001
);
    // Verilog-2001 constant function, including the DIV_CYCLES=1 case.
    function integer counter_width;
        input integer value;
        integer remaining;
        begin
            remaining = value - 1;
            counter_width = 0;
            while (remaining > 0) begin
                counter_width = counter_width + 1;
                remaining = remaining >> 1;
            end
            if (counter_width < 1) counter_width = 1;
        end
    endfunction

    localparam integer COUNT_WIDTH = counter_width(DIV_CYCLES);
    localparam integer LAST_COUNT_INTEGER = DIV_CYCLES - 1;
    localparam [COUNT_WIDTH-1:0] LAST_COUNT = LAST_COUNT_INTEGER[COUNT_WIDTH-1:0];
    reg [COUNT_WIDTH-1:0] count = 0;
    // FPGA configuration INIT provides start-up reset without a button press.
    // Asynchronous assertion, two-clock synchronous release. Button bounce
    // may restart reset; it cannot advance the LED sequence while held.
    (* ASYNC_REG = "TRUE", SHREG_EXTRACT = "NO" *)
    reg [1:0] reset_pipe = 2'b11;
    always @(posedge clk or posedge btn0) begin
        if (btn0) reset_pipe <= 2'b11;
        else reset_pipe <= {reset_pipe[0], 1'b0};
    end

    // Clock enable divider: all registers stay on the original clock.
    always @(posedge clk) begin
        if (reset_pipe[1]) begin
            count <= 0;
            led <= 4'b0001;
        end else if (count == LAST_COUNT) begin
            count <= 0;
            led <= {led[2:0], led[3]};
        end else begin
            count <= count + 1'b1;
        end
    end
endmodule
