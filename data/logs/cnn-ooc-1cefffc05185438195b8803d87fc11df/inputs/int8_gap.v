`timescale 1ns/1ps
// Caller supplies the complete sum of exactly 256 nonnegative INT8 values.
module int8_gap (
    input wire [31:0] total,
    output wire signed [7:0] result,
    output wire error
);
    wire [32:0] rounded;
    assign error = total > 32512;
    assign rounded = ({1'b0, total} + 33'd128) >> 8;
    assign result = error ? 8'sd0 : rounded[7:0];
endmodule
