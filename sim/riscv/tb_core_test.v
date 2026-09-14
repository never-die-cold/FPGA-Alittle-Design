`timescale 1ns / 1ps
// tb_core_test.v —— v0 核 RV32I 逐指令自检 testbench
// 流程：$readmemh 预载 hello_test.hex → 复位 → 跑定拍 → 检查 tohost_exit == 0
// 失败时 tohost_exit = 失败用例编号（见 src/riscv_fw/test_rv32i.S）
// 接口以 src/riscv/design_v0.md §5.7 为准；运行目录约定：在 sim/ 下执行
module tb_core_test;

    localparam integer CLK_PERIOD   = 10;                    // 100 MHz
    localparam integer RESET_CYCLES = 8;
    localparam integer RUN_CYCLES   = 10000;
    localparam [31:0]  TOEXIT_ADDR   = 32'h8000_3FF4;        // start.S 写入的退出码
    localparam [31:0]  TOEXIT_EXPECT = 32'd0;

    reg clk = 0;
    reg rst_n = 0;
    integer i;

    // ---- core_top 接口（design_v0.md §5.7）----
    wire [31:0] imem_addr;
    reg  [31:0] imem_rdata;                                  // 由指令存储器模型驱动
    wire [31:0] dmem_addr;
    wire [31:0] dmem_wdata;
    wire [3:0]  dmem_be;
    wire        dmem_we;
    wire [31:0] dmem_rdata;

    // ---- 指令存储器模型：4096×32，同步读（本拍地址，下一拍数据）----
    reg [31:0] imem [0:4095];
    initial imem_rdata = 32'h0000_0013;
    always @(posedge clk)
        imem_rdata <= imem[imem_addr[13:2]];

    initial begin
        for (i = 0; i < 4096; i = i + 1)
            imem[i] = 32'h00000013;
        $readmemh("../src/riscv_fw/hello_test.hex", imem);
    end

    // ---- 数据存储器模型：4096×32，异步读 + 4 位字节使能写 ----
    reg [31:0] dmem [0:4095];
    always @(posedge clk)
        if (dmem_we) begin
            if (dmem_be[0]) dmem[dmem_addr[13:2]][7:0]   <= dmem_wdata[7:0];
            if (dmem_be[1]) dmem[dmem_addr[13:2]][15:8]  <= dmem_wdata[15:8];
            if (dmem_be[2]) dmem[dmem_addr[13:2]][23:16] <= dmem_wdata[23:16];
            if (dmem_be[3]) dmem[dmem_addr[13:2]][31:24] <= dmem_wdata[31:24];
        end
    assign dmem_rdata = dmem[dmem_addr[13:2]];

    // ---- 时钟 ----
    always #(CLK_PERIOD / 2) clk = ~clk;

    // ---- DUT ----
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

    // ---- 激励与自检 ----
    initial begin
        for (i = 0; i < 4096; i = i + 1)
            dmem[i] = 32'h0;

        $dumpfile("tb_core_test.vcd");
        $dumpvars(0, tb_core_test);

        repeat (RESET_CYCLES) @(posedge clk);
        rst_n = 1;

        repeat (RUN_CYCLES) @(posedge clk);

        if (dmem[TOEXIT_ADDR[13:2]] === TOEXIT_EXPECT) begin
            $display("PASS: all RV32I tests passed (tohost_exit = 0)");
        end else begin
            $display("FAIL: test #%0d failed (tohost_exit = %0d), last pc = 0x%08x",
                     dmem[TOEXIT_ADDR[13:2]], dmem[TOEXIT_ADDR[13:2]], imem_addr);
            $fatal(1);
        end
        $finish;
    end

endmodule
