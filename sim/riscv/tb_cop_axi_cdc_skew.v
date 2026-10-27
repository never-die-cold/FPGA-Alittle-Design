`timescale 1ns/1ps
// Model payload capture one s_clk later than ack; repeat distinct addresses.
module tb_cop_axi_cdc_skew;
    reg s_clk=0,m_clk=0,s_rst_n=0,m_rst_n=0;
    reg [11:0] araddr=0; reg arvalid=0,rready=0;
    wire arready,rvalid; wire [31:0] rdata; wire [1:0] rresp;
    wire [11:0] m_araddr; wire m_arvalid,m_rready;
    reg [31:0] m_rdata=0; reg [1:0] m_rresp=0; reg m_rvalid=0;
    reg [31:0] delayed0=0,delayed1=0;
    reg [1:0] resp0=0,resp1=0;
    integer n;
    always #5 s_clk=~s_clk;
    always #12.5 m_clk=~m_clk;
    cop_axi_lite_cdc dut(.s_clk(s_clk),.s_rst_n(s_rst_n),
        .s_awaddr(12'd0),.s_awvalid(1'b0),.s_awready(),
        .s_wdata(32'd0),.s_wstrb(4'd0),.s_wvalid(1'b0),.s_wready(),
        .s_bresp(),.s_bvalid(),.s_bready(1'b1),
        .s_araddr(araddr),.s_arvalid(arvalid),.s_arready(arready),
        .s_rdata(rdata),.s_rresp(rresp),.s_rvalid(rvalid),.s_rready(rready),
        .m_clk(m_clk),.m_rst_n(m_rst_n),.m_awaddr(),.m_awvalid(),.m_awready(1'b1),
        .m_wdata(),.m_wstrb(),.m_wvalid(),.m_wready(1'b1),
        .m_bresp(2'd0),.m_bvalid(1'b0),.m_bready(),
        .m_araddr(m_araddr),.m_arvalid(m_arvalid),.m_arready(1'b1),
        .m_rdata(m_rdata),.m_rresp(m_rresp),.m_rvalid(m_rvalid),.m_rready(m_rready));
    always @(posedge m_clk) begin
        if(!m_rst_n) begin m_rvalid<=0; m_rdata<=0; m_rresp<=0; end
        else if(m_arvalid) begin
            m_rdata<=32'ha5000000 | m_araddr;
            m_rresp<=m_araddr[2] ? 2'b10 : 2'b00;
            m_rvalid<=1;
        end else if(m_rready) m_rvalid<=0;
    end
    always @(posedge s_clk) begin
        delayed0<=dut.rdata_hold; delayed1<=delayed0;
        resp0<=dut.rresp_hold; resp1<=resp0;
    end
    initial begin
        force dut.rdata_s1=delayed1;
        force dut.rresp_s1=resp1;
        repeat(5) @(negedge s_clk); s_rst_n=1; m_rst_n=1;
        for(n=0;n<8;n=n+1) begin
            @(negedge s_clk); araddr=n*4; arvalid=1;
            while(!arready) @(negedge s_clk);
            @(negedge s_clk); arvalid=0;
            while(!rvalid) @(negedge s_clk);
            repeat(3) begin
                if(rdata!==(32'ha5000000 | (n*4)) || rresp!==(n[0] ? 2'b10 : 2'b00))
                    $fatal(1,"CDC stale response address=%h got=%h resp=%h",araddr,rdata,rresp);
                @(negedge s_clk);
            end
            rready=1; @(negedge s_clk); rready=0;
        end
        $display("PASS: CDC delayed payload matches 8 addresses and survives response backpressure");
        $finish;
    end
    initial begin #20000; $fatal(1,"CDC skew test timeout"); end
endmodule
