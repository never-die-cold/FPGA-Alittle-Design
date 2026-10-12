`timescale 1ns/1ps
// line_buffer 专项 tb：同步读、同拍同址先读后写（返回旧值）、按址读写独立性
module tb_line_buffer;
    reg clk, we;
    reg [3:0] waddr, raddr;
    reg [7:0] wdata;
    wire [7:0] rdata;
    integer i, errors;

    line_buffer #(.WIDTH(16), .DW(8)) dut (
        .clk(clk), .we(we), .waddr(waddr), .wdata(wdata),
        .raddr(raddr), .rdata(rdata)
    );
    always #5 clk = ~clk;

    task expect_val;
        input [7:0] got, exp;
        input [63:0] tag;
        begin
            if (got !== exp) begin
                errors = errors + 1;
                $display("FAIL: %0s got=%02x exp=%02x", tag, got, exp);
            end
        end
    endtask

    initial begin
        clk = 0; we = 0; waddr = 0; raddr = 0; wdata = 0; errors = 0;
        @(negedge clk);
        // 1) 写入 16 个可识别值：mem[i] = A0+i
        for (i = 0; i < 16; i = i + 1) begin
            we = 1; waddr = i; wdata = 8'hA0 + i;
            @(negedge clk);
        end
        we = 0;
        // 2) 逐址回读：设地址后隔一拍取数（同步读语义）
        for (i = 0; i < 16; i = i + 1) begin
            raddr = i;
            @(negedge clk);
            expect_val(rdata, 8'hA0 + i, "readback");
        end
        // 3) 同拍同址写读：rdata 必须返回旧值（先读后写，gaussian 依赖）
        waddr = 4'd5; wdata = 8'hFF; raddr = 4'd5; we = 1;
        @(negedge clk);
        expect_val(rdata, 8'hA5, "read-before-write");
        we = 0;
        // 4) 下一拍读到新值
        @(negedge clk);
        expect_val(rdata, 8'hFF, "updated");
        // 5) 写读异址互不干扰：写 7 读 8
        waddr = 4'd7; wdata = 8'h77; raddr = 4'd8; we = 1;
        @(negedge clk);
        expect_val(rdata, 8'hA8, "write-read-diff-addr");
        we = 0;
        if (errors != 0) begin
            $display("FAIL: line_buffer %0d errors", errors);
            $fatal(1);
        end
        $display("PASS: line_buffer sync-read, read-before-write, addressing");
        $finish;
    end
endmodule
