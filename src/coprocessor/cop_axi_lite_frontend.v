`timescale 1ns/1ps
// One-outstanding AXI4-Lite front end; register permission stays in the backend.
module cop_axi_lite_frontend (
    input wire clk, rst_n,
    input wire [11:0] s_awaddr_i, input wire s_awvalid_i, output wire s_awready_o,
    input wire [31:0] s_wdata_i, input wire [3:0] s_wstrb_i,
    input wire s_wvalid_i, output wire s_wready_o,
    output reg [1:0] s_bresp_o, output reg s_bvalid_o, input wire s_bready_i,
    input wire [11:0] s_araddr_i, input wire s_arvalid_i, output wire s_arready_o,
    output reg [31:0] s_rdata_o, output reg [1:0] s_rresp_o,
    output reg s_rvalid_o, input wire s_rready_i,
    output reg write_valid_o, output reg [11:0] write_offset_o,
    output reg [31:0] write_data_o, output reg [3:0] write_strb_o,
    input wire write_done_i, write_slverr_i,
    output wire [11:0] read_offset_o, input wire [31:0] read_data_i, input wire read_slverr_i
);
    reg have_aw,have_w,write_wait;
    assign s_awready_o=!have_aw && !write_wait && !s_bvalid_o;
    assign s_wready_o=!have_w && !write_wait && !s_bvalid_o;
    assign s_arready_o=!s_rvalid_o;
    assign read_offset_o=s_araddr_i;
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n) begin
            have_aw<=0; have_w<=0; write_wait<=0; write_valid_o<=0;
            write_offset_o<=0; write_data_o<=0; write_strb_o<=0;
            s_bresp_o<=0; s_bvalid_o<=0; s_rdata_o<=0; s_rresp_o<=0; s_rvalid_o<=0;
        end else begin
            write_valid_o<=0;
            if(s_awvalid_i && s_awready_o) begin have_aw<=1; write_offset_o<=s_awaddr_i; end
            if(s_wvalid_i && s_wready_o) begin
                have_w<=1; write_data_o<=s_wdata_i; write_strb_o<=s_wstrb_i;
            end
            if(have_aw && have_w && !write_wait) begin write_valid_o<=1; write_wait<=1; end
            if(write_wait && write_done_i) begin
                write_wait<=0; have_aw<=0; have_w<=0; s_bvalid_o<=1;
                s_bresp_o<=write_slverr_i ? 2'b10 : 2'b00;
            end else if(s_bvalid_o && s_bready_i) s_bvalid_o<=0;
            if(s_arvalid_i && s_arready_o) begin
                s_rdata_o<=read_data_i; s_rresp_o<=read_slverr_i ? 2'b10 : 2'b00; s_rvalid_o<=1;
            end else if(s_rvalid_o && s_rready_i) s_rvalid_o<=0;
        end
    end
endmodule
