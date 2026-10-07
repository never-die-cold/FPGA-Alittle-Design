`timescale 1ns/1ps
// tb_axi_lock_reset —— 锁定丢失时 AXI 在途事务必须照常完成（2026-10-03 上板挂死复现）
// 上板实测：PS 轮询 R12 期间拔 HDMI，video_locked 掉低连带复位 axi_regs，
// BRESP/RRESP 永不返回 → PS 总线挂死（串口/网口同死）。本 tb 定向复现：
//   1) 基线：锁定稳定时写/读正常（约定同 tb_axi_regs：bready/rready 按拍驱动）；
//   2) 写在途：wr_fire 当拍后撤锁（bvalid 已寄存、主机下一沿采样）→ 仍须被采样到；
//   3) 读在途：rd_fire 当拍后撤锁（rvalid 已寄存未采样）→ 仍须被采样到；
//   4) 恢复后 R0 保持写入值（从机复位不得清掉寄存器堆）。
// 判据：响应丢失 = $fatal（上板挂死等价场景）；全过打 PASS。
module tb_axi_lock_reset;
    reg pclk=0,aclk=0,rst_n=0,locked=0;
    always #5 pclk=~pclk;
    always #7 aclk=~aclk;
    reg vs=0,hs=0,de=0;
    reg [23:0] rbg=0;
    wire ovs,ohs,ode;
    wire [23:0] orgb;
    reg awvalid=0,wvalid=0,arvalid=0,bready=0,rready=0;
    reg [31:0] awaddr=0,wdata=0,araddr=0;
    reg [3:0] wstrb=4'hF;
    wire awready,wready,bvalid,arready,rvalid;
    wire [31:0] rdata; wire [1:0] bresp,rresp;
    reg [31:0] rd;
    vision_axi #(.ENABLE_DIAGNOSTIC(1)) dut(.pclk(pclk),.s_axi_aclk(aclk),.s_axi_aresetn(rst_n),.video_locked(locked),
        .raw_vs(vs),.raw_hs(hs),.raw_de(de),.raw_rbg(rbg),
        .video_vs(ovs),.video_hs(ohs),.video_de(ode),.video_rbg(orgb),
        .s_axi_awaddr(awaddr),.s_axi_araddr(araddr),.s_axi_awprot(3'b0),.s_axi_arprot(3'b0),
        .s_axi_awvalid(awvalid),.s_axi_wvalid(wvalid),.s_axi_bready(bready),
        .s_axi_arvalid(arvalid),.s_axi_rready(rready),.s_axi_wdata(wdata),.s_axi_wstrb(wstrb),
        .s_axi_awready(awready),.s_axi_wready(wready),.s_axi_bvalid(bvalid),
        .s_axi_bresp(bresp),.s_axi_arready(arready),.s_axi_rvalid(rvalid),
        .s_axi_rdata(rdata),.s_axi_rresp(rresp));
    always @(negedge pclk) begin vs<=1'b0; hs<=1'b0; de<=1'b1; rbg<=rbg+1; end

    task axi_write(input [31:0] a, input [31:0] d, input integer max_wait);
        integer n;
        begin
            @(negedge aclk);
            awaddr=a; wdata=d; awvalid=1; wvalid=1; bready=1;
            @(posedge aclk);            // 接受 + wr_fire，bvalid 置起
            @(negedge aclk);
            awvalid=0; wvalid=0;
            n=0; while (!bvalid) begin
                if (++n>max_wait) $fatal(1,"bvalid timeout after aw/w accepted (PS hang)");
                @(negedge aclk);
            end
            @(posedge aclk);            // bready=1 清除 bvalid
            @(negedge aclk);
            bready=0;
        end
    endtask

    task axi_read(input [31:0] a, output [31:0] d, input integer max_wait);
        integer n;
        begin
            @(negedge aclk);
            araddr=a; arvalid=1;
            @(posedge aclk);            // rd_fire，rvalid/rdata 置起
            @(negedge aclk);
            arvalid=0;
            n=0; while (!rvalid) begin
                if (++n>max_wait) $fatal(1,"rvalid timeout after rd_fire (PS hang)");
                @(negedge aclk);
            end
            d=rdata;
            rready=1;
            @(posedge aclk);            // rready 清除 rvalid
            @(negedge aclk);
            rready=0;
        end
    endtask

    initial begin
        repeat(3) @(negedge aclk);
        rst_n=1; locked=1;
        repeat(4) @(negedge aclk);
        // 1) 基线
        axi_write(32'h0, 32'h9, 50);
        axi_read(32'h0, rd, 50);
        if (rd !== 32'h9) $fatal(1,"baseline R0 readback wrong: %h", rd);
        $display("INFO baseline write/read ok");
        // 2) 写在途撤锁：wr_fire 已寄存 bvalid，撤锁在主机采样（下一 negedge）前
        @(negedge aclk);
        awaddr=32'h0; wdata=32'h1; awvalid=1; wvalid=1; bready=1;
        @(posedge aclk); #1 locked=0;   // buggy：异步复位在采样前抹掉 bvalid
        @(negedge aclk);
        awvalid=0; wvalid=0;
        begin : w_inflight
            integer n;
            n=0;
            while (!bvalid) begin
                if (++n>50) $fatal(1,"write response lost on lock drop (PS bus hang repro)");
                @(negedge aclk);
            end
        end
        locked=1;
        @(posedge aclk); @(negedge aclk); bready=0;
        $display("INFO in-flight write completed across lock drop");
        // 2b) bready=0 挂起撤锁：bvalid 已寄存未采样，撤锁后必须原样挂起，
        //     恢复锁与 bready 后恰好完成一次（评审补测规格）
        @(negedge aclk);
        awaddr=32'h10; wdata=32'hA5; awvalid=1; wvalid=1; bready=0;
        @(posedge aclk); #1 locked=0;
        @(negedge aclk);
        awvalid=0; wvalid=0;
        begin : w_inflight_noready
            integer n;
            n=0;
            while (!bvalid) begin
                if (++n>50) $fatal(1,"write bvalid lost with bready=0 on lock drop");
                @(negedge aclk);
            end
        end
        locked=1;
        repeat(3) @(negedge aclk);
        if (!bvalid) $fatal(1,"bvalid dropped before bready (lost response)");
        bready=1;
        @(posedge aclk); @(negedge aclk); bready=0;
        $display("INFO bready=0 pending write survived lock drop");
        // 3) 读在途撤锁：rd_fire 已寄存 rvalid，撤锁在主机采样前
        begin : r_inflight
            integer n;
            n=0;
            @(negedge aclk);
            araddr=32'h0; arvalid=1; rready=1;
            @(posedge aclk); #1 locked=0;
            @(negedge aclk);
            arvalid=0;
            while (!rvalid) begin
                if (++n>50) $fatal(1,"read response lost on lock drop (PS bus hang repro)");
                @(negedge aclk);
            end
            rd=rdata;
        end
        locked=1;
        @(posedge aclk); @(negedge aclk); rready=0;
        repeat(4) @(negedge aclk);
        // 4) 恢复后寄存器堆保持：R0 应为步骤 2 写入的 0x1，R4 应为 2b 写入的 0xA5
        axi_read(32'h0, rd, 50);
        if (rd !== 32'h1) $fatal(1,"R0 lost after lock recovery (slave was reset): %h", rd);
        axi_read(32'h10, rd, 50);
        if (rd !== 32'hA5) $fatal(1,"R4 wrong after recovery (write lost or duplicated): %h", rd);
        $display("PASS: AXI slave survives video lock drop with in-flight transactions");
        $finish;
    end
    initial begin #200000;$fatal(1,"timeout");end
endmodule
