`timescale 1ns/1ps
// One synchronous read port plus one write port; no reset keeps BRAM inference valid.
module cop_sync_ram_1r1w #(parameter AW=9, parameter DW=64) (
    input wire clk, we_i, re_i,
    input wire [AW-1:0] write_address_i, read_address_i,
    input wire [DW-1:0] write_data_i,
    output reg [DW-1:0] read_data_o
);
    (* ram_style="block" *) reg [DW-1:0] mem [0:(1<<AW)-1];
    always @(posedge clk) begin
        if(we_i) mem[write_address_i] <= write_data_i;
        if(re_i) read_data_o <= mem[read_address_i];
    end
endmodule
