`timescale 1ns/1ps
// C01 read-only status CSR. AXI/stream clock is FCLK0; display is independent.
module capture_status_axi #(parameter WIDTH=1280, HEIGHT=720)(
    (* X_INTERFACE_PARAMETER="XIL_INTERFACENAME s_axi_aclk, ASSOCIATED_BUSIF s_axi:stream, ASSOCIATED_RESET s_axi_aresetn" *)
    input wire s_axi_aclk,
    (* X_INTERFACE_PARAMETER="XIL_INTERFACENAME s_axi_aresetn, POLARITY ACTIVE_LOW" *)
    input wire s_axi_aresetn,
    input wire [15:0] s_axi_awaddr,
    input wire [2:0] s_axi_awprot,
    input wire s_axi_awvalid, output wire s_axi_awready,
    input wire [31:0] s_axi_wdata, input wire [3:0] s_axi_wstrb,
    input wire s_axi_wvalid, output wire s_axi_wready,
    output reg s_axi_bvalid, input wire s_axi_bready, output wire [1:0] s_axi_bresp,
    input wire [15:0] s_axi_araddr, input wire [2:0] s_axi_arprot,
    input wire s_axi_arvalid, output wire s_axi_arready,
    output reg [31:0] s_axi_rdata, output reg s_axi_rvalid,
    input wire s_axi_rready, output reg [1:0] s_axi_rresp,
    input wire pclk, video_locked, pixel_overflow,
    input wire [23:0] raw_rbg,
    output wire [23:0] native_rgb,
    (* X_INTERFACE_PARAMETER="XIL_INTERFACENAME pixel_reset, POLARITY ACTIVE_HIGH" *)
    output wire pixel_reset,
    (* X_INTERFACE_INFO="xilinx.com:interface:axis:1.0 stream TDATA", X_INTERFACE_MODE="monitor" *)
    input wire [23:0] stream_tdata,
    (* X_INTERFACE_INFO="xilinx.com:interface:axis:1.0 stream TVALID" *)
    input wire stream_tvalid,
    (* X_INTERFACE_INFO="xilinx.com:interface:axis:1.0 stream TREADY" *)
    input wire stream_tready,
    (* X_INTERFACE_INFO="xilinx.com:interface:axis:1.0 stream TUSER" *)
    input wire stream_tuser,
    (* X_INTERFACE_INFO="xilinx.com:interface:axis:1.0 stream TLAST" *)
    input wire stream_tlast
);
    wire clk=s_axi_aclk, rst_n=s_axi_aresetn;
    (* ASYNC_REG="TRUE" *) reg [1:0] lock_sync;
    wire pixel_rst_n, fault, active, complete;
    wire [31:0] seq, rejected, epoch;
    reg fault_q, lock_q;
    reg [31:0] overflow_intervals, lock_losses;
    // Low-address byte in little-endian DDR must be B, then G, then R.
    assign native_rgb={raw_rbg[23:16],raw_rbg[7:0],raw_rbg[15:8]};
    reset_sync pixel_release(.clk(pclk),.arst_n(rst_n && video_locked),.rst_n(pixel_rst_n));
    assign pixel_reset=!pixel_rst_n;
    capture_fault_cdc fault_bridge(.src_clk(pclk),.dst_clk(clk),.rst_n(rst_n),
        .src_fault(pixel_overflow),.dst_fault(fault));
    capture_stream_monitor #(.WIDTH(WIDTH),.HEIGHT(HEIGHT)) monitor(
        .clk(clk),.rst_n(rst_n),.locked(lock_sync[1]),.fault(fault),
        .tvalid(stream_tvalid),.tready(stream_tready),
        .tuser(stream_tuser),.tlast(stream_tlast),.active(active),
        .stream_seq(seq),.rejected_frames(rejected),.error_epoch(epoch),.frame_complete(complete));
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n) begin
            lock_sync<=0; fault_q<=0; lock_q<=0; overflow_intervals<=0; lock_losses<=0;
        end else begin
            lock_sync<={lock_sync[0],video_locked}; fault_q<=fault; lock_q<=lock_sync[1];
            if(fault && !fault_q) overflow_intervals<=overflow_intervals+1;
            if(lock_q && !lock_sync[1]) lock_losses<=lock_losses+1;
        end
    end
    // Every write is rejected with SLVERR, including split AW/W arrival.
    reg aw_hold, w_hold;
    assign s_axi_awready=!s_axi_bvalid && !aw_hold;
    assign s_axi_wready=!s_axi_bvalid && !w_hold;
    assign s_axi_bresp=2'b10;
    assign s_axi_arready=!s_axi_rvalid || s_axi_rready;
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n) begin aw_hold<=0; w_hold<=0; s_axi_bvalid<=0; end
        else begin
            if(s_axi_awvalid && s_axi_awready) aw_hold<=1;
            if(s_axi_wvalid && s_axi_wready) w_hold<=1;
            if(!s_axi_bvalid && (aw_hold || (s_axi_awvalid && s_axi_awready)) &&
                (w_hold || (s_axi_wvalid && s_axi_wready))) begin
                aw_hold<=0; w_hold<=0; s_axi_bvalid<=1;
            end else if(s_axi_bready) s_axi_bvalid<=0;
        end
    end
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n) begin s_axi_rvalid<=0; s_axi_rdata<=0; s_axi_rresp<=0; end
        else if(s_axi_arvalid && s_axi_arready) begin
            s_axi_rvalid<=1; s_axi_rdata<=0; s_axi_rresp<=0;
            case(s_axi_araddr)
                16'h0000: s_axi_rdata<=32'h43415031; // CAP1
                16'h0004: s_axi_rdata<={28'd0,(epoch!=0),fault,active,lock_sync[1]};
                16'h0008: s_axi_rdata<=seq;
                16'h000c: s_axi_rdata<=rejected;
                16'h0010: s_axi_rdata<=epoch;
                16'h0014: s_axi_rdata<=WIDTH;
                16'h0018: s_axi_rdata<=HEIGHT;
                16'h001c: s_axi_rdata<=overflow_intervals;
                16'h0020: s_axi_rdata<=lock_losses;
                default: s_axi_rresp<=2'b10;
            endcase
        end else if(s_axi_rready) s_axi_rvalid<=0;
    end
endmodule
