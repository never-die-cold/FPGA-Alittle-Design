`timescale 1ns/1ps
// PS-side shadow configuration; AXI handshakes are handled by the wrapper.
module cop_config_regs (
    input wire clk, rst_n, write_valid_i, busy_i,
    input wire [11:0] write_offset_i,
    input wire [31:0] write_data_i,
    input wire [3:0] write_strb_i,
    input wire [11:0] read_offset_i,
    output reg write_done_o, slverr_o, cfg_valid_o,
    output reg [31:0] read_data_o,
    output reg [31:0] cfg_applied_o, model_id_o, weight_crc32_o, timeout_cycles_o, weight_bytes_o,
    output reg [31:0] work_order_o,
    output reg [4:0] roi_count_o,
    output reg [7:0] min_margin_o
);
    reg [31:0] shadow [0:19]; integer i; reg [31:0] merged;
    function [31:0] merge32;
        input [31:0] old_value, new_value; input [3:0] strb;
        begin
            merge32=old_value;
            if(strb[0]) merge32[7:0]=new_value[7:0];
            if(strb[1]) merge32[15:8]=new_value[15:8];
            if(strb[2]) merge32[23:16]=new_value[23:16];
            if(strb[3]) merge32[31:24]=new_value[31:24];
        end
    endfunction
    wire shadow_write = write_offset_i>=12'h018 && write_offset_i<=12'h064 &&
                        write_offset_i!=12'h020 && write_offset_i[1:0]==0;
    wire fields_valid = shadow[1]!=0 && shadow[5]>=1 && shadow[5]<=16 && shadow[6]!=0 &&
        shadow[12][5:0]==0 && shadow[13]!=0 && shadow[14][5:0]==0 &&
        shadow[15][5:0]==0 && shadow[16]==4096 && shadow[17][5:0]==0 &&
        shadow[18]==16 && shadow[19]<=254;
    always @* begin
        read_data_o=0;
        if(read_offset_i==12'h020) read_data_o=cfg_applied_o;
        else if(read_offset_i>=12'h018 && read_offset_i<=12'h064 && read_offset_i[1:0]==0)
            read_data_o=shadow[(read_offset_i-12'h018)>>2];
    end
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n) begin
            write_done_o<=0; slverr_o<=0; cfg_valid_o<=0; cfg_applied_o<=0;
            model_id_o<=0; weight_crc32_o<=0; roi_count_o<=0; timeout_cycles_o<=0;
            weight_bytes_o<=0; work_order_o<=0; min_margin_o<=0;
            for(i=0;i<20;i=i+1) shadow[i]<=0;
        end else begin
            write_done_o<=0; slverr_o<=0;
            if(write_valid_i) begin
                write_done_o<=1;
                if(shadow_write) begin
                    merged=merge32(shadow[(write_offset_i-12'h018)>>2],write_data_i,write_strb_i);
                    shadow[(write_offset_i-12'h018)>>2]<=merged;
                end else if(write_offset_i==12'h068 && write_data_i==1 && !busy_i && fields_valid) begin
                    cfg_applied_o<=shadow[1]; model_id_o<=shadow[3]; weight_crc32_o<=shadow[4];
                    roi_count_o<=shadow[5][4:0];
                    timeout_cycles_o<=shadow[6]; work_order_o<=shadow[7]; weight_bytes_o<=shadow[13];
                    min_margin_o<=shadow[19][7:0]; cfg_valid_o<=1;
                end else slverr_o<=1;
            end
        end
    end
endmodule
