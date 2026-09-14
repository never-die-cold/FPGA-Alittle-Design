`timescale 1ns / 1ps
// tb_core_smoke.v —— v0 核冒烟 testbench（骨架，RTL 到位后启用）
// 流程：$readmemh 预载 hello.hex → 复位 → 跑固定拍数 → 检查 tohost
// 接口以 src/riscv/design_v0.md §5.7 为准；src/riscv/ RTL 未写全时本 tb 不可编译（预期）
// 运行目录约定：在 sim/ 下执行（见 sim/scripts/run_iverilog.sh）
module tb_core_smoke;

    localparam integer CLK_PERIOD   = 10;                    // 100 MHz
    localparam integer RESET_CYCLES = 8;
    localparam integer RUN_CYCLES   = 4000;
    localparam [31:0]  TOHOST_ADDR   = 32'h8000_3FF0;        // main 写入的结果值
    localparam [31:0]  TOHOST_EXPECT = 32'd13;               // 见 src/riscv_fw/main_v0.c（RV32I 冒烟）
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
    initial imem_rdata = 32'h0000_0013;                      // 上电默认 NOP
    always @(posedge clk)
        imem_rdata <= imem[imem_addr[13:2]];

    initial begin
        for (i = 0; i < 4096; i = i + 1)
            imem[i] = 32'h00000013;                          // 默认 NOP
        $readmemh("../src/riscv_fw/hello_v0.hex", imem);
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

        $dumpfile("tb_core_smoke.vcd");
        $dumpvars(0, tb_core_smoke);

        repeat (RESET_CYCLES) @(posedge clk);
        rst_n = 1;

        repeat (RUN_CYCLES) @(posedge clk);

        if (dmem[TOHOST_ADDR[13:2]] === TOHOST_EXPECT &&
            dmem[TOEXIT_ADDR[13:2]] === TOEXIT_EXPECT) begin
            $display("PASS: tohost = %0d (0x%08x), tohost_exit = %0d",
                     dmem[TOHOST_ADDR[13:2]], dmem[TOHOST_ADDR[13:2]], dmem[TOEXIT_ADDR[13:2]]);
        end else begin
            $display("FAIL: tohost = %0d (0x%08x) expect %0d; tohost_exit = %0d expect %0d",
                     dmem[TOHOST_ADDR[13:2]], dmem[TOHOST_ADDR[13:2]], TOHOST_EXPECT,
                     dmem[TOEXIT_ADDR[13:2]], TOEXIT_EXPECT);
            $display("      last imem_addr = 0x%08x", imem_addr);
            $fatal(1);
        end
        $finish;
    end

endmodule
