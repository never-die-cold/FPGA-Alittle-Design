`timescale 1ns / 1ps
// Eight signed INT8 products reduced by a fixed-width balanced tree.
module dot8 (
    input  wire [63:0] act_i,
    input  wire [63:0] weight_i,
    output wire signed [18:0] sum_o
);
    wire [127:0] product_bus;
    wire signed [16:0] sum01, sum23, sum45, sum67;
    wire signed [17:0] sum0123, sum4567;
    genvar lane;

    generate
        for (lane = 0; lane < 8; lane = lane + 1) begin : gen_mac_lane
            mac_lane u_mac_lane (
                .act_i(act_i[8*lane +: 8]),
                .weight_i(weight_i[8*lane +: 8]),
                .product_o(product_bus[16*lane +: 16])
            );
        end
    endgenerate

    assign sum01 = $signed({product_bus[15],  product_bus[15:0]})
                 + $signed({product_bus[31],  product_bus[31:16]});
    assign sum23 = $signed({product_bus[47],  product_bus[47:32]})
                 + $signed({product_bus[63],  product_bus[63:48]});
    assign sum45 = $signed({product_bus[79],  product_bus[79:64]})
                 + $signed({product_bus[95],  product_bus[95:80]});
    assign sum67 = $signed({product_bus[111], product_bus[111:96]})
                 + $signed({product_bus[127], product_bus[127:112]});
    assign sum0123 = $signed({sum01[16], sum01}) + $signed({sum23[16], sum23});
    assign sum4567 = $signed({sum45[16], sum45}) + $signed({sum67[16], sum67});
    assign sum_o = $signed({sum0123[17], sum0123})
                 + $signed({sum4567[17], sum4567});
endmodule
