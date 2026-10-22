`timescale 1ns/1ps
// Board-top activations: sixteen 4096-byte ROI slots plus shared ping/pong/GAP buffers.
module cop_activation_storage (
    input wire clk, rst_n, init_we_i, input wire [15:0] init_address_i,
    input wire [63:0] init_data_i, input wire [3:0] roi_index_i,
    input wire read_enable_i, input wire [1:0] read_bank_i,
    input wire [15:0] read_address_i, input wire write_enable_i,
    input wire [1:0] write_bank_i, input wire [15:0] write_address_i,
    input wire [63:0] write_data_i, output reg [63:0] input_data_o
);
    reg [63:0] gap [0:7],gap_q; wire [63:0] roi_q,ping_q,pong_q;
    reg [1:0] read_bank_q; reg [2:0] roi_lane_q;
    cop_sync_ram_1r1w #(.AW(13)) roi_ram(.clk(clk),.we_i(init_we_i),
        .re_i(read_enable_i && read_bank_i==0),.write_address_i(init_address_i[12:0]),
        .read_address_i({roi_index_i,read_address_i[11:3]}),.write_data_i(init_data_i),.read_data_o(roi_q));
    cop_sync_ram_1r1w #(.AW(12)) ping_ram(.clk(clk),
        .we_i(write_enable_i && write_bank_i==1),.re_i(read_enable_i && read_bank_i==1),
        .write_address_i(write_address_i[11:0]),.read_address_i(read_address_i[11:0]),
        .write_data_i(write_data_i),.read_data_o(ping_q));
    cop_sync_ram_1r1w #(.AW(11)) pong_ram(.clk(clk),
        .we_i(write_enable_i && write_bank_i==2),.re_i(read_enable_i && read_bank_i==2),
        .write_address_i(write_address_i[10:0]),.read_address_i(read_address_i[10:0]),
        .write_data_i(write_data_i),.read_data_o(pong_q));
    always @* begin
        case(read_bank_q)
            0: input_data_o={56'd0,roi_q[roi_lane_q*8 +: 8]};
            1: input_data_o=ping_q; 2: input_data_o=pong_q; 3: input_data_o=gap_q;
        endcase
    end
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n) begin read_bank_q<=0; roi_lane_q<=0; gap_q<=0; end
        else begin
            if(write_enable_i && write_bank_i==3) gap[write_address_i]<=write_data_i;
            if(read_enable_i && read_bank_i==3) gap_q<=gap[read_address_i];
            if(read_enable_i) begin read_bank_q<=read_bank_i; roi_lane_q<=read_address_i[2:0]; end
        end
    end
endmodule
