`timescale 1ns/1ps
// forwarding 单元级专项 tb —— 对应 design_v1.md 冻结契约 §8.2/§8.3/§8.6/§13.1
// 由 verify 线按冻结端口表预写（2026-09-29）；forwarding.v 落地（RTL 线 R2 步）后
// 必须接入 run_iverilog.sh（单独模式 + all）并全 PASS，作为该模块验收门禁之一。
// 数值约定：EX 源值=32'hE500_0000+rd，MEM 源值=32'h6000_0000+rd，WB 源值=32'h1000_0000+rd，
// RF 原始读值 rs1=32'hAAAA_0001、rs2=32'hAAAA_0002，便于波形与断言直读来源。
module tb_forwarding;
    reg         enable;
    reg         uses_rs1, uses_rs2;
    reg  [4:0]  rs1_addr, rs2_addr;
    reg  [31:0] rs1_data, rs2_data;
    reg         ex_valid, ex_we, ex_ready;
    reg  [4:0]  ex_rd;
    reg  [31:0] ex_data;
    reg         mem_valid, mem_we, mem_ready;
    reg  [4:0]  mem_rd;
    reg  [31:0] mem_data;
    reg         wb_valid, wb_we;
    reg  [4:0]  wb_rd;
    reg  [31:0] wb_data;
    wire [31:0] rs1_fwd, rs2_fwd;
    wire [1:0]  rs1_sel, rs2_sel;   // 00=RF 01=WB 10=MEM 11=EX
    integer     checks;

    forwarding dut (
        .enable(enable),
        .uses_rs1(uses_rs1), .uses_rs2(uses_rs2),
        .rs1_addr(rs1_addr), .rs2_addr(rs2_addr),
        .rs1_data(rs1_data), .rs2_data(rs2_data),
        .ex_valid(ex_valid), .ex_we(ex_we), .ex_ready(ex_ready),
        .ex_rd(ex_rd), .ex_data(ex_data),
        .mem_valid(mem_valid), .mem_we(mem_we), .mem_ready(mem_ready),
        .mem_rd(mem_rd), .mem_data(mem_data),
        .wb_valid(wb_valid), .wb_we(wb_we),
        .wb_rd(wb_rd), .wb_data(wb_data),
        .rs1_fwd(rs1_fwd), .rs2_fwd(rs2_fwd),
        .rs1_sel(rs1_sel), .rs2_sel(rs2_sel)
    );

    // 三来源统一置为有效可用，个别用例再单独关掉
    task set_sources;
        input [4:0] er, mr, wr;
        begin
            ex_rd  = er; ex_data  = 32'hE500_0000 + er; ex_valid  = 1; ex_we  = 1; ex_ready  = 1;
            mem_rd = mr; mem_data = 32'h6000_0000 + mr; mem_valid = 1; mem_we = 1; mem_ready = 1;
            wb_rd  = wr; wb_data  = 32'h1000_0000 + wr; wb_valid  = 1; wb_we  = 1;
        end
    endtask

    task check1;
        input [31:0] exp_val;
        input [1:0]  exp_sel;
        input        which_rs1;   // 1=检查 rs1，0=检查 rs2
        begin
            checks = checks + 1;
            if (which_rs1) begin
                if (rs1_fwd !== exp_val || rs1_sel !== exp_sel) begin
                    $display("FAIL: rs1 fwd=%h sel=%b exp=%h sel=%b", rs1_fwd, rs1_sel, exp_val, exp_sel);
                    $fatal(1);
                end
            end else begin
                if (rs2_fwd !== exp_val || rs2_sel !== exp_sel) begin
                    $display("FAIL: rs2 fwd=%h sel=%b exp=%h sel=%b", rs2_fwd, rs2_sel, exp_val, exp_sel);
                    $fatal(1);
                end
            end
        end
    endtask

    initial begin
        checks = 0;
        enable = 1; uses_rs1 = 1; uses_rs2 = 1;
        rs1_addr = 5'd5;  rs2_addr = 5'd6;
        rs1_data = 32'hAAAA_0001; rs2_data = 32'hAAAA_0002;

        // 1) 无命中：三来源 rd 均不等于消费者地址
        set_sources(5'd20, 5'd21, 5'd22);
        #1 check1(32'hAAAA_0001, 2'b00, 1);
        check1(32'hAAAA_0002, 2'b00, 0);

        // 2) 消费者地址为 x0：输出固定 0（sel 不作检查）
        rs1_addr = 5'd0; rs2_addr = 5'd0;
        set_sources(5'd0, 5'd0, 5'd0);
        #1 if (rs1_fwd !== 32'h0 || rs2_fwd !== 32'h0) begin
            $display("FAIL: x0 消费者必须输出 0，实际 rs1=%h rs2=%h", rs1_fwd, rs2_fwd);
            $fatal(1);
        end
        checks = checks + 1;
        rs1_addr = 5'd5; rs2_addr = 5'd6;

        // 3) used=0：即使命中也强制 RF
        set_sources(5'd5, 5'd5, 5'd5);
        uses_rs1 = 0; uses_rs2 = 0;
        #1 check1(32'hAAAA_0001, 2'b00, 1);
        check1(32'hAAAA_0002, 2'b00, 0);
        uses_rs1 = 1; uses_rs2 = 1;

        // 4) 单一来源命中
        set_sources(5'd9, 5'd9, 5'd5);   // 只 WB 命中 rs1 → 01
        #1 check1(32'h1000_0005, 2'b01, 1);
        set_sources(5'd9, 5'd6, 5'd9);   // 只 MEM 命中 rs2 → 10
        #1 check1(32'h6000_0006, 2'b10, 0);
        set_sources(5'd5, 5'd9, 5'd9);   // 只 EX 命中 rs1 → 11
        #1 check1(32'hE500_0005, 2'b11, 1);

        // 5) 多重命中优先级 EX > MEM > WB
        set_sources(5'd5, 5'd5, 5'd5);
        #1 check1(32'hE500_0005, 2'b11, 1);        // 三者全中 → EX
        ex_valid = 0;  #1 check1(32'h6000_0005, 2'b10, 1);  // EX 失格 → MEM
        mem_valid = 0; #1 check1(32'h1000_0005, 2'b01, 1);  // MEM 失格 → WB
        ex_valid = 1; mem_valid = 1;
        rs2_addr = 5'd5;
        #1 check1(32'hE500_0005, 2'b11, 0);        // rs2 独立同判
        rs2_addr = 5'd6;

        // 6) 门控位逐位验证：先失格高优先级源，隔离观察目标源的 valid/we/ready 门控
        set_sources(5'd5, 5'd5, 5'd5);
        ex_valid = 0; mem_ready = 0;                 // 只剩 WB 有效
        #1 check1(32'h1000_0005, 2'b01, 1);          // 基线：WB 命中
        wb_we = 0;   #1 check1(32'hAAAA_0001, 2'b00, 1);   // wb_we=0 → RF
        wb_we = 1;   #1 check1(32'h1000_0005, 2'b01, 1);   // 恢复
        wb_valid = 0; #1 check1(32'hAAAA_0001, 2'b00, 1);  // wb_valid=0 → RF
        wb_valid = 1;

        mem_ready = 1; ex_we = 0;                    // EX 失格(we)，MEM 有效
        #1 check1(32'h6000_0005, 2'b10, 1);          // 基线：MEM 命中
        mem_we = 0;  #1 check1(32'h1000_0005, 2'b01, 1);   // mem_we=0 → 退 WB
        mem_we = 1; mem_ready = 0;
        #1 check1(32'h1000_0005, 2'b01, 1);          // mem_ready=0 → 退 WB
        mem_ready = 1;

        ex_valid = 1; ex_we = 1;                     // 三源全有效
        #1 check1(32'hE500_0005, 2'b11, 1);          // 基线：EX 命中
        ex_ready = 0; #1 check1(32'h6000_0005, 2'b10, 1);  // ex_ready=0 → 退 MEM
        ex_ready = 1; ex_valid = 0;
        #1 check1(32'h6000_0005, 2'b10, 1);          // ex_valid=0 → 退 MEM
        ex_valid = 1;

        // 7) 生产者 rd=x0：与消费者地址不构成命中，走 RF
        rs1_addr = 5'd5;
        set_sources(5'd0, 5'd0, 5'd0);
        #1 check1(32'hAAAA_0001, 2'b00, 1);

        // 8) enable=0：两操作数强制 RF 且 sel=00
        enable = 0;
        set_sources(5'd5, 5'd6, 5'd7);
        #1 check1(32'hAAAA_0001, 2'b00, 1);
        check1(32'hAAAA_0002, 2'b00, 0);
        enable = 1;

        $display("PASS: forwarding unit checks (%0d cases)", checks);
        $finish;
    end
endmodule
