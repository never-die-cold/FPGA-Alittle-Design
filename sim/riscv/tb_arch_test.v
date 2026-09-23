`timescale 1ns / 1ps
// tb_arch_test.v —— riscv-arch-test 签名比对 testbench（PYNQ-Z2 自研 v0 核）
// 用法（由 sim/scripts/run_arch_test.sh 调用）：
//   vvp tb_arch_test.vvp +hex=<镜像hex> +ref=<参考签名> +ref_len=<n> \
//       +sig_start=<字节地址> +cycles=<n> +sig_out=<输出文件> +name=<测试名>
// 语义：统一镜像同时预载 imem 与 dmem（数据区初值可见）；跑固定周期后读签名区，
//       逐字比对参考签名，写 .signature.output；PASS/FAIL 自检（FAIL 非零退出）
module tb_arch_test;

    localparam integer CLK_PERIOD   = 10;
    localparam integer RESET_CYCLES = 8;

    reg clk = 0;
    reg rst_n = 0;
    integer i;
    integer errors;

    // ---- plusargs ----
    reg [8*256-1:0] hex_file;
    reg [8*256-1:0] ref_file;
    reg [8*256-1:0] sig_out;
    reg [8*256-1:0] test_name;
    integer sig_start  = 32'h8000_0000;
    integer ref_len    = 0;
    integer run_cycles = 200000;

    // ---- core_top 接口（design_v0.md §5.7）----
    wire [31:0] imem_addr;
    reg  [31:0] imem_rdata;
    wire [31:0] dmem_addr;
    wire [31:0] dmem_wdata;
    wire [3:0]  dmem_be;
    wire        dmem_we;
    wire [31:0] dmem_rdata;

    // ---- 指令存储器模型：8192×32，同步读 ----
    reg [31:0] imem [0:8191];
    initial imem_rdata = 32'h0000_0013;
    always @(posedge clk)
        imem_rdata <= imem[imem_addr[14:2]];

    // ---- 数据存储器模型：8192×32，异步读 + 4 位字节使能写 ----
    reg [31:0] dmem [0:8191];
    always @(posedge clk)
        if (dmem_we) begin
            if (dmem_be[0]) dmem[dmem_addr[14:2]][7:0]   <= dmem_wdata[7:0];
            if (dmem_be[1]) dmem[dmem_addr[14:2]][15:8]  <= dmem_wdata[15:8];
            if (dmem_be[2]) dmem[dmem_addr[14:2]][23:16] <= dmem_wdata[23:16];
            if (dmem_be[3]) dmem[dmem_addr[14:2]][31:24] <= dmem_wdata[31:24];
        end
    assign dmem_rdata = dmem[dmem_addr[14:2]];

    always #(CLK_PERIOD / 2) clk = ~clk;

    core_top dut (
        .clk        (clk),
        .rst_n      (rst_n),
        .imem_addr  (imem_addr),
        .imem_rdata (imem_rdata),
        .dmem_addr  (dmem_addr),
        .dmem_wdata (dmem_wdata),
        .dmem_be    (dmem_be),
        .dmem_we    (dmem_we),
        .dmem_rdata (dmem_rdata)
    );

    // ---- 参考签名与比对 ----
    reg [31:0] ref_mem [0:8191];
    integer sig_idx;
    integer fd;
    integer shown;

    initial begin
        if (!$value$plusargs("hex=%s", hex_file)) begin
            $display("FAIL: 缺少 +hex 参数");
            $fatal(1);
        end
        if (!$value$plusargs("ref=%s", ref_file)) begin
            $display("FAIL: 缺少 +ref 参数");
            $fatal(1);
        end
        i = $value$plusargs("sig_out=%s", sig_out);
        i = $value$plusargs("name=%s", test_name);
        i = $value$plusargs("ref_len=%d", ref_len);
        i = $value$plusargs("sig_start=%d", sig_start);
        i = $value$plusargs("cycles=%d", run_cycles);

        for (i = 0; i < 8192; i = i + 1) begin
            imem[i] = 32'h0000_0013;
            dmem[i] = 32'h0;
        end
        $readmemh(hex_file, imem);
        $readmemh(hex_file, dmem);          // 统一镜像：数据区初值对 dmem 同样可见
        $readmemh(ref_file, ref_mem);

        $display("== arch-test %0s: 预载完成，运行 %0d 周期 ==", test_name, run_cycles);
        repeat (RESET_CYCLES) @(posedge clk);
        rst_n = 1;
        repeat (run_cycles) @(posedge clk);

        sig_idx = (sig_start & 32'h0000_7FFF) >> 2;
        errors = 0;
        shown = 0;
        fd = 0;
        if (sig_out != 0) fd = $fopen(sig_out, "w");
        for (i = 0; i < ref_len; i = i + 1) begin
            if (fd != 0) $fdisplay(fd, "%08x", dmem[sig_idx + i]);
            if (dmem[sig_idx + i] !== ref_mem[i]) begin
                errors = errors + 1;
                if (shown < 10) begin
                    $display("MISMATCH[%0d] expect %08x actual %08x", i, ref_mem[i], dmem[sig_idx + i]);
                    shown = shown + 1;
                end
            end
        end
        if (fd != 0) $fclose(fd);

        if (errors == 0) begin
            $display("PASS: %0s signature %0d words match reference", test_name, ref_len);
            $finish;
        end else begin
            $display("FAIL: %0s %0d/%0d signature words mismatch", test_name, errors, ref_len);
            $fatal(1);
        end
    end

endmodule
