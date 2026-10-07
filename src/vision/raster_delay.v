`timescale 1ns/1ps
// Read-before-write circular RAM: data is delayed by DEPTH pixel clocks.
// Only validity resets; RAM contents are never reset, so block RAM can infer.
module raster_delay #(parameter WIDTH=29, DEPTH=4966)(
    input wire clk,rst_n,
    input wire [WIDTH-1:0] in_data,
    output reg [WIDTH-1:0] out_data,
    output reg out_valid
);
    localparam AW=(DEPTH>1)?$clog2(DEPTH):1;
    (* ram_style="block" *) reg [WIDTH-1:0] mem[0:DEPTH-1];
    reg [AW-1:0] ptr;
    reg [AW:0] filled;
    always @(posedge clk) begin
        if(rst_n) begin
            mem[ptr]<=in_data;
            out_data<=mem[ptr];
        end
    end
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n) begin ptr<=0;filled<=0;out_valid<=0;end
        else begin
            ptr<=(ptr==DEPTH-1)?0:ptr+1'b1;
            if(filled<DEPTH) filled<=filled+1'b1;
            out_valid<=(filled==DEPTH);
        end
    end
endmodule
