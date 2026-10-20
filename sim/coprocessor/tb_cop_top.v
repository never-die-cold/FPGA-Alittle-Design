`timescale 1ns/1ps
module tb_cop_top;
    reg core_clk=0,cop_clk=0,rst_n=0,we=0; reg [31:0] addr=0,wdata=0; reg [3:0] be=4'hf;
    wire hit,start,result_write; wire [31:0] rdata,status,counts,decision,result_seq;
    wire [3:0] index,task_index; wire [127:0] result_data;
    reg awvalid=0,wvalid=0,bready=0,arvalid=0,rready=0;
    reg dma_start=0,dma_valid=0,dma_last=0,dma_kind=0;
    reg [11:0] awaddr,araddr; reg [31:0] axi_wdata;
    wire awready,wready,bvalid,arready,rvalid,dma_ready,store_write; wire [31:0] axi_rdata;
    wire [1:0] bresp,rresp;
    reg [63:0] memory_data; reg [1023:0] weight_data;
    reg [511:0] bias_data,multiplier_data; reg [95:0] shift_data;
    reg [7:0] roi [0:4095]; reg [63:0] ping [0:4095],pong [0:2047],gap [0:7];
    reg [1023:0] weights [0:268]; reg [31:0] biases [0:159],multipliers [0:159];
    reg [5:0] shifts [0:159]; reg [4095:0] model_folder,folder,filename;
    wire mem_en,weight_en,param_en,mem_write; wire [1:0] read_bank,write_bank;
    wire [15:0] read_address,weight_address,write_address; wire [7:0] parameter_address;
    wire [63:0] memory_write_data; integer starts=0,beat,lane,found;
    always #5 core_clk=~core_clk; always #7 cop_clk=~cop_clk;
    always @(posedge cop_clk) if(start) starts=starts+1;
    cop_top dut(.core_clk(core_clk),.cop_clk(cop_clk),.rst_n(rst_n),.core_addr_i(addr),
        .core_wdata_i(wdata),.core_be_i(be),.core_we_i(we),.core_hit_o(hit),.core_rdata_o(rdata),
        .s_axi_awaddr_i(awaddr),.s_axi_awvalid_i(awvalid),.s_axi_awready_o(awready),
        .s_axi_wdata_i(axi_wdata),.s_axi_wstrb_i(4'hf),.s_axi_wvalid_i(wvalid),
        .s_axi_wready_o(wready),.s_axi_bresp_o(bresp),.s_axi_bvalid_o(bvalid),.s_axi_bready_i(bready),
        .s_axi_araddr_i(araddr),.s_axi_arvalid_i(arvalid),.s_axi_arready_o(arready),
        .s_axi_rdata_o(axi_rdata),.s_axi_rresp_o(rresp),.s_axi_rvalid_o(rvalid),.s_axi_rready_i(rready),
        .dma_start_i(dma_start),.dma_kind_i(dma_kind),.dma_data_i(64'd0),.dma_keep_i(8'hff),
        .dma_valid_i(dma_valid),.dma_last_i(dma_last),.store_ready_i(1'b1),.dma_ready_o(dma_ready),
        .store_write_o(store_write),.target_id_i(16'h1234),.memory_data_i(memory_data),
        .weight_data_i(weight_data),.bias_data_i(bias_data),.multiplier_data_i(multiplier_data),
        .shift_data_i(shift_data),.memory_enable_o(mem_en),.weight_enable_o(weight_en),
        .parameter_enable_o(param_en),.read_bank_o(read_bank),.write_bank_o(write_bank),
        .read_address_o(read_address),.weight_address_o(weight_address),.write_address_o(write_address),
        .parameter_address_o(parameter_address),.memory_write_o(mem_write),.memory_write_data_o(memory_write_data),
        .irq_pending_i(1'b0),.engine_start_o(start),.result_write_o(result_write),
        .task_result_index_o(task_index),.result_seq_o(result_seq),.result_data_o(result_data),
        .status_o(status),.fw_counts_o(counts),
        .fw_decision_o(decision),.result_index_o(index));
    always @(posedge cop_clk) begin
        if(mem_en) case(read_bank)
            0: memory_data<={56'd0,roi[read_address]};
            1: memory_data<=ping[read_address];
            2: memory_data<=pong[read_address];
            3: memory_data<=gap[read_address];
        endcase
        if(weight_en) weight_data<=weights[weight_address];
        if(param_en) for(lane=0;lane<16;lane=lane+1) begin
            bias_data[lane*32 +: 32]<=biases[parameter_address+lane];
            multiplier_data[lane*32 +: 32]<=multipliers[parameter_address+lane];
            shift_data[lane*6 +: 6]<=shifts[parameter_address+lane];
        end
        if(mem_write) case(write_bank)
            1: ping[write_address]<=memory_write_data;
            2: pong[write_address]<=memory_write_data;
            3: gap[write_address]<=memory_write_data;
        endcase
    end
    task ps_wr; input [11:0] a; input [31:0] d;
        begin @(negedge cop_clk); awaddr=a; axi_wdata=d; awvalid=1; wvalid=1;
            @(negedge cop_clk); awvalid=0; wvalid=0; wait(bvalid);
            if(bresp!=0) $fatal(1); bready=1;
            @(posedge cop_clk); #1; bready=0; end
    endtask
    task ps_rd; input [11:0] a; input [31:0] expected;
        begin @(negedge cop_clk); araddr=a; arvalid=1; @(negedge cop_clk); arvalid=0;
            wait(rvalid); if(rresp!=0 || axi_rdata!==expected) $fatal(1); rready=1;
            @(posedge cop_clk); #1; rready=0; end
    endtask
    initial begin
        found=$value$plusargs("model=%s",model_folder); if(!found) $fatal(1);
        found=$value$plusargs("case=%s",folder); if(!found) $fatal(1);
        $sformat(filename,"%0s/weights.hex",model_folder); $readmemh(filename,weights);
        $sformat(filename,"%0s/bias.hex",model_folder); $readmemh(filename,biases);
        $sformat(filename,"%0s/multipliers.hex",model_folder); $readmemh(filename,multipliers);
        $sformat(filename,"%0s/shifts.hex",model_folder); $readmemh(filename,shifts);
        $sformat(filename,"%0s/input.hex",folder); $readmemh(filename,roi);
        memory_data=0; weight_data=0; bias_data=0; multiplier_data=0; shift_data=0;
        repeat(3) @(negedge core_clk); rst_n=1;
        ps_wr(12'h01c,1); ps_wr(12'h024,32'h1234); ps_wr(12'h028,32'h6522df69);
        ps_wr(12'h02c,1); ps_wr(12'h030,2000000); ps_wr(12'h034,32'h0a010000);
        ps_wr(12'h048,32'h1000); ps_wr(12'h04c,8); ps_wr(12'h050,32'h2000);
        ps_wr(12'h054,32'h3000); ps_wr(12'h058,4096); ps_wr(12'h05c,32'h4000);
        ps_wr(12'h060,16); ps_wr(12'h064,5); ps_wr(12'h068,1);
        // loader 逐字节折 CRC，每拍占多个 cop 拍：按 AXI-Stream 握手驱动，并等置位再断言。
        @(negedge cop_clk); dma_start=1; @(negedge cop_clk); dma_start=0; dma_valid=1; dma_last=1;
        @(posedge cop_clk); while(!dma_ready) @(posedge cop_clk); #1; dma_valid=0; dma_last=0;
        wait(dut.model_valid); #1;
        if(dut.dma_bytes!=8) $fatal(1);
        @(negedge cop_clk); dma_kind=1; dma_start=1; @(negedge cop_clk); dma_start=0;
        for(beat=0;beat<512;beat=beat+1) begin
            dma_last=(beat==511); dma_valid=1;
            @(posedge cop_clk); while(!dma_ready) @(posedge cop_clk); #1; dma_valid=0;
        end
        wait(dut.roi_valid); #1;
        if(dut.dma_bytes!=4096) $fatal(1);
        @(negedge core_clk); addr=32'h8001000c; wdata=1; we=1;
        @(negedge core_clk); we=0; wait(starts==1); wait(!dut.mailbox_pending);
        wait(result_seq==1); repeat(2) @(posedge cop_clk); #1;
        if(!result_write && result_seq!=1) $fatal(1);
        if(result_data[15:0]!==16'h1234 || result_data[23:16]!==8'd2 || !result_data[25] ||
           result_data[55:32]!==24'h04fd02 || result_data[63:56]!==8'd2 ||
           result_data[78:64]!==15'd258) $fatal(1);
        ps_wr(12'h06c,0); ps_rd(12'h034,32'h0a010000);
        ps_rd(12'h07c,1); ps_rd(12'h074,32'h0004fd02);
        repeat(3) @(posedge core_clk); addr=32'h80010070; #1;
        if(rdata[15:0]!==16'h1234 || rdata[23:16]!==8'd2 || !rdata[25]) $fatal(1);
        addr=32'h80010074; #1; if(rdata!==32'h0004fd02) $fatal(1);
        addr=32'h80010078; #1; if(rdata!==32'h00020102) $fatal(1);
        @(negedge core_clk); addr=32'h8001000c; wdata=8; we=1;
        @(negedge core_clk); we=0; wait(!dut.mailbox_pending); repeat(2) @(posedge cop_clk);
        addr=32'h80010010; #1;
        if(!hit || starts!=1 || rdata[10] || !rdata[0] || rdata[2] || rdata[7]) $fatal(1);
        @(negedge cop_clk); dma_kind=1; dma_start=1; @(negedge cop_clk); dma_start=0;
        dma_valid=1; dma_last=1; @(posedge cop_clk); while(!dma_ready) @(posedge cop_clk); #1;
        dma_valid=0; dma_last=0;
        wait(status[3]); #1;   // 短包错误在 CRC 折叠完才置位
        @(negedge core_clk); addr=32'h8001000c; wdata=16; we=1;
        @(negedge core_clk); we=0; wait(!dut.mailbox_pending); repeat(2) @(posedge cop_clk);
        if(status[3]) $fatal(1);
        @(negedge core_clk); wdata=1; we=1; @(negedge core_clk); we=0;
        wait(!dut.mailbox_pending); wait(dut.task_busy);
        repeat(20) @(posedge cop_clk); #1;
        if(!dut.task_busy || dut.u_task.state!=2) begin
            $display("FAIL second task finished early busy=%b state=%0d seq=%0d",
                dut.task_busy,dut.u_task.state,result_seq); $fatal(1);
        end
        ps_wr(12'h00c,2); repeat(2) @(posedge cop_clk); #1;
        if(dut.task_busy || !status[3]) begin
            $display("FAIL abort busy=%b error=%b abort=%b task_error=%b state=%0d",
                dut.task_busy,status[3],dut.abort_command,dut.task_error,dut.u_task.state); $fatal(1);
        end
        ps_wr(12'h00c,4); repeat(2) @(posedge cop_clk); #1;
        if(status[4:2] || result_seq || !dut.model_valid) $fatal(1);
        ps_wr(12'h01c,2); repeat(2) @(posedge cop_clk); #1;
        if(status[5] || !dut.model_valid) $fatal(1);
        ps_wr(12'h068,1); repeat(2) @(posedge cop_clk); #1;
        if(!status[5] || status[6] || dut.roi_valid || status[0]) $fatal(1);
        $display("PASS: cop_top AXI/J02 result, DMA error, ABORT/SOFT_RESET and CFG_VALID revocation"); $finish;
    end
    initial begin #15000000; $display("TRACE starts=%0d pending=%b cfg=%b model=%b roi=%b busy=%b state=%0d",
        starts,dut.mailbox_pending,dut.cfg_valid,dut.model_valid,dut.roi_valid,dut.task_busy,dut.u_task.state);
        $fatal(1,"cop_top timeout"); end
endmodule
