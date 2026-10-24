`timescale 1ns/1ps
module tb_cop_axi_lite_cdc;
    reg s_clk=0,m_clk=0,s_rst_n=0,m_rst_n=0;
    reg [11:0] s_awaddr=0,s_araddr=0; reg s_awvalid=0,s_wvalid=0,s_bready=0,s_arvalid=0,s_rready=0;
    reg [31:0] s_wdata=0; reg [3:0] s_wstrb=0;
    wire s_awready,s_wready,s_arready; wire [1:0] s_bresp,s_rresp; wire s_bvalid,s_rvalid; wire [31:0] s_rdata;
    wire [11:0] m_awaddr,m_araddr; wire m_awvalid,m_wvalid,m_bready,m_arvalid,m_rready;
    wire [31:0] m_wdata; wire [3:0] m_wstrb;
    reg m_awready=0,m_wready=0,m_bvalid=0,m_arready=0,m_rvalid=0;
    reg [1:0] m_bresp=0,m_rresp=0; reg [31:0] m_rdata=0;
    always #5 s_clk=~s_clk;
    always #13 m_clk=~m_clk;
    cop_axi_lite_cdc dut(.s_clk(s_clk),.s_rst_n(s_rst_n),.s_awaddr(s_awaddr),.s_awvalid(s_awvalid),
        .s_awready(s_awready),.s_wdata(s_wdata),.s_wstrb(s_wstrb),.s_wvalid(s_wvalid),.s_wready(s_wready),
        .s_bresp(s_bresp),.s_bvalid(s_bvalid),.s_bready(s_bready),.s_araddr(s_araddr),
        .s_arvalid(s_arvalid),.s_arready(s_arready),.s_rdata(s_rdata),.s_rresp(s_rresp),
        .s_rvalid(s_rvalid),.s_rready(s_rready),.m_clk(m_clk),.m_rst_n(m_rst_n),
        .m_awaddr(m_awaddr),.m_awvalid(m_awvalid),.m_awready(m_awready),.m_wdata(m_wdata),
        .m_wstrb(m_wstrb),.m_wvalid(m_wvalid),.m_wready(m_wready),.m_bresp(m_bresp),
        .m_bvalid(m_bvalid),.m_bready(m_bready),.m_araddr(m_araddr),.m_arvalid(m_arvalid),
        .m_arready(m_arready),.m_rdata(m_rdata),.m_rresp(m_rresp),.m_rvalid(m_rvalid),.m_rready(m_rready));
    initial begin
        repeat(4) @(negedge s_clk); s_rst_n=1;
        repeat(3) @(negedge m_clk); m_rst_n=1;
        @(negedge m_clk);
        if(m_awaddr!==0 || m_wdata!==0 || m_wstrb!==0 || m_araddr!==0) $fatal(1,"m payload reset missing");

        @(negedge s_clk); s_awaddr=12'h16c; s_wdata=32'ha53c09e1; s_wstrb=4'b0101;
        s_awvalid=1; s_wvalid=1;
        while(!(s_awready && s_wready)) @(negedge s_clk);
        @(negedge s_clk); s_awvalid=0; s_wvalid=0;
        while(!(m_awvalid && m_wvalid)) @(negedge m_clk);
        if(m_awaddr!==12'h16c || m_wdata!==32'ha53c09e1 || m_wstrb!==4'b0101) $fatal(1,"write payload mismatch");
        if(m_awaddr===12'hfff || m_wdata===32'hffffffff || m_wstrb===4'hf) $fatal(1,"write payload folded to ones");
        m_awready=1; m_wready=1; @(negedge m_clk); m_awready=0; m_wready=0;
        while(!m_bready) @(negedge m_clk);
        m_bresp=2'b00; m_bvalid=1; @(negedge m_clk); m_bvalid=0;
        while(!s_bvalid) @(negedge s_clk);
        if(s_bresp!==0) $fatal(1,"write response mismatch");
        s_bready=1; @(negedge s_clk); s_bready=0;

        s_araddr=12'h2a4; s_arvalid=1;
        while(!s_arready) @(negedge s_clk);
        @(negedge s_clk); s_arvalid=0;
        while(!m_arvalid) @(negedge m_clk);
        if(m_araddr!==12'h2a4 || m_araddr===12'hfff) $fatal(1,"read address mismatch or folded to ones");
        m_arready=1; @(negedge m_clk); m_arready=0;
        while(!m_rready) @(negedge m_clk);
        m_rdata=32'hc001d00d; m_rresp=0; m_rvalid=1; @(negedge m_clk); m_rvalid=0;
        while(!s_rvalid) @(negedge s_clk);
        if(s_rdata!==32'hc001d00d || s_rresp!==0) $fatal(1,"read response mismatch");
        s_rready=1; @(negedge s_clk); s_rready=0;
        $display("PASS: axi_lite_cdc reset plus write/read payload cross intact; no all-ones folding");
        $finish;
    end
    initial begin #20000; $fatal(1,"axi_lite_cdc timeout"); end
endmodule
