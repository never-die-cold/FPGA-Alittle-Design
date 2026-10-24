`timescale 1ns/1ps
module tb_cop_firmware_e2e;
    parameter FIRMWARE_HEX="src/riscv_fw/cop_job.hex";
    reg clk=0,rst_n=0,ps_we=0,busy=0,accepted_evt=0,done_evt=0;
    reg [11:0] ps_offset=0; reg [31:0] ps_data=0,seq=0; reg [3:0] delay_count=0;
    reg [1023:0] golden_file; integer fd,fields,cycles=0,seq_reads=0;
    integer golden_class,golden_margin,golden_score,golden_low,golden_threshold;
    reg saw_start=0,saw_accepted=0,saw_terminal=0,saw_meta=0;
    wire [3:0] led,be,result_index; wire cop_hit,cop_we,gate_hit,request,start;
    wire [11:0] offset; wire [31:0] cop_addr,cop_wdata,cop_rdata,request_data,status;
    wire [31:0] fw_counts,fw_decision,error_code; wire [127:0] result_data;
    wire accepted,done,error,timeout,result_valid,unconsumed;
    always #5 clk=~clk;
    assign result_data={32'd472593,16'd0,1'b0,golden_score[14:0],golden_margin[7:0],
        24'h04fd02,5'd0,1'b0,golden_low[0],1'b1,6'd0,golden_class[1:0],16'h1234};
    soc_top #(.IMEM_INIT_FILE(FIRMWARE_HEX),.DMEM_INIT_FILE(FIRMWARE_HEX),.ENABLE_COP(1)) dut(
        .clk(clk),.rst_n(rst_n),.led(led),.cop_rdata_i(cop_rdata),.cop_hit_o(cop_hit),
        .cop_we_o(cop_we),.cop_addr_o(cop_addr),.cop_wdata_o(cop_wdata),.cop_be_o(be));
    cop_core_mmio_gate gate(.addr_i(cop_addr),.wdata_i(cop_wdata),.status_i(status),.be_i(be),.we_i(cop_we),
        .fw_counts_i(fw_counts),.fw_decision_i(fw_decision),.result_index_i(result_index),
        .result_data_i(result_data),.result_seq_i(seq),.cfg_applied_i(32'd1),.dma_bytes_i(32'd4096),
        .work_order_i(32'h0a010000),.roi_count_i(5'd1),.busy_i(busy),.mailbox_pending_i(1'b0),
        .cop_hit_o(gate_hit),.write_request_o(request),.write_offset_o(offset),
        .write_data_o(request_data),.rdata_o(cop_rdata));
    cop_ctrl_regs regs(.clk(clk),.rst_n(rst_n),.write_valid_i(request||ps_we),
        .write_offset_i(ps_we?ps_offset:offset),.write_data_i(ps_we?ps_data:request_data),
        .task_busy_i(busy),.task_accepted_i(accepted_evt),.task_done_i(done_evt),
        .task_error_i(1'b0),.task_timeout_i(1'b0),.cfg_valid_i(1'b1),.model_valid_i(1'b1),
        .dma_busy_i(1'b0),.irq_pending_i(1'b0),.start_pulse_o(start),.abort_pulse_o(),
        .soft_reset_pulse_o(),.write_done_o(),.accepted_o(accepted),.done_o(done),.error_o(error),
        .timeout_o(timeout),.result_valid_o(result_valid),.error_code_o(error_code),
        .result_index_o(result_index),.fw_counts_o(fw_counts),.fw_decision_o(fw_decision),
        .unconsumed_o(unconsumed),.status_o(status));
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n) begin busy<=0; accepted_evt<=0; done_evt<=0; delay_count<=0; seq<=0; end
        else begin
            accepted_evt<=0; done_evt<=0;
            if(start) begin busy<=1; accepted_evt<=1; delay_count<=5; saw_start<=1; end
            else if(busy && delay_count!=0) delay_count<=delay_count-1'b1;
            else if(busy) begin busy<=0; done_evt<=1; seq<=seq+1'b1; end
        end
    end
    always @(posedge clk) if(rst_n && cop_hit && !cop_we) begin
        if(cop_addr[11:0]==12'h010 && status[11]) saw_accepted<=1;
        if(cop_addr[11:0]==12'h010 && status[2]) saw_terminal<=1;
        if(cop_addr[11:0]==12'h070) saw_meta<=1;
        if(cop_addr[11:0]==12'h07c) seq_reads=seq_reads+1;
    end
    task consume; begin @(negedge clk); ps_offset=12'h00c; ps_data=32'h40; ps_we=1;
        @(posedge clk); #1; ps_we=0; end endtask
    initial begin
        if(!$value$plusargs("golden=%s",golden_file)) $fatal(1,"missing +golden");
        fd=$fopen(golden_file,"r"); fields=$fscanf(fd,"%d %d %d %d %d\n",golden_class,
            golden_margin,golden_score,golden_low,golden_threshold); $fclose(fd);
        if(fields!=5 || golden_class!=2 || golden_margin!=2 || golden_score!=258 || !golden_low) $fatal(1);
        repeat(5) @(posedge clk); rst_n=1;
        while(dut.u_dmem.mem[12'hffc]!==32'h4a303403 && cycles<200000) begin
            @(posedge clk); cycles=cycles+1;
        end
        if(cycles>=200000 || !saw_start || !saw_accepted || !saw_terminal || !saw_meta || seq_reads<3) begin
            $display("FAIL cycles=%0d start=%b accepted=%b terminal=%b meta=%b seq_reads=%0d tohost=%h status=%h",
                cycles,saw_start,saw_accepted,saw_terminal,saw_meta,seq_reads,dut.u_dmem.mem[12'hffc],status);
            $fatal(1);
        end
        if(seq!=1 || fw_counts!==32'h00010000 || fw_decision!==32'h00010403 || !unconsumed) begin
            $display("FAIL seq=%0d counts=%h decision=%h unconsumed=%b status=%h",
                seq,fw_counts,fw_decision,unconsumed,status); $fatal(1);
        end
        consume(); #1;
        if(accepted || done || error || timeout || result_valid || unconsumed || error_code || seq!=1) $fatal(1);
        $display("PASS: firmware_e2e CPU START/ACCEPTED/DONE/RESULT_META/RESULT_SEQ/FW writes + PS CONSUME; J02 zero=2/2/258/1");
        $finish;
    end
endmodule
