`timescale 1ns/1ps
// Retain a pixel-domain overflow until the AXI domain acknowledges it.
// Events during one request/ack round trip coalesce into one fault interval.
// Reset is PS reset only: loss of the pixel clock must not clear evidence.
module capture_fault_cdc(
    input wire src_clk, dst_clk, rst_n, src_fault,
    output wire dst_fault
);
    reg pending, ack;
    wire src_rst_n;
    reset_sync source_release(.clk(src_clk),.arst_n(rst_n),.rst_n(src_rst_n));
    (* ASYNC_REG="TRUE" *) reg [1:0] ack_sync, pending_sync;
    always @(posedge src_clk or negedge src_rst_n) begin
        if (!src_rst_n) begin pending<=0; ack_sync<=0; end
        else begin
            ack_sync<={ack_sync[0],ack};
            if (src_fault) pending<=1;
            else if (ack_sync[1]) pending<=0;
        end
    end
    always @(posedge dst_clk or negedge rst_n) begin
        if (!rst_n) begin pending_sync<=0; ack<=0; end
        else begin pending_sync<={pending_sync[0],pending}; ack<=pending_sync[1]; end
    end
    assign dst_fault=pending_sync[1];
endmodule
