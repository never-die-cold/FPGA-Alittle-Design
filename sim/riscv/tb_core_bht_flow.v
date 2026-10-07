`timescale 1ns/1ps
module tb_core_bht_flow;
    parameter [1:0] BHT_MODE = 2'd2;
    reg clk=0, rst_n=0; reg [31:0] imem_rdata;
    wire [31:0] imem_addr, dmem_addr, dmem_wdata, dmem_rdata;
    wire [3:0] dmem_be; wire dmem_we;
    reg [31:0] imem [0:8191], dmem [0:8191];
    integer i, cycles=0, resolves=0, lookups=0, hits=0, misses=0;
    integer mispredicts=0, writes=0, x10_writes=0, starts=0, errors=0;
    reg invalid_to_mem, flushed;
    always #5 clk=~clk;
    always @(posedge clk) imem_rdata <= imem[imem_addr[14:2]];
    assign dmem_rdata=dmem[dmem_addr[14:2]];
    core_top #(.ENABLE_FORWARDING(1'b1), .BHT_MODE(BHT_MODE)) dut (
        .clk(clk),.rst_n(rst_n),.imem_addr(imem_addr),.imem_rdata(imem_rdata),
        .dmem_addr(dmem_addr),.dmem_wdata(dmem_wdata),.dmem_be(dmem_be),
        .dmem_we(dmem_we),.dmem_rdata(dmem_rdata));
    always @(posedge clk) if (rst_n) begin
        invalid_to_mem=!dut.instr_valid;
        flushed=dut.flush;
        if (!dut.instr_valid && (dut.muldiv_start || dut.redirect ||
            dut.branch_resolve || dut.mem_in_valid || dut.bp_lookup_event))
            $fatal(1,"FAIL: invalid IF payload produced an EX side effect");
        #1;
        if (invalid_to_mem && (dut.mem_valid || dut.rf_we || dmem_we))
            $fatal(1,"FAIL: invalid payload reached architectural commit");
        if (flushed && dut.instr_valid !== 1'b0)
            $fatal(1,"FAIL: redirect did not invalidate the young slot");
    end
    always @(posedge clk) if (rst_n) begin
        cycles=cycles+1;
        if (dut.branch_resolve) begin
            resolves=resolves+1;
            if (dut.branch_mispredict) begin
                mispredicts=mispredicts+1;
                if (imem_addr !== (dut.branch_taken ? dut.redirect_target : dut.pc_id+4)) begin $display("FAIL: wrong recovery address"); errors=errors+1; end
            end
            if (dut.flush !== dut.branch_mispredict) begin $display("FAIL: branch flush != mispredict"); errors=errors+1; end
            if (dut.bp_predict_taken && !dut.branch_mispredict && dut.flush) begin $display("FAIL: correct taken prediction flushed"); errors=errors+1; end
        end
        if (dut.bp_lookup_event) begin
            lookups=lookups+1;
            if (dut.bp_miss_event) begin
                misses=misses+1;
            end else if (dut.bp_hit_event) hits=hits+1;
        end
        if (dut.bp_hit_event && dut.bp_miss_event) begin $display("FAIL: hit and miss overlap"); errors=errors+1; end
        if (dut.bp_lookup_event !== (dut.bp_hit_event || dut.bp_miss_event)) begin $display("FAIL: event accounting"); errors=errors+1; end
        if (dut.rf_we && dut.mem_rd==5'd10) x10_writes=x10_writes+1;
        if (dut.muldiv_start) starts=starts+1;
        if (dmem_we) begin
            writes=writes+1;
            if (dmem_be[0]) dmem[dmem_addr[14:2]][7:0]<=dmem_wdata[7:0];
            if (dmem_be[1]) dmem[dmem_addr[14:2]][15:8]<=dmem_wdata[15:8];
            if (dmem_be[2]) dmem[dmem_addr[14:2]][23:16]<=dmem_wdata[23:16];
            if (dmem_be[3]) dmem[dmem_addr[14:2]][31:24]<=dmem_wdata[31:24];
        end
    end
    initial begin
        imem_rdata=32'h00000013;
        for(i=0;i<8192;i=i+1) begin imem[i]=32'h00000013; dmem[i]=0; end
        imem[0]=32'h00000093; // addi x1,x0,0
        imem[1]=32'h00500113; // addi x2,x0,5
        imem[2]=32'h00000513; // addi x10,x0,0
        imem[3]=32'h00108093; // store loop: addi x1,x1,1
        imem[4]=32'hfe20cee3; // blt x1,x2,-4: T,T,T,T,N
        imem[5]=32'h00102023; // sw x1,0(x0): legal only after final N
        imem[6]=32'h00000093; // addi x1,x0,0
        imem[7]=32'h00108093; // reg-write loop
        imem[8]=32'hfe20cee3; // blt x1,x2,-4
        imem[9]=32'h00150513; // addi x10,x10,1: legal once
        imem[10]=32'h00000093; // addi x1,x0,0
        imem[11]=32'h00700193; // addi x3,x0,7
        imem[12]=32'h00300213; // addi x4,x0,3
        imem[13]=32'h00108093; // mul loop
        imem[14]=32'hfe20cee3; // blt x1,x2,-4
        imem[15]=32'h024185b3; // mul x11,x3,x4: legal once
        imem[16]=32'h00a02223; // sw x10,4(x0)
        imem[17]=32'h00b02423; // sw x11,8(x0)
        imem[18]=32'h0000006f; // stop loop
        repeat(4) @(posedge clk); rst_n=1;
        while(writes<3 && cycles<300) @(posedge clk);
        @(posedge clk); #1;
        if(resolves!=15 || writes!=3 || x10_writes!=2 || starts!=1 ||
           dmem[0]!==5 || dmem[1]!==1 || dmem[2]!==21) begin
            $display("FAIL: resolve/write/x10/start/data=%0d/%0d/%0d/%0d/%0d,%0d,%0d",resolves,writes,x10_writes,starts,dmem[0],dmem[1],dmem[2]); errors=errors+1;
        end
        if((BHT_MODE==0 && (lookups!=0 || hits!=0 || misses!=0 || mispredicts!=12)) ||
           (BHT_MODE==1 && (lookups!=15 || hits!=9 || misses!=6)) ||
           (BHT_MODE==2 && (lookups!=15 || hits!=6 || misses!=9))) begin
            $display("FAIL: mode/lookup/hit/miss/mispredict=%0d/%0d/%0d/%0d/%0d",BHT_MODE,lookups,hits,misses,mispredicts); errors=errors+1;
        end
        if(errors==0) $display("PASS: BHT mode %0d, wrong-path store/RF/muldiv suppressed",BHT_MODE);
        else $fatal(1,"FAIL: BHT flow errors=%0d",errors);
        $finish;
    end
endmodule
