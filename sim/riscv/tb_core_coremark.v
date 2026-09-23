`timescale 1ns / 1ps
// tb_core_coremark.v —— 通用固件回归/跑分 tb（CoreMark 短迭代等）
// 跑法（在 sim/ 下）：vvp build/tb_core_coremark.vvp
//   [+hex=路径] [+exp_tohost=N] [+exp_exit=N] [+max_cycles=N] [+timer_addr=HEX] [+vcd]
//   [+exp_iter=N] [+exp_seedcrc=HEX] [+exp_crclist=HEX] [+exp_crcmatrix=HEX] [+exp_crcstate=HEX] [+exp_crcfinal=HEX]
// 默认固件 ../src/riscv_fw/coremark.hex；未入库前可用 +hex=../src/riscv_fw/hello.hex 冒烟
// 判据：观察到写 tohost_exit(0x8000_3FF4) 即结束；核对 exit/tohost 后打印 cycles/instrs/bubbles/CPI
// 观测块（契约 docs/coremark_tb_contract.md §4.3）：镜像自带 MAGIC 时自动 dump 11 字并按 +exp_* 判据校验
// 存储模型：8192×32、addr[14:2]（design_v0.md §3.3 冻结契约）
module tb_core_coremark;

    localparam integer CLK_PERIOD   = 10;
    localparam integer RESET_CYCLES = 8;
    localparam [12:0]  TOHOST_IDX      = 13'h0FFC;  // 0x8000_3FF0 >> 2
    localparam [12:0]  TOHOST_EXIT_IDX = 13'h0FFD;  // 0x8000_3FF4 >> 2

    reg clk = 0;
    reg rst_n = 0;
    integer i, fd;
    integer errors = 0;

    // plusargs 可覆盖项
    reg [1023:0] hex_file = "../src/riscv_fw/coremark.hex";
    integer exp_tohost = 0, has_exp_tohost = 0, exp_exit = 0;
    integer max_cycles = 10000000;
    integer timer_addr = 0;      // 非 0：该字节地址的读返回自由运行周期数（CoreMark 计时用）

    // 观测块（契约 §4.3）：基址 0x8000_7F00，字索引 0x1FC0
    localparam [12:0] OBS_IDX        = 13'h1FC0;
    localparam [31:0] OBS_MAGIC_ID   = 32'h434D_4B31; // "CMK1"
    localparam [31:0] OBS_MAGIC_DONE = 32'h444F_4E45; // "DONE"
    integer exp_iter = 0, has_exp_iter = 0;
    integer exp_seedcrc = 0, has_exp_seedcrc = 0;
    integer exp_crclist = 0, has_exp_crclist = 0;
    integer exp_crcmatrix = 0, has_exp_crcmatrix = 0;
    integer exp_crcstate = 0, has_exp_crcstate = 0;
    integer exp_crcfinal = 0, has_exp_crcfinal = 0;

    // ---- core_top 外部接口（design_v0.md §5.7）----
    wire [31:0] imem_addr, dmem_addr, dmem_wdata, dmem_rdata;
    wire [3:0]  dmem_be;
    wire        dmem_we;
    reg  [31:0] imem_rdata = 32'h0000_0013;
    wire [12:0] imem_idx = imem_addr[14:2];
    wire [12:0] dmem_idx = dmem_addr[14:2];

    // ---- 周期 / 退休指令 / 气泡统计 + 结束监视 ----
    // 注：instr_valid/stall 为 v0 两级核内部信号，Part B 重构后需同步
    reg [31:0] cycle_count = 0, instr_count = 0, bubble_count = 0;
    integer tohost_seen = 0, exit_seen = 0;
    reg [31:0] tohost_val = 0, exit_val = 0;
    reg [63:0] cpi_x1000 = 0;

    // ---- 存储模型：8192×32，同步指令读 / 异步数据读 + 字节写 ----
    reg [31:0] imem [0:8191];
    reg [31:0] dmem [0:8191];
    always @(posedge clk) imem_rdata <= imem[imem_idx];
    always @(posedge clk) if (dmem_we) begin
        if (dmem_be[0]) dmem[dmem_idx][7:0]   <= dmem_wdata[7:0];
        if (dmem_be[1]) dmem[dmem_idx][15:8]  <= dmem_wdata[15:8];
        if (dmem_be[2]) dmem[dmem_idx][23:16] <= dmem_wdata[23:16];
        if (dmem_be[3]) dmem[dmem_idx][31:24] <= dmem_wdata[31:24];
    end
    wire timer_hit = (timer_addr != 0) && (dmem_addr[31:2] == timer_addr[31:2]) && !dmem_we;
    assign dmem_rdata = timer_hit ? cycle_count : dmem[dmem_idx];

    always #(CLK_PERIOD / 2) clk = ~clk;

    core_top dut (
        .clk(clk), .rst_n(rst_n), .imem_addr(imem_addr), .imem_rdata(imem_rdata),
        .dmem_addr(dmem_addr), .dmem_wdata(dmem_wdata), .dmem_be(dmem_be),
        .dmem_we(dmem_we), .dmem_rdata(dmem_rdata)
    );

    always @(posedge clk) if (rst_n) begin
        cycle_count = cycle_count + 1;
        if (dut.instr_valid && !dut.stall) instr_count = instr_count + 1;
        if (!dut.instr_valid) bubble_count = bubble_count + 1;
        if (dmem_we && (dmem_idx == TOHOST_IDX)) begin
            tohost_seen = 1;
            tohost_val  = dmem_wdata;
        end
        if (dmem_we && (dmem_idx == TOHOST_EXIT_IDX) && !exit_seen) begin
            exit_seen = 1;
            exit_val  = dmem_wdata;
        end
        if ((cycle_count % 2000000) == 0)
            $display("... 进度 cycles=%0d pc=0x%08x tohost=%0d", cycle_count, imem_addr, tohost_val);
    end

    initial begin
        i = $value$plusargs("hex=%s", hex_file);
        i = $value$plusargs("exp_tohost=%d", exp_tohost);
        has_exp_tohost = i;
        i = $value$plusargs("exp_exit=%d", exp_exit);
        i = $value$plusargs("max_cycles=%d", max_cycles);
        i = $value$plusargs("timer_addr=%h", timer_addr);
        i = $value$plusargs("exp_iter=%d", exp_iter);        has_exp_iter = i;
        i = $value$plusargs("exp_seedcrc=%h", exp_seedcrc);  has_exp_seedcrc = i;
        i = $value$plusargs("exp_crclist=%h", exp_crclist);  has_exp_crclist = i;
        i = $value$plusargs("exp_crcmatrix=%h", exp_crcmatrix); has_exp_crcmatrix = i;
        i = $value$plusargs("exp_crcstate=%h", exp_crcstate); has_exp_crcstate = i;
        i = $value$plusargs("exp_crcfinal=%h", exp_crcfinal); has_exp_crcfinal = i;

        fd = $fopen(hex_file, "r");
        if (fd == 0) $fatal(1, "hex 打不开：%0s（未移植 CoreMark 时用 +hex=../src/riscv_fw/hello.hex）", hex_file);
        $fclose(fd);

        for (i = 0; i < 8192; i = i + 1) begin
            imem[i] = 32'h0000_0013;
            dmem[i] = 32'd0;
        end
        $readmemh(hex_file, imem);
        // 哈佛双口加载器语义：镜像同时预载 DMEM（.data 初值与 .rodata 读取，
        // CoreMark 的 switch 跳转表在 rodata，必须可读；见 docs/coremark_tb_contract.md §4.2）
        $readmemh(hex_file, dmem);

        if ($test$plusargs("vcd")) begin
            $dumpfile("tb_core_coremark.vcd");
            $dumpvars(0, tb_core_coremark);
        end

        repeat (RESET_CYCLES) @(posedge clk);
        rst_n = 1'b1;
        while (!exit_seen && cycle_count < max_cycles) @(posedge clk);

        if (!exit_seen) begin
            $display("FAIL: %0d 周期超时未写 tohost_exit（pc=0x%08x tohost_seen=%0d tohost=%0d）",
                     max_cycles, imem_addr, tohost_seen, tohost_val);
            $fatal(1);
        end
        $display("== coremark hex=%0s exit=%0d tohost=%0d cycles=%0d instrs=%0d bubbles=%0d",
                 hex_file, exit_val, tohost_val, cycle_count, instr_count, bubble_count);
        if (exit_val !== exp_exit) begin
            $display("FAIL: exit 期望 %0d 实际 %0d", exp_exit, exit_val);
            errors = errors + 1;
        end
        if (has_exp_tohost && (!tohost_seen || tohost_val !== exp_tohost)) begin
            $display("FAIL: tohost 期望 %0d 实际 %0d（seen=%0d）", exp_tohost, tohost_val, tohost_seen);
            errors = errors + 1;
        end

        // ---- 观测块判据（契约 §4.3/§5.1）----
        if (dmem[OBS_IDX] === OBS_MAGIC_ID) begin
            $display("== obs iter=%0d seedcrc=0x%04x crclist=0x%04x crcmatrix=0x%04x crcstate=0x%04x crcfinal=0x%04x t0=%0d t1=%0d errors=%0d",
                     dmem[OBS_IDX+1], dmem[OBS_IDX+2][15:0], dmem[OBS_IDX+3][15:0],
                     dmem[OBS_IDX+4][15:0], dmem[OBS_IDX+5][15:0], dmem[OBS_IDX+6][15:0],
                     dmem[OBS_IDX+7], dmem[OBS_IDX+8], dmem[OBS_IDX+9]);
            if (dmem[OBS_IDX+10] !== OBS_MAGIC_DONE) begin
                $display("FAIL: 观测块未封口 DONE_MAGIC=0x%08x", dmem[OBS_IDX+10]);
                errors = errors + 1;
            end
            if (has_exp_iter    && dmem[OBS_IDX+1]  !== exp_iter)    begin $display("FAIL: obs iterations 期望 %0d 实际 %0d", exp_iter, dmem[OBS_IDX+1]); errors = errors + 1; end
            if (has_exp_seedcrc && dmem[OBS_IDX+2]  !== exp_seedcrc) begin $display("FAIL: obs seedcrc 期望 0x%04x 实际 0x%04x", exp_seedcrc, dmem[OBS_IDX+2][15:0]); errors = errors + 1; end
            if (has_exp_crclist && dmem[OBS_IDX+3]  !== exp_crclist) begin $display("FAIL: obs crclist 期望 0x%04x 实际 0x%04x", exp_crclist, dmem[OBS_IDX+3][15:0]); errors = errors + 1; end
            if (has_exp_crcmatrix && dmem[OBS_IDX+4] !== exp_crcmatrix) begin $display("FAIL: obs crcmatrix 期望 0x%04x 实际 0x%04x", exp_crcmatrix, dmem[OBS_IDX+4][15:0]); errors = errors + 1; end
            if (has_exp_crcstate && dmem[OBS_IDX+5] !== exp_crcstate) begin $display("FAIL: obs crcstate 期望 0x%04x 实际 0x%04x", exp_crcstate, dmem[OBS_IDX+5][15:0]); errors = errors + 1; end
            if (has_exp_crcfinal && dmem[OBS_IDX+6] !== exp_crcfinal) begin $display("FAIL: obs crcfinal 期望 0x%04x 实际 0x%04x", exp_crcfinal, dmem[OBS_IDX+6][15:0]); errors = errors + 1; end
        end else if (has_exp_iter || has_exp_seedcrc || has_exp_crclist || has_exp_crcmatrix || has_exp_crcstate || has_exp_crcfinal) begin
            $display("FAIL: 未找到观测块（dmem[0x%04x]=0x%08x），无法执行 CRC 判据", OBS_IDX, dmem[OBS_IDX]);
            errors = errors + 1;
        end
        if (errors != 0) $fatal(1, "FAIL: %0d 项不符", errors);
        cpi_x1000 = (instr_count != 0) ? (({32'b0, cycle_count} * 64'd1000) / {32'b0, instr_count}) : 64'd0;
        $display("PASS: coremark cycles=%0d instrs=%0d bubbles=%0d cpi=%0d.%03d",
                 cycle_count, instr_count, bubble_count, cpi_x1000 / 1000, cpi_x1000 % 1000);
        $finish;
    end
endmodule
