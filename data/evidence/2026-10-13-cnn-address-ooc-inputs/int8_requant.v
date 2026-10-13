`timescale 1ns/1ps
// C02: ReLU before requant; nearest rounding with half cases away from zero.
module int8_requant (
    input wire signed [31:0] accumulator,
    input wire [31:0] multiplier,
    input wire [5:0] shift,
    input wire relu,
    output wire signed [7:0] result,
    output wire error
);
    wire signed [31:0] value;
    wire signed [63:0] product;
    wire [63:0] magnitude, rounded;
    assign error = multiplier == 0 || multiplier[31] || shift == 63;
    assign value = relu && accumulator[31] ? 32'sd0 : accumulator;
    assign product = value * $signed(multiplier);
    // Valid INT32 * positive INT32 never reaches INT64_MIN.
    assign magnitude = product[63] ? -product : product;
    assign rounded = shift == 0 ? magnitude : (magnitude + (64'd1 << (shift-1))) >> shift;
    assign result = error ? 8'sd0 : rounded > 127 ? (product[63] ? -8'sd127 : 8'sd127)
                   : product[63] ? -$signed(rounded[7:0]) : $signed(rounded[7:0]);
endmodule
