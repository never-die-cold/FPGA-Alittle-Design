`timescale 1ns/1ps
// Manifest-v1 byte offsets to physical model banks. Writes always target the inactive slot.
module cop_payload_adapter (
    input wire clk, rst_n, start_i, commit_i, abort_i,
    input wire [31:0] payload_base_i, payload_bytes_i,
    input wire store_write_i, input wire [31:0] store_addr_i,
    input wire [63:0] store_data_i, input wire [7:0] store_strb_i,
    input wire active_bank_i,
    output wire store_ready_o,
    output reg init_we_o, init_bank_o, output reg [2:0] init_kind_o,
    output reg [15:0] init_address_o, output reg [63:0] init_data_o,
    output reg shadow_bank_o, commit_o, error_o, loading_o
);
    localparam TOTAL_BYTES=32'd36032;
    localparam WEIGHT_END=32'd34432, BIAS_BASE=32'd34432, BIAS_VALID_END=32'd35020;
    localparam MULT_BASE=32'd35072, MULT_VALID_END=32'd35660, SHIFT_BASE=32'd35712;
    reg pending; reg [3:0] step;
    reg [31:0] next_addr, hold_addr;
    reg [63:0] hold_data;
    wire [31:0] byte_addr=hold_addr+step;
    assign store_ready_o=loading_o && !pending;
    function shift_valid;
        input [31:0] address;
        begin shift_valid=(address>=35712 && address<35728) ||
            (address>=35776 && address<35808) ||
            (address>=35840 && address<35872) ||
            (address>=35904 && address<35971); end
    endfunction
    function [7:0] shift_index;
        input [31:0] address;
        begin
            if(address<35728) shift_index=address-35712;
            else if(address<35808) shift_index=16+address-35776;
            else if(address<35872) shift_index=48+address-35840;
            else shift_index=80+address-35904;
        end
    endfunction
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n) begin
            pending<=0; step<=0; next_addr<=0; hold_addr<=0; hold_data<=0;
            init_we_o<=0; init_bank_o<=0; init_kind_o<=0; init_address_o<=0; init_data_o<=0;
            shadow_bank_o<=1; commit_o<=0; error_o<=0; loading_o<=0;
        end else begin
            init_we_o<=0; commit_o<=0; error_o<=0;
            if(start_i) begin
                pending<=0; next_addr<=0;
                if(loading_o || payload_base_i[5:0]!=0 || payload_bytes_i!=TOTAL_BYTES) begin
                    loading_o<=0; error_o<=1;
                end else begin loading_o<=1; shadow_bank_o<=!active_bank_i; end
            end else if(abort_i) begin loading_o<=0; pending<=0;
            end else if(commit_i) begin
                if(loading_o && !pending && next_addr==TOTAL_BYTES) begin
                    commit_o<=1; loading_o<=0;
                end else begin error_o<=1; loading_o<=0; pending<=0; end
            end else if(store_write_i && store_ready_o) begin
                if(store_addr_i!=next_addr || store_addr_i[2:0]!=0 || store_strb_i!=8'hff ||
                   store_addr_i>TOTAL_BYTES-8) begin
                    error_o<=1; loading_o<=0; pending<=0;
                end else begin
                    hold_addr<=store_addr_i; hold_data<=store_data_i; step<=0; pending<=1;
                    next_addr<=next_addr+8;
                end
            end else if(pending) begin
                init_bank_o<=shadow_bank_o;
                if(hold_addr<WEIGHT_END) begin
                    init_we_o<=1; init_kind_o<=1; init_address_o<=hold_addr[18:3];
                    init_data_o<=hold_data; pending<=0;
                end else if(hold_addr<MULT_BASE) begin
                    if(byte_addr<BIAS_VALID_END) begin
                        init_we_o<=1; init_kind_o<=2; init_address_o<=(byte_addr-BIAS_BASE)>>2;
                        init_data_o<={32'd0,hold_data[step*8 +: 32]};
                    end
                    if(step==4) pending<=0; else step<=4;
                end else if(hold_addr<SHIFT_BASE) begin
                    if(byte_addr<MULT_VALID_END) begin
                        init_we_o<=1; init_kind_o<=3; init_address_o<=(byte_addr-MULT_BASE)>>2;
                        init_data_o<={32'd0,hold_data[step*8 +: 32]};
                    end
                    if(step==4) pending<=0; else step<=4;
                end else begin
                    if(shift_valid(byte_addr)) begin
                        if(hold_data[step*8 +: 8]>62) begin
                            error_o<=1; loading_o<=0; pending<=0;
                        end else begin
                            init_we_o<=1; init_kind_o<=4; init_address_o<=shift_index(byte_addr);
                            init_data_o<={56'd0,hold_data[step*8 +: 8]};
                        end
                    end
                    if(step==7) pending<=0; else step<=step+1;
                end
            end
        end
    end
endmodule
