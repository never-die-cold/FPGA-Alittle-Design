`timescale 1ns/1ps
module tb_cop_top;
    reg core_clk=0,cop_clk=0,rst_n=0,we=0; reg [31:0] addr=0,wdata=0; reg [3:0] be=4'hf;
    wire hit,start; wire [31:0] rdata,status,counts,decision; wire [3:0] index;
    integer starts=0;
    always #5 core_clk=~core_clk; always #7 cop_clk=~cop_clk;
    always @(posedge cop_clk) if(start) starts=starts+1;
    cop_top dut(.core_clk(core_clk),.cop_clk(cop_clk),.rst_n(rst_n),.core_addr_i(addr),
        .core_wdata_i(wdata),.core_be_i(be),.core_we_i(we),.core_hit_o(hit),.core_rdata_o(rdata),
        .task_ready_i(1'b1),.task_busy_i(1'b0),.task_done_i(1'b0),.task_error_i(1'b0),
        .task_timeout_i(1'b0),.cfg_valid_i(1'b1),.model_valid_i(1'b1),.dma_busy_i(1'b0),
        .irq_pending_i(1'b0),.task_start_o(start),.status_o(status),.fw_counts_o(counts),
        .fw_decision_o(decision),.result_index_o(index));
    initial begin
        repeat(3) @(negedge core_clk); rst_n=1; addr=32'h8001000c; wdata=1; we=1;
        @(negedge core_clk); we=0; wait(starts==1); wait(!dut.mailbox_pending);
        addr=32'h80010010; #1;
        if(!hit || starts!=1 || rdata[10] || !rdata[0]) $fatal(1);
        $display("PASS: cop_top carries one core START through CDC and drains ACK"); $finish;
    end
    initial begin #3000; $fatal(1,"cop_top timeout"); end
endmodule
