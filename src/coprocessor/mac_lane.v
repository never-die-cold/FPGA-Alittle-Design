`timescale 1ns / 1ps
// Signed INT8 multiply lane; accumulation belongs to dot8/mac_array.
module mac_lane (
    input  wire signed [7:0]  act_i,
    input  wire signed [7:0]  weight_i,
    output wire signed [15:0] product_o
);
    assign product_o = act_i * weight_i;
endmodule
