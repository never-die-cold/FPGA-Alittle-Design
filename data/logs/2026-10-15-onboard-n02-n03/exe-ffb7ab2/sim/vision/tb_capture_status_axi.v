`timescale 1ns/1ps
module tb_capture_status_axi;
    reg clk=0,pclk=0,pclock_run=1,rst=0,locked=0,overflow=0;
    always #5 clk=~clk;
    always #7 if(pclock_run) pclk=~pclk;
    reg [15:0] awaddr=0,araddr=0;
    reg awvalid=0,wvalid=0,bready=0,arvalid=0,rready=0;
    reg valid=0,ready=1,sof=0,eol=0;
    reg [23:0] raw=24'h112233;
    wire awready,wready,bvalid,arready,rvalid,pixel_reset;
    wire [1:0] bresp,rresp;
    wire [31:0] rdata;
    wire [23:0] rgb;
    capture_status_axi #(.WIDTH(4),.HEIGHT(3)) dut(
        .s_axi_aclk(clk),.s_axi_aresetn(rst),
        .s_axi_awaddr(awaddr),.s_axi_awprot(3'd0),.s_axi_awvalid(awvalid),.s_axi_awready(awready),
        .s_axi_wdata(32'hffffffff),.s_axi_wstrb(4'hf),.s_axi_wvalid(wvalid),.s_axi_wready(wready),
        .s_axi_bvalid(bvalid),.s_axi_bready(bready),.s_axi_bresp(bresp),
        .s_axi_araddr(araddr),.s_axi_arprot(3'd0),.s_axi_arvalid(arvalid),.s_axi_arready(arready),
        .s_axi_rdata(rdata),.s_axi_rvalid(rvalid),.s_axi_rready(rready),.s_axi_rresp(rresp),
        .pclk(pclk),.video_locked(locked),.pixel_overflow(overflow),.raw_rbg(raw),
        .native_rgb(rgb),.pixel_reset(pixel_reset),
        .stream_tdata(24'd0),.stream_tvalid(valid),.stream_tready(ready),.stream_tuser(sof),.stream_tlast(eol));
    task check;
        input condition; input [511:0] label;
        begin if(!condition) begin $display("FAIL: %0s",label); $fatal(1); end end
    endtask
    task beat;
        input s,l;
        begin @(negedge clk); valid=1; sof=s; eol=l;
            @(posedge clk); #1;
            @(negedge clk); valid=0; sof=0; eol=0; end
    endtask
    task frame;
        integer row,col;
        begin for(row=0;row<3;row=row+1) for(col=0;col<4;col=col+1)
            beat(row==0 && col==0,col==3); end
    endtask
    task read;
        input [15:0] address; input [31:0] expected; input [1:0] response;
        integer hold;
        begin @(negedge clk); araddr=address; arvalid=1;
            @(posedge clk); #1; check(rvalid && rdata==expected && rresp==response,"CSR read");
            @(negedge clk); arvalid=0; araddr=16'hffff;
            for(hold=0;hold<3;hold=hold+1) begin
                @(posedge clk); #1; check(!arready && rvalid && rdata==expected && rresp==response,"read stable under backpressure");
            end
            @(negedge clk); rready=1; @(posedge clk); #1;
            @(negedge clk); rready=0; check(!rvalid,"read consumed");
        end
    endtask
    task write_rejected;
        input data_first;
        begin @(negedge clk); if(data_first) wvalid=1; else awvalid=1;
            @(posedge clk); #1; check(!bvalid,"wait for both write channels");
            @(negedge clk); wvalid=0; awvalid=0;
            repeat(3) @(negedge clk);
            if(data_first) awvalid=1; else wvalid=1;
            @(posedge clk); #1; check(bvalid && bresp==2,"read-only write rejected");
            @(negedge clk); wvalid=0; awvalid=0;
            repeat(3) begin @(posedge clk); #1; check(bvalid && !awready && !wready,"write response retained"); end
            @(negedge clk); bready=1; @(posedge clk); #1;
            @(negedge clk); bready=0;
        end
    endtask
    initial begin
        #1; rst=0; repeat(2) @(negedge clk); rst=1;
        #1; check(rgb==24'h113322,"RBG to DDR BGR byte order");
        raw=24'hff0000; #1; check(rgb==24'hff0000,"red lane");
        raw=24'h0000ff; #1; check(rgb==24'h00ff00,"green lane");
        raw=24'h00ff00; #1; check(rgb==24'h0000ff,"blue lane");
        read(0,32'h43415031,0); read(16'h14,4,0); read(16'h18,3,0);
        read(16'h24,0,2); read(16'h0001,0,2); read(16'h0100,0,2);
        write_rejected(0); write_rejected(1); read(0,32'h43415031,0);
        locked=1; repeat(5) @(negedge clk); check(!pixel_reset,"pixel reset release");
        read(4,1,0);
        frame(); read(8,1,0); beat(1,0); read(4,3,0);
        // One short overflow survives a stopped source clock until destination acknowledgement.
        @(negedge pclk); overflow=1; @(posedge pclk); #1; overflow=0; pclock_run=0;
        repeat(8) @(negedge clk); read(16'h1c,1,0); read(16'h10,1,0);
        read(16'hc,1,0); read(8,1,0);
        pclock_run=1; repeat(20) @(negedge clk); read(4,9,0);
        frame(); read(8,2,0);
        @(negedge pclk); overflow=1; repeat(12) @(negedge clk);
        read(16'h1c,2,0); read(16'h10,2,0);
        overflow=0; repeat(20) @(negedge clk);
        locked=0; #1; check(pixel_reset,"lock loss asynchronously asserts pixel reset");
        repeat(8) @(negedge clk); read(16'h20,1,0); read(16'h10,3,0);
        // Status bus remains responsive with no pixel clock or video lock.
        pclock_run=0; read(0,32'h43415031,0); read(4,8,0);
        @(negedge clk); rst=0; #1; check(!rvalid && !bvalid,"bus reset clears responses");
        $display("PASS: capture CSR, split writes, backpressure, color lanes, fault CDC and clock/lock loss"); $finish;
    end
    initial begin #100000; $display("FAIL: watchdog"); $fatal(1); end
endmodule
