`timescale 1ns/1ps
// Four completed analysis rows, tagged by row and source frame parity.
// A row is invalidated before rewriting; unready/stale reads return valid=0.
module diagnostic_rows #(parameter WIDTH=1280)(
    input wire clk,rst_n,write_vs,write_de,write_epoch,
    input wire [7:0] write_y,
    input wire [15:0] read_row,
    input wire [((WIDTH>1)?$clog2(WIDTH):1)-1:0] read_x,
    input wire read_epoch,
    output reg [7:0] read_y,
    output reg read_valid
);
    localparam XW=(WIDTH>1)?$clog2(WIDTH):1;
    (* ram_style="block" *) reg [7:0] mem[0:(4*(1<<XW))-1];
    reg [XW-1:0] wx;
    reg [15:0] wy;
    reg [15:0] row_tag[0:3];
    reg [3:0] ready,epoch_tag;
    wire [XW+1:0] wa={wy[1:0],wx};
    wire [XW+1:0] ra={read_row[1:0],read_x};
    always @(posedge clk) begin
        if(rst_n && write_de) mem[wa]<=write_y;
        read_y<=mem[ra];
    end
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n) begin wx<=0;wy<=0;ready<=0;epoch_tag<=0;read_valid<=0;end
        else begin
            read_valid<=ready[read_row[1:0]] &&
                row_tag[read_row[1:0]]==read_row && epoch_tag[read_row[1:0]]==read_epoch;
            if(write_vs) begin wx<=0;wy<=0;ready<=0;end
            else if(write_de) begin
                if(wx==0) ready[wy[1:0]]<=0;
                if(wx==WIDTH-1) begin
                    wx<=0;wy<=wy+1'b1;ready[wy[1:0]]<=1;
                    row_tag[wy[1:0]]<=wy;epoch_tag[wy[1:0]]<=write_epoch;
                end else wx<=wx+1'b1;
            end
        end
    end
endmodule
