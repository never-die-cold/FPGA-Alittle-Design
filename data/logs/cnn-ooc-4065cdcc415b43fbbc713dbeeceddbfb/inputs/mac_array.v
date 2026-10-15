`timescale 1ns/1ps
// C02: weights[out_lane16][in_lane8], in_lane varies fastest.
// Combinational arithmetic only; a scheduler must register/validate the result.
module mac_array (
    input wire [63:0] activation_lanes,
    input wire [1023:0] weight_lanes,
    input wire [511:0] accumulator_lanes,
    output wire [511:0] result_lanes,
    output wire [15:0] overflow
);
    wire signed [31:0] products [0:127];
    wire [127:0] product_overflow;
    genvar o, i;
    generate for (o = 0; o < 16; o = o + 1) begin: outputs
        for (i = 0; i < 8; i = i + 1) begin: inputs
            int8_mac cell_mac (
                .activation(activation_lanes[i*8 +: 8]),
                .weight(weight_lanes[(o*8+i)*8 +: 8]), .accumulator(32'sd0),
                .result(products[o*8+i]), .overflow(product_overflow[o*8+i]));
        end
        // Eight products cannot overflow INT32; maximum magnitude is 129032.
        wire signed [31:0] dot;
        wire signed [32:0] total;
        assign dot = products[o*8] + products[o*8+1] + products[o*8+2] + products[o*8+3]
                   + products[o*8+4] + products[o*8+5] + products[o*8+6] + products[o*8+7];
        assign total = {accumulator_lanes[o*32+31], accumulator_lanes[o*32 +: 32]}
                     + {dot[31], dot};
        assign result_lanes[o*32 +: 32] = total[31:0];
        assign overflow[o] = total[32] ^ total[31];
    end endgenerate
endmodule
