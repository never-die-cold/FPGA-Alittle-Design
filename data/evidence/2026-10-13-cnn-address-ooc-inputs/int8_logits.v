`timescale 1ns/1ps
module int8_logits (
    input wire [23:0] logits,
    input wire [7:0] min_margin,
    output wire [1:0] class_id,
    output wire [7:0] margin_q,
    output wire [14:0] score_q15,
    output wire low_conf,
    output wire error
);
    wire signed [7:0] a, b, c, top1, top2;
    wire [1:0] winner;
    wire signed [8:0] difference;
    wire [15:0] scaled;
    assign a = logits[7:0]; assign b = logits[15:8]; assign c = logits[23:16];
    assign error = a == -8'sd128 || b == -8'sd128 || c == -8'sd128;
    assign winner = a >= b && a >= c ? 2'd0 : b >= c ? 2'd1 : 2'd2;
    assign top1 = winner == 0 ? a : winner == 1 ? b : c;
    assign top2 = winner == 0 ? (b >= c ? b : c)
                : winner == 1 ? (a >= c ? a : c) : (a >= b ? a : b);
    assign difference = {top1[7], top1} - {top2[7], top2};
    assign margin_q = error ? 8'd0 : difference[7:0];
    // Exact for 0..254: floor((m*32767+127)/254) = 129*m + (m>=127).
    assign scaled = {1'b0,margin_q,7'd0}+{8'd0,margin_q}+(margin_q>=127 ? 16'd1 : 16'd0);
    assign score_q15 = error ? 15'd0 : scaled[14:0];
    assign class_id = error ? 2'd3 : winner;
    assign low_conf = error || margin_q < min_margin;
endmodule
