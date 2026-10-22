`timescale 1ns/1ps
module tb_pynq_cop_top;
    reg ps_clk=0,cop_clk=0,ps_rst_n=0,cop_rst_n=0;
    reg [11:0] awaddr=0,araddr=0; reg awvalid=0,wvalid=0,bready=0,arvalid=0,rready=0;
    reg [31:0] wdata=0; reg [3:0] wstrb=0;
    wire awready,wready; wire [1:0] bresp,rresp; wire bvalid,arready,rvalid; wire [31:0] rdata;
    reg [63:0] tdata=0; reg [7:0] tkeep=0; reg tlast=0,tvalid=0,dma_start=0,dma_kind=0;
    wire tready,dma_start_ready,payload_error; wire [3:0] led;
    integer cycles=0;
    always #5 ps_clk=~ps_clk;
    always #12.5 cop_clk=~cop_clk;
    always @(posedge ps_clk) cycles=cycles+1;
    pynq_cop_top dut(.ps_clk_100_i(ps_clk),.ps_rst_n_i(ps_rst_n),.cop_clk_40_i(cop_clk),
        .cop_rst_n_i(cop_rst_n),.s_axi_awaddr_i(awaddr),.s_axi_awvalid_i(awvalid),
        .s_axi_awready_o(awready),.s_axi_wdata_i(wdata),.s_axi_wstrb_i(wstrb),
        .s_axi_wvalid_i(wvalid),.s_axi_wready_o(wready),.s_axi_bresp_o(bresp),
        .s_axi_bvalid_o(bvalid),.s_axi_bready_i(bready),.s_axi_araddr_i(araddr),
        .s_axi_arvalid_i(arvalid),.s_axi_arready_o(arready),.s_axi_rdata_o(rdata),
        .s_axi_rresp_o(rresp),.s_axi_rvalid_o(rvalid),.s_axi_rready_i(rready),
        .s_axis_tdata_i(tdata),.s_axis_tkeep_i(tkeep),.s_axis_tlast_i(tlast),
        .s_axis_tvalid_i(tvalid),.s_axis_tready_o(tready),.dma_start_ps_i(dma_start),
        .dma_kind_ps_i(dma_kind),.dma_start_ready_o(dma_start_ready),
        .payload_error_o(payload_error),.led(led));
    initial begin
        repeat(5) @(negedge ps_clk); ps_rst_n=1;
        repeat(3) @(negedge cop_clk); cop_rst_n=1;
        repeat(4) @(negedge ps_clk);
        araddr=0; arvalid=1;
        while(!arready) @(negedge ps_clk);
        @(negedge ps_clk); arvalid=0; rready=1;
        while(!rvalid) @(negedge ps_clk);
        if(rdata!==32'h434f5030 || rresp!==0) $fatal(1);
        @(negedge ps_clk); rready=0;
        tdata=64'h0123_4567_89ab_cdef; tkeep=8'hff; tlast=1; tvalid=1;
        while(!tready) @(negedge ps_clk);
        @(negedge ps_clk); tvalid=0;
        while(!dut.dma_valid) @(negedge cop_clk);
        if(dut.dma_data!==64'h0123_4567_89ab_cdef || dut.dma_keep!==8'hff || !dut.dma_last) $fatal(1);
        if(payload_error) $fatal(1);
        $display("PASS: pynq_cop_top 100/40MHz AXI-Lite reads COP_ID and AXIS FIFO preserves 73-bit beat; cop_job.hex elaborated");
        $finish;
    end
    initial begin #200000; $display("FAIL: pynq_cop_top timeout cycles=%0d",cycles); $fatal(1); end
endmodule
