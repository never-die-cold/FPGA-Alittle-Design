`timescale 1ns/1ps
// Five CE stages: 128 DSP products, balanced 8-way sum, INT32 checked add.
// Data registers need no reset; validity is cleared on reset/abort.
module mac_array_pipeline (
    input wire clk, rst_n, ce, abort, in_valid,
    input wire [63:0] activation_lanes,
    input wire [1023:0] weight_lanes,
    input wire [511:0] accumulator_lanes,
    output wire out_valid,
    output wire [511:0] result_lanes,
    output wire [15:0] overflow
);
    reg [4:0] valid;
    reg [511:0] acc0, acc1, acc2, acc3;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) valid<=0;
        else if (abort) valid<=0;
        else if (ce) valid<={valid[3:0],in_valid};
    end
    always @(posedge clk) if (ce) begin
        acc0<=accumulator_lanes; acc1<=acc0; acc2<=acc1; acc3<=acc2;
    end
    assign out_valid=valid[4];
    genvar o,i;
    generate for(o=0;o<16;o=o+1) begin: lanes
        (* use_dsp="yes" *) reg signed [15:0] products [0:7];
        reg signed [16:0] pairs [0:3];
        reg signed [17:0] quads [0:1];
        reg signed [18:0] dot;
        reg signed [32:0] total;
        for(i=0;i<8;i=i+1) begin: multiply
            always @(posedge clk) if(ce)
                products[i]<=$signed(activation_lanes[i*8 +: 8])*$signed(weight_lanes[(o*8+i)*8 +: 8]);
        end
        for(i=0;i<4;i=i+1) begin: sum_pairs
            always @(posedge clk) if(ce)
                pairs[i]<={products[2*i][15],products[2*i]}+{products[2*i+1][15],products[2*i+1]};
        end
        for(i=0;i<2;i=i+1) begin: sum_quads
            always @(posedge clk) if(ce)
                quads[i]<={pairs[2*i][16],pairs[2*i]}+{pairs[2*i+1][16],pairs[2*i+1]};
        end
        always @(posedge clk) if(ce) begin
            dot<={quads[0][17],quads[0]}+{quads[1][17],quads[1]};
            total<={acc3[o*32+31],acc3[o*32 +: 32]}+{{14{dot[18]}},dot};
        end
        assign result_lanes[o*32 +: 32]=total[31:0];
        assign overflow[o]=total[32]^total[31];
    end endgenerate
endmodule
