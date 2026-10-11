`timescale 1ns/1ps
// 稳定总线握手：请求发出到确认返回前，hold_data/hold_id 不变。
module config_bridge #(parameter WIDTH=352)(
    input wire src_clk, dst_clk, rst_n,
    input wire src_commit,
    input wire [WIDTH-1:0] src_data,
    input wire dst_frame,
    output wire src_busy,
    output reg [31:0] src_applied,
    output reg [WIDTH-1:0] dst_data,
    output reg [31:0] dst_id
);
    reg [WIDTH-1:0] hold_data;
    reg [31:0] hold_id;
    reg request, acknowledge;
    wire src_reset,dst_reset;
    reset_sync u_src_reset(.clk(src_clk),.arst_n(rst_n),.rst_n(src_reset));
    reset_sync u_dst_reset(.clk(dst_clk),.arst_n(rst_n),.rst_n(dst_reset));
    (* ASYNC_REG="TRUE" *) reg req_meta,req_sync,ack_meta,ack_sync;
    assign src_busy=request!=ack_sync;
    always @(posedge src_clk or negedge src_reset) begin
        if(!src_reset) begin
            hold_data<=0;hold_id<=0;request<=0;
            ack_meta<=0;ack_sync<=0;src_applied<=0;
        end else begin
            ack_meta<=acknowledge;ack_sync<=ack_meta;
            if(!src_busy) src_applied<=hold_id;
            if(src_commit && !src_busy) begin
                hold_data<=src_data;hold_id<=hold_id+1;request<=~request;
            end
        end
    end
    always @(posedge dst_clk or negedge dst_reset) begin
        if(!dst_reset) begin
            req_meta<=0;req_sync<=0;acknowledge<=0;dst_data<=0;dst_id<=0;
        end else begin
            req_meta<=request;req_sync<=req_meta;
            if(dst_frame && req_sync!=acknowledge) begin
                dst_data<=hold_data;dst_id<=hold_id;acknowledge<=req_sync;
            end
        end
    end
endmodule
