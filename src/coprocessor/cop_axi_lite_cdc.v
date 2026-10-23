`timescale 1ns/1ps
// One-outstanding AXI4-Lite bridge: stable payload plus toggle/ack in each direction.
module cop_axi_lite_cdc (
    input wire s_clk,s_rst_n,input wire [11:0] s_awaddr,input wire s_awvalid,output wire s_awready,
    input wire [31:0] s_wdata,input wire [3:0] s_wstrb,input wire s_wvalid,output wire s_wready,
    output reg [1:0] s_bresp,output reg s_bvalid,input wire s_bready,
    input wire [11:0] s_araddr,input wire s_arvalid,output wire s_arready,
    output reg [31:0] s_rdata,output reg [1:0] s_rresp,output reg s_rvalid,input wire s_rready,
    input wire m_clk,m_rst_n,output reg [11:0] m_awaddr,output reg m_awvalid,input wire m_awready,
    output reg [31:0] m_wdata,output reg [3:0] m_wstrb,output reg m_wvalid,input wire m_wready,
    input wire [1:0] m_bresp,input wire m_bvalid,output wire m_bready,
    output reg [11:0] m_araddr,output reg m_arvalid,input wire m_arready,
    input wire [31:0] m_rdata,input wire [1:0] m_rresp,input wire m_rvalid,output wire m_rready
);
    reg [11:0] aw_hold,ar_hold; reg [31:0] wd_hold; reg [3:0] ws_hold;
    reg have_aw,have_w,w_busy,r_busy,w_req,r_req,w_ack_seen,r_ack_seen;
    reg [1:0] bresp_hold; reg [31:0] rdata_hold; reg [1:0] rresp_hold;
    reg w_ack,r_ack,w_active,r_active;
    (* ASYNC_REG="TRUE", SHREG_EXTRACT="NO" *) reg wack_s1,wack_s2,rack_s1,rack_s2;
    (* ASYNC_REG="TRUE", SHREG_EXTRACT="NO" *) reg [1:0] bresp_s1,bresp_s2,rresp_s1,rresp_s2;
    (* ASYNC_REG="TRUE", SHREG_EXTRACT="NO" *) reg [31:0] rdata_s1,rdata_s2;
    assign s_awready=!have_aw && !w_busy && !s_bvalid;
    assign s_wready=!have_w && !w_busy && !s_bvalid;
    assign s_arready=!r_busy && !s_rvalid;
    always @(posedge s_clk or negedge s_rst_n) begin
        if(!s_rst_n) begin
            aw_hold<=0; ar_hold<=0; wd_hold<=0; ws_hold<=0;
            have_aw<=0; have_w<=0; w_busy<=0; r_busy<=0; w_req<=0; r_req<=0;
            w_ack_seen<=0; r_ack_seen<=0; s_bresp<=0; s_bvalid<=0; s_rdata<=0; s_rresp<=0; s_rvalid<=0;
            wack_s1<=0; wack_s2<=0; rack_s1<=0; rack_s2<=0;
            bresp_s1<=0; bresp_s2<=0; rdata_s1<=0; rdata_s2<=0; rresp_s1<=0; rresp_s2<=0;
        end else begin
            wack_s1<=w_ack; wack_s2<=wack_s1; rack_s1<=r_ack; rack_s2<=rack_s1;
            bresp_s1<=bresp_hold; bresp_s2<=bresp_s1;
            rdata_s1<=rdata_hold; rdata_s2<=rdata_s1; rresp_s1<=rresp_hold; rresp_s2<=rresp_s1;
            if(s_awvalid && s_awready) begin aw_hold<=s_awaddr; have_aw<=1; end
            if(s_wvalid && s_wready) begin wd_hold<=s_wdata; ws_hold<=s_wstrb; have_w<=1; end
            if(!w_busy && have_aw && have_w) begin w_req<=!w_req; w_busy<=1; have_aw<=0; have_w<=0; end
            if(w_busy && wack_s2!=w_ack_seen) begin
                w_ack_seen<=wack_s2; w_busy<=0; s_bresp<=bresp_s2; s_bvalid<=1;
            end else if(s_bvalid && s_bready) s_bvalid<=0;
            if(s_arvalid && s_arready) begin ar_hold<=s_araddr; r_req<=!r_req; r_busy<=1; end
            if(r_busy && rack_s2!=r_ack_seen) begin
                r_ack_seen<=rack_s2; r_busy<=0; s_rdata<=rdata_s2; s_rresp<=rresp_s2; s_rvalid<=1;
            end else if(s_rvalid && s_rready) s_rvalid<=0;
        end
    end
    (* ASYNC_REG="TRUE", SHREG_EXTRACT="NO" *) reg wreq_m1,wreq_m2,rreq_m1,rreq_m2;
    reg wreq_seen,rreq_seen;
    (* ASYNC_REG="TRUE", SHREG_EXTRACT="NO" *) reg [11:0] aw_m1,aw_m2,ar_m1,ar_m2;
    (* ASYNC_REG="TRUE", SHREG_EXTRACT="NO" *) reg [31:0] wd_m1,wd_m2;
    (* ASYNC_REG="TRUE", SHREG_EXTRACT="NO" *) reg [3:0] ws_m1,ws_m2;
    always @(posedge m_clk or negedge m_rst_n) begin
        if(!m_rst_n) begin
            w_ack<=0; r_ack<=0; w_active<=0; r_active<=0; wreq_m1<=0; wreq_m2<=0; wreq_seen<=0;
            rreq_m1<=0; rreq_m2<=0; rreq_seen<=0; m_awvalid<=0; m_wvalid<=0; m_arvalid<=0;
            aw_m1<=0; aw_m2<=0; ar_m1<=0; ar_m2<=0;
            wd_m1<=0; wd_m2<=0; ws_m1<=0; ws_m2<=0;
            m_awaddr<=0; m_wdata<=0; m_wstrb<=0; m_araddr<=0;
            bresp_hold<=0; rdata_hold<=0; rresp_hold<=0;
        end else begin
            wreq_m1<=w_req; wreq_m2<=wreq_m1; rreq_m1<=r_req; rreq_m2<=rreq_m1;
            aw_m1<=aw_hold; aw_m2<=aw_m1; wd_m1<=wd_hold; wd_m2<=wd_m1; ws_m1<=ws_hold; ws_m2<=ws_m1;
            ar_m1<=ar_hold; ar_m2<=ar_m1;
            if(!w_active && wreq_m2!=wreq_seen) begin
                wreq_seen<=wreq_m2; m_awaddr<=aw_m2; m_wdata<=wd_m2; m_wstrb<=ws_m2;
                m_awvalid<=1; m_wvalid<=1; w_active<=1;
            end
            if(m_awvalid && m_awready) m_awvalid<=0;
            if(m_wvalid && m_wready) m_wvalid<=0;
            if(m_bvalid && m_bready) begin bresp_hold<=m_bresp; w_ack<=wreq_seen; w_active<=0; end
            if(!r_active && rreq_m2!=rreq_seen) begin
                rreq_seen<=rreq_m2; m_araddr<=ar_m2; m_arvalid<=1; r_active<=1;
            end
            if(m_arvalid && m_arready) m_arvalid<=0;
            if(m_rvalid && m_rready) begin
                rdata_hold<=m_rdata; rresp_hold<=m_rresp; r_ack<=rreq_seen; r_active<=0;
            end
        end
    end
    assign m_bready=w_active && !m_awvalid && !m_wvalid;
    assign m_rready=r_active && !m_arvalid;
endmodule
