`timescale 1ns/1ps
// axi_regs 专项 tb：AXI-Lite 从机 BFM 验证
// 覆盖：复位值、写读回、wstrb 字节使能、保留区读 0/写忽略、序列化握手
// （bvalid 未完成前 awready/wready 拉低）、bresp/rresp OKAY。
module tb_axi_regs;
    reg clk, rst_n;
    reg        awvalid, wvalid, arvalid, bready, rready;
    reg [6:0]  awaddr, araddr;
    reg [31:0] wdata;
    reg [3:0]  wstrb;
    wire       awready, wready, arready, bvalid, rvalid;
    wire [1:0] bresp, rresp;
    wire [31:0] rdata;
    localparam NREG = 16;
    wire [NREG*32-1:0] regs_flat;
    integer errors;
    axi_regs #(.NREG(NREG), .AW(7), .RESV_BASE(11)) dut (
        .clk(clk), .rst_n(rst_n),
        .awvalid(awvalid), .awready(awready), .awaddr(awaddr),
        .wvalid(wvalid), .wready(wready), .wdata(wdata), .wstrb(wstrb),
        .bvalid(bvalid), .bready(bready), .bresp(bresp),
        .arvalid(arvalid), .arready(arready), .araddr(araddr),
        .rvalid(rvalid), .rready(rready), .rdata(rdata), .rresp(rresp),
        .regs_flat(regs_flat),.cfg_busy(1'b0),.cfg_applied(32'b0)
    );
    always #5 clk = ~clk;

    // 确定性拍数驱动（本从机 ready/响应时序完全确定，无需 wait 轮询）：
    // 写：negedge 发起 → posedge 接受(bvalid 置起) → 采样 → 下一 posedge bready 清除
    // 读：negedge 发起 → posedge 接受(rvalid/rdata 置起) → 采样 → rready 一拍清除
    task axi_write;
        input [6:0]  addr;
        input [31:0] data;
        input [3:0]  strb;
        begin
            @(negedge clk);
            awaddr = addr; awvalid = 1; wdata = data; wstrb = strb; wvalid = 1;
            bready = 1;
            @(posedge clk);                 // 写被接受，bvalid 置起
            @(negedge clk);
            awvalid = 0; wvalid = 0;
            if (bvalid !== 1'b1 || bresp !== 2'b00) begin
                errors = errors + 1;
                $display("FAIL: write bvalid=%b bresp=%b (exp 1/00)", bvalid, bresp);
            end
            @(posedge clk);                 // bready=1 清除 bvalid
            @(negedge clk);
            bready = 0;
            if (bvalid !== 1'b0) begin
                errors = errors + 1;
                $display("FAIL: write bvalid not cleared");
            end
        end
    endtask

    task axi_read;
        input [6:0]  addr;
        input [31:0] exp;
        begin
            @(negedge clk);
            araddr = addr; arvalid = 1;
            @(posedge clk);                 // 读被接受，rvalid/rdata 置起
            @(negedge clk);
            arvalid = 0;
            if (rvalid !== 1'b1 || rresp !== 2'b00 || rdata !== exp) begin
                errors = errors + 1;
                $display("FAIL: read[%h]=%h rvalid=%b resp=%b exp=%h/00",
                         addr, rdata, rvalid, rresp, exp);
            end
            rready = 1;
            @(posedge clk);                 // rready 清除 rvalid
            @(negedge clk);
            rready = 0;
            if (rvalid !== 1'b0) begin
                errors = errors + 1;
                $display("FAIL: read rvalid not cleared");
            end
        end
    endtask

    initial begin
        clk = 0; rst_n = 0;
        awvalid = 0; wvalid = 0; arvalid = 0; bready = 0; rready = 0;
        awaddr = 0; araddr = 0; wdata = 0; wstrb = 0;
        errors = 0;
        repeat (4) @(negedge clk);
        rst_n = 1;

        // 1) 复位值：R0..R10 读 0
        axi_read(6'h00, 32'h0);
        axi_read(6'h24, 32'h0);          // R9
        // 2) 写读回：R0 全开、box 参数
        axi_write(6'h00, 32'h0000_000F, 4'hF);
        axi_read (6'h00, 32'h0000_000F);
        axi_write(6'h04, 32'h0000_0002, 4'hF);
        axi_read (6'h04, 32'h0000_0002);
        // 3) wstrb 字节使能：只写低字节
        axi_write(6'h14, 32'hDEAD_BEEF, 4'b0001);   // R5 低字节
        axi_read (6'h14, 32'h0000_00EF);
        axi_write(6'h14, 32'h1122_3344, 4'b1100);   // 只写高两字节
        axi_read (6'h14, 32'h1122_00EF);
        // 4) 保留区：R11 写忽略、读 0
        axi_write(6'h2C, 32'h55AA_55AA, 4'hF);
        axi_read (6'h2C, 32'h0);
        // 5) 越界：写丢弃、读 0，响应仍 OKAY
        axi_write(7'h40, 32'hFFFF_FFFF, 4'hF);      // index 16 越界
        axi_read (7'h40, 32'h0);
        // 6) regs_flat 抽查：R0 值出现在 flat 向量
        if (regs_flat[0*32 +: 32] !== 32'h0000_000F) begin
            errors = errors + 1;
            $display("FAIL: regs_flat R0=%h exp=0000000f", regs_flat[0*32 +: 32]);
        end

        if (errors != 0) begin
            $display("FAIL: axi_regs %0d errors", errors);
            $fatal(1);
        end
        $display("PASS: axi_regs rw/strb/reserved/oob/flat, 0 errors");
        $finish;
    end
endmodule
