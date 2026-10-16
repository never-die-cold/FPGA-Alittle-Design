`timescale 1ns/1ps
// Four CE stages: signed multiply, absolute value, rounding add, shift/saturate.
module int8_requant_pipeline (
    input wire clk,rst_n,ce,abort,in_valid,
    input wire signed [31:0] accumulator,
    input wire [31:0] multiplier,
    input wire [5:0] shift,
    input wire relu,
    output wire out_valid,
    output reg signed [7:0] result,
    output wire error
);
    reg [3:0] valid,errors;
    reg signed [63:0] product;
    reg [63:0] magnitude,biased;
    reg [5:0] s0,s1,s2;
    reg neg1,neg2;
    wire signed [31:0] value=relu && accumulator[31] ? 32'sd0 : accumulator;
    wire [63:0] rounded=s2==0 ? biased : biased>>s2;
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n) begin valid<=0; errors<=0; end
        else if(abort) begin valid<=0; errors<=0; end
        else if(ce) begin
            valid<={valid[2:0],in_valid};
            errors<={errors[2:0],multiplier==0 || multiplier[31] || shift==63};
        end
    end
    always @(posedge clk) if(ce) begin
        product<=value*$signed(multiplier); s0<=shift;
        magnitude<=product[63] ? -product : product; neg1<=product[63]; s1<=s0;
        biased<=s1==0 ? magnitude : magnitude+(64'd1<<(s1-1)); neg2<=neg1; s2<=s1;
        result<=errors[2] ? 8'sd0 : rounded>127 ? (neg2 ? -8'sd127 : 8'sd127)
                : neg2 ? -$signed(rounded[7:0]) : $signed(rounded[7:0]);
    end
    assign out_valid=valid[3]; assign error=errors[3];
endmodule
