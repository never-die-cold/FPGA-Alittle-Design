`timescale 1ns/1ps
module tb_cop_top;
    reg core_clk=0,cop_clk=0,rst_n=0,we=0; reg [31:0] addr=0,wdata=0; reg [3:0] be=4'hf;
    wire hit,start; wire [31:0] rdata,status,counts,decision; wire [3:0] index;
    reg ps_valid=0,dma_start=0,dma_valid=0,dma_last=0,dma_kind=0;
    reg [11:0] ps_offset; reg [31:0] ps_data; wire ps_done,ps_error,dma_ready,store_write;
    integer starts=0;
    always #5 core_clk=~core_clk; always #7 cop_clk=~cop_clk;
    always @(posedge cop_clk) if(start) starts=starts+1;
    cop_top dut(.core_clk(core_clk),.cop_clk(cop_clk),.rst_n(rst_n),.core_addr_i(addr),
        .core_wdata_i(wdata),.core_be_i(be),.core_we_i(we),.core_hit_o(hit),.core_rdata_o(rdata),
        .ps_write_valid_i(ps_valid),.ps_write_offset_i(ps_offset),.ps_write_data_i(ps_data),
        .ps_write_strb_i(4'hf),.ps_write_done_o(ps_done),.ps_slverr_o(ps_error),
        .dma_start_i(dma_start),.dma_kind_i(dma_kind),.dma_data_i(64'd0),.dma_keep_i(8'hff),
        .dma_valid_i(dma_valid),.dma_last_i(dma_last),.store_ready_i(1'b1),.dma_ready_o(dma_ready),
        .store_write_o(store_write),
        .task_ready_i(1'b1),.task_busy_i(1'b0),.task_done_i(1'b0),.task_error_i(1'b0),
        .task_timeout_i(1'b0),
        .irq_pending_i(1'b0),.task_start_o(start),.status_o(status),.fw_counts_o(counts),
        .fw_decision_o(decision),.result_index_o(index));
    task ps_wr; input [11:0] a; input [31:0] d;
        begin @(negedge cop_clk); ps_offset=a; ps_data=d; ps_valid=1; @(posedge cop_clk); #1;
            if(!ps_done || ps_error) $fatal(1); @(negedge cop_clk); ps_valid=0; end
    endtask
    initial begin
        repeat(3) @(negedge core_clk); rst_n=1;
        ps_wr(12'h01c,1); ps_wr(12'h024,32'h1234); ps_wr(12'h02c,1); ps_wr(12'h030,1000);
        ps_wr(12'h048,32'h1000); ps_wr(12'h04c,8); ps_wr(12'h050,32'h2000);
        ps_wr(12'h054,32'h3000); ps_wr(12'h058,4096); ps_wr(12'h05c,32'h4000);
        ps_wr(12'h060,16); ps_wr(12'h064,0); ps_wr(12'h068,1);
        @(negedge cop_clk); dma_start=1; @(negedge cop_clk); dma_start=0; dma_valid=1; dma_last=1;
        @(posedge cop_clk); #1; dma_valid=0; dma_last=0;
        @(posedge cop_clk); #1;
        if(!dut.model_valid || dut.dma_bytes!=8) $fatal(1);
        addr=32'h8001000c; wdata=1; we=1;
        @(negedge core_clk); we=0; wait(starts==1); wait(!dut.mailbox_pending);
        addr=32'h80010010; #1;
        if(!hit || starts!=1 || rdata[10] || !rdata[0]) $fatal(1);
        $display("PASS: cop_top commits config, loads one model packet, crosses START and drains ACK"); $finish;
    end
    initial begin #3000; $fatal(1,"cop_top timeout"); end
endmodule
