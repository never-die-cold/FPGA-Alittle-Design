`timescale 1ns / 1ps
// tb_core_fwd.v —— 转发专项契约级 testbench（数据冒险气泡 + 分支气泡）
// 流程：预载 riscv/fwd/fwd_test.hex → 复位 → 运行至结束标记 → 自检 PASS/FAIL
//   1) 各阶段结果与期望常数比对（R 型连读 / lw→运算 / 循环计数 / 误跳标记）
//   2) 各阶段气泡计数比对：v0 默认 A=0 B=0 C=5 D=0（design_v0 §2.2 无数据停顿、§2.3 taken 分支 1 拍）
//      v1 接入时用 +exp_a=0 +exp_b=4 +exp_c=5 +exp_d=0 之类覆盖（见 sim/README.md）
// 运行目录约定：在 sim/ 下执行（sim/scripts/run_iverilog.sh fwd）
module tb_core_fwd;

    localparam integer CLK_PERIOD   = 10;                    // 100 MHz
    localparam integer RESET_CYCLES = 8;
    localparam integer CYCLE_LIMIT  = 30000;                 // 看门狗上限

    // 观测地址（见 sim/riscv/fwd/fwd_test.S）
    localparam [11:0] MARK_IDX   = 12'hF80;                  // 0x8000_3E00 >> 2
    localparam [11:0] RESULT_IDX = 12'hE00;                  // 0x8000_3800 >> 2

    // 气泡期望（默认 = v0 契约；可用 plusargs 覆盖）
    integer exp_a = 0;                                       // 阶段 A：R 型连读
    integer exp_b = 0;                                       // 阶段 B：lw→运算
    integer exp_c = 5;                                       // 阶段 C：taken 分支/跳转次数
    integer exp_d = 0;                                       // 阶段 D：not-taken 分支

    reg clk = 0;
    reg rst_n = 0;
    integer i;
    integer k;

    // ---- core_top 接口（design_v0.md §5.7）----
    wire [31:0] imem_addr;
    reg  [31:0] imem_rdata;
    wire [31:0] dmem_addr;
    wire [31:0] dmem_wdata;
    wire [3:0]  dmem_be;
    wire        dmem_we;
    wire [31:0] dmem_rdata;

    // ---- 指令存储器模型：4096×32，同步读 ----
    reg [31:0] imem [0:4095];
    initial imem_rdata = 32'h0000_0013;
    always @(posedge clk)
        imem_rdata <= imem[imem_addr[13:2]];

    initial begin
        for (i = 0; i < 4096; i = i + 1)
            imem[i] = 32'h00000013;
        $readmemh("riscv/fwd/fwd_test.hex", imem);
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

    // ---- 监视：周期 / 气泡 / 阶段标记 ----
    // 气泡定义：复位释放后 instr_valid==0 的拍（v0 = 分支冲刷注入的 NOP 拍）
    integer cycle_count  = 0;
    integer bubble_count = 0;
    integer marker_seen  = 0;
    integer mark_bubbles [0:8];
    integer mark_cycles  [0:8];
    reg [31:0] mark_value [0:8];

    always @(posedge clk) begin
        if (rst_n) begin
            cycle_count = cycle_count + 1;
            if (dut.instr_valid === 1'b0)
                bubble_count = bubble_count + 1;
            if (dmem_we && (dmem_addr[13:2] == MARK_IDX)) begin
                if (marker_seen <= 8) begin
                    mark_bubbles[marker_seen] = bubble_count;
                    mark_cycles [marker_seen] = cycle_count;
                    mark_value  [marker_seen] = dmem_wdata;
                end
                marker_seen = marker_seen + 1;
            end
        end
    end

    // ---- 期望结果（见 fwd_test.S 注释逐条推导）----
    reg [31:0] exp_res_a [0:9];
    reg [31:0] exp_res_b [0:4];
    initial begin
        exp_res_a[0]=3; exp_res_a[1]=6; exp_res_a[2]=9; exp_res_a[3]=3; exp_res_a[4]=10;
        exp_res_a[5]=14; exp_res_a[6]=8; exp_res_a[7]=16; exp_res_a[8]=4; exp_res_a[9]=12;
        exp_res_b[0]=200; exp_res_b[1]=300; exp_res_b[2]=400; exp_res_b[3]=300; exp_res_b[4]=328;
    end

    // ---- 激励与自检 ----
    integer errors = 0;
    integer pa_b, pb_b, pc_b, pd_b;
    integer pa_c, pb_c, pc_c, pd_c;

    initial begin
        i = $value$plusargs("exp_a=%d", exp_a);
        i = $value$plusargs("exp_b=%d", exp_b);
        i = $value$plusargs("exp_c=%d", exp_c);
        i = $value$plusargs("exp_d=%d", exp_d);

        for (i = 0; i < 4096; i = i + 1)
            dmem[i] = 32'h0;

        $dumpfile("tb_core_fwd.vcd");
        $dumpvars(0, tb_core_fwd);

        repeat (RESET_CYCLES) @(posedge clk);
        rst_n = 1;

        while (marker_seen < 9 && cycle_count < CYCLE_LIMIT)
            @(posedge clk);

        if (marker_seen < 9) begin
            $display("FAIL: 未跑完（marker_seen=%0d, last_marker=0x%08x, cycles=%0d, last_pc=0x%08x）",
                     marker_seen,
                     (marker_seen > 0) ? mark_value[marker_seen-1] : 32'h0,
                     cycle_count, imem_addr);
            errors = errors + 1;
        end else begin
            // 标记序列：101..108 + 200
            for (k = 0; k < 8; k = k + 1)
                if (mark_value[k] !== (101 + k)) begin
                    $display("FAIL: 标记[%0d] 期望 %0d 实际 0x%08x", k, 101 + k, mark_value[k]);
                    errors = errors + 1;
                end
            if (mark_value[8] !== 32'd200) begin
                $display("FAIL: 结束标记 期望 200 实际 0x%08x", mark_value[8]);
                errors = errors + 1;
            end

            // 阶段结果比对
            for (k = 0; k < 10; k = k + 1)
                if (dmem[RESULT_IDX + k] !== exp_res_a[k]) begin
                    $display("FAIL: 阶段A 结果[%0d] 期望 %0d 实际 %0d", k, exp_res_a[k], dmem[RESULT_IDX + k]);
                    errors = errors + 1;
                end
            for (k = 0; k < 5; k = k + 1)
                if (dmem[RESULT_IDX + 16 + k] !== exp_res_b[k]) begin
                    $display("FAIL: 阶段B 结果[%0d] 期望 %0d 实际 %0d", k, exp_res_b[k], dmem[RESULT_IDX + 16 + k]);
                    errors = errors + 1;
                end
            if (dmem[RESULT_IDX + 24] !== 32'd4) begin
                $display("FAIL: 阶段C 循环计数 期望 4 实际 %0d", dmem[RESULT_IDX + 24]);
                errors = errors + 1;
            end
            if (dmem[RESULT_IDX + 25] !== 32'd0) begin
                $display("FAIL: 阶段D 误跳标记 期望 0 实际 %0d（not-taken 分支被误判）", dmem[RESULT_IDX + 25]);
                errors = errors + 1;
            end

            // 阶段气泡/周期统计
            pa_b = mark_bubbles[1] - mark_bubbles[0];
            pb_b = mark_bubbles[3] - mark_bubbles[2];
            pc_b = mark_bubbles[5] - mark_bubbles[4];
            pd_b = mark_bubbles[7] - mark_bubbles[6];
            pa_c = mark_cycles[1] - mark_cycles[0];
            pb_c = mark_cycles[3] - mark_cycles[2];
            pc_c = mark_cycles[5] - mark_cycles[4];
            pd_c = mark_cycles[7] - mark_cycles[6];

            $display("== fwd phase A (R-type RAW) : cycles=%0d bubbles=%0d (expect %0d)", pa_c, pa_b, exp_a);
            $display("== fwd phase B (lw->op)     : cycles=%0d bubbles=%0d (expect %0d)", pb_c, pb_b, exp_b);
            $display("== fwd phase C (taken)      : cycles=%0d bubbles=%0d (expect %0d)", pc_c, pc_b, exp_c);
            $display("== fwd phase D (not-taken)  : cycles=%0d bubbles=%0d (expect %0d)", pd_c, pd_b, exp_d);

            if (pa_b !== exp_a) begin $display("FAIL: 阶段A 气泡 期望 %0d 实际 %0d", exp_a, pa_b); errors = errors + 1; end
            if (pb_b !== exp_b) begin $display("FAIL: 阶段B 气泡 期望 %0d 实际 %0d", exp_b, pb_b); errors = errors + 1; end
            if (pc_b !== exp_c) begin $display("FAIL: 阶段C 气泡 期望 %0d 实际 %0d", exp_c, pc_b); errors = errors + 1; end
            if (pd_b !== exp_d) begin $display("FAIL: 阶段D 气泡 期望 %0d 实际 %0d", exp_d, pd_b); errors = errors + 1; end
        end

        if (errors == 0) begin
            $display("PASS: fwd_test 结果全对；气泡 A/B/C/D = %0d/%0d/%0d/%0d，总周期 %0d，总气泡 %0d",
                     pa_b, pb_b, pc_b, pd_b, cycle_count, bubble_count);
            $finish;
        end else begin
            $display("FAIL: %0d 项不符（详见上）", errors);
            $fatal(1);
        end
    end

endmodule
