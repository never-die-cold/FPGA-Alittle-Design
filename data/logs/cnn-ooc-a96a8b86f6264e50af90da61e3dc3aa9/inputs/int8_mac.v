// C02 scalar arithmetic primitive; callers reject overflow, never saturate.
// Legal model operands are signed INT8 [-127,127]; no storage or handshake.
`timescale 1ns/1ps
module int8_mac (
    input wire signed [7:0] activation,
    input wire signed [7:0] weight,
    input wire signed [31:0] accumulator,
    output wire signed [31:0] result,
    output wire overflow
);
    wire signed [15:0] product;
    wire signed [32:0] total;
    assign product = activation * weight;
    assign total = {accumulator[31], accumulator} + {{17{product[15]}}, product};
    assign result = total[31:0];
    assign overflow = total[32] ^ total[31];
endmodule
