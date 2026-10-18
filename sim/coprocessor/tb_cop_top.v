`timescale 1ns/1ps
module tb_cop_top;
    reg core_clk=0,cop_clk=0,rst_n=0,we=0; reg [31:0] addr=0,wdata=0; reg [3:0] be=4'hf;
    wire hit,start,result_write; wire [31:0] rdata,status,counts,decision,result_seq;
    wire [3:0] index,task_index; wire [127:0] result_data;
    reg ps_valid=0,dma_start=0,dma_valid=0,dma_last=0,dma_kind=0;
    reg [11:0] ps_offset; reg [31:0] ps_data; wire ps_done,ps_error,dma_ready,store_write;
    integer starts=0,beat;
    always #5 core_clk=~core_clk; always #7 cop_clk=~cop_clk;
    always @(posedge cop_clk) if(start) starts=starts+1;
    cop_top dut(.core_clk(core_clk),.cop_clk(cop_clk),.rst_n(rst_n),.core_addr_i(addr),
        .core_wdata_i(wdata),.core_be_i(be),.core_we_i(we),.core_hit_o(hit),.core_rdata_o(rdata),
        .ps_write_valid_i(ps_valid),.ps_write_offset_i(ps_offset),.ps_write_data_i(ps_data),
        .ps_write_strb_i(4'hf),.ps_write_done_o(ps_done),.ps_slverr_o(ps_error),
        .dma_start_i(dma_start),.dma_kind_i(dma_kind),.dma_data_i(64'd0),.dma_keep_i(8'hff),
        .dma_valid_i(dma_valid),.dma_last_i(dma_last),.store_ready_i(1'b1),.dma_ready_o(dma_ready),
        .store_write_o(store_write),.target_id_i(16'h1234),.memory_data_i(64'd0),
        .weight_data_i(1024'd0),.bias_data_i(512'd0),.multiplier_data_i({16{32'd1}}),
        .shift_data_i(96'd0),
        .irq_pending_i(1'b0),.engine_start_o(start),.result_write_o(result_write),
        .task_result_index_o(task_index),.result_seq_o(result_seq),.result_data_o(result_data),
        .status_o(status),.fw_counts_o(counts),
        .fw_decision_o(decision),.result_index_o(index));
    task ps_wr; input [11:0] a; input [31:0] d;
        begin @(negedge cop_clk); ps_offset=a; ps_data=d; ps_valid=1; @(posedge cop_clk); #1;
            if(!ps_done || ps_error) $fatal(1); @(negedge cop_clk); ps_valid=0; end
    endtask
    initial begin
        repeat(3) @(negedge core_clk); rst_n=1;
        ps_wr(12'h01c,1); ps_wr(12'h024,32'h1234); ps_wr(12'h02c,1); ps_wr(12'h030,2000000);
        ps_wr(12'h048,32'h1000); ps_wr(12'h04c,8); ps_wr(12'h050,32'h2000);
        ps_wr(12'h054,32'h3000); ps_wr(12'h058,4096); ps_wr(12'h05c,32'h4000);
        ps_wr(12'h060,16); ps_wr(12'h064,0); ps_wr(12'h068,1);
        @(negedge cop_clk); dma_start=1; @(negedge cop_clk); dma_start=0; dma_valid=1; dma_last=1;
        @(posedge cop_clk); #1; dma_valid=0; dma_last=0;
        @(posedge cop_clk); #1;
        if(!dut.model_valid || dut.dma_bytes!=8) $fatal(1);
        @(negedge cop_clk); dma_kind=1; dma_start=1; @(negedge cop_clk); dma_start=0; dma_valid=1;
        for(beat=0;beat<512;beat=beat+1) begin dma_last=beat==511; @(posedge cop_clk); #1; end
        dma_valid=0; dma_last=0; @(posedge cop_clk); #1;
        if(!dut.roi_valid || dut.dma_bytes!=4096) $fatal(1);
        @(negedge core_clk); addr=32'h8001000c; wdata=1; we=1;
        @(negedge core_clk); we=0; wait(starts==1); wait(!dut.mailbox_pending);
        wait(result_seq==1); repeat(2) @(posedge cop_clk); #1;
        if(!result_write && result_seq!=1) $fatal(1);
        if(result_data[15:0]!==16'h1234 || result_data[23:16]!==8'd0 ||
           result_data[55:32]!==24'h000000 || result_data[63:56]!==8'd0) $fatal(1);
        addr=32'h80010010; #1;
        if(!hit || starts!=1 || rdata[10] || !rdata[0]) $fatal(1);
        $display("PASS: cop_top config/load/CDC through active cnn_sequencer to result commit"); $finish;
    end
    initial begin #15000000; $display("TRACE starts=%0d pending=%b cfg=%b model=%b roi=%b busy=%b state=%0d",
        starts,dut.mailbox_pending,dut.cfg_valid,dut.model_valid,dut.roi_valid,dut.task_busy,dut.u_task.state);
        $fatal(1,"cop_top timeout"); end
endmodule
