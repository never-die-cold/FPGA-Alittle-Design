`timescale 1ns/1ps
// hazard 单元级专项 tb —— 对应 design_v1.md 冻结契约 §9.1/§9.2/§9.4/§9.5/§9.6/§13.2
// 由 verify 线按冻结端口表预写（2026-09-29）；hazard.v 落地（RTL 线 R3 步）后
// 必须接入 run_iverilog.sh（单独模式 + all）并全 PASS，作为该模块验收门禁之一。
// 方法：tb 内置契约方程的独立参考模型，先定向用例再降维穷举扫描，逐组合对拍全部输出，
// 并断言全局不变量 redirect && front_stall == 0（契约 §13.2 硬性要求）。
module tb_hazard;
    reg         enable_forwarding;
    reg         c_valid, c_uses_rs1, c_uses_rs2;
    reg  [4:0]  c_rs1, c_rs2;
    reg         p_valid, p_we, p_is_load;
    reg  [4:0]  p_rd;
    reg         muldiv_wait, branch_taken, jump_taken;
    wire        data_stall, front_stall, ex_accept, redirect, if_flush, mem_in_valid;
    integer     checks;

    hazard dut (
        .enable_forwarding(enable_forwarding),
        .c_valid(c_valid), .c_uses_rs1(c_uses_rs1), .c_uses_rs2(c_uses_rs2),
        .c_rs1(c_rs1), .c_rs2(c_rs2),
        .p_valid(p_valid), .p_we(p_we), .p_is_load(p_is_load), .p_rd(p_rd),
        .muldiv_wait(muldiv_wait),
        .branch_taken(branch_taken), .jump_taken(jump_taken),
        .data_stall(data_stall), .front_stall(front_stall),
        .ex_accept(ex_accept), .redirect(redirect), .if_flush(if_flush),
        .mem_in_valid(mem_in_valid)
    );

    // 契约方程参考模型 + 全输出对拍（含互斥不变量）
    task apply_and_check;
        begin
            #1;
            begin : ref_model
                reg raw_rs1, raw_rs2, raw_dep;
                reg exp_data_stall, exp_front, exp_accept, exp_redirect;
                raw_rs1 = c_uses_rs1 && (c_rs1 == p_rd);
                raw_rs2 = c_uses_rs2 && (c_rs2 == p_rd);
                raw_dep = c_valid && p_valid && p_we && (p_rd != 5'd0) && (raw_rs1 || raw_rs2);
                exp_data_stall = enable_forwarding ? (raw_dep && p_is_load) : raw_dep;
                exp_front      = exp_data_stall || muldiv_wait;
                exp_accept     = c_valid && !exp_front;
                exp_redirect   = exp_accept && (branch_taken || jump_taken);
                checks = checks + 1;
                if (data_stall   !== exp_data_stall ||
                    front_stall  !== exp_front      ||
                    ex_accept    !== exp_accept     ||
                    redirect     !== exp_redirect   ||
                    if_flush     !== exp_redirect   ||
                    mem_in_valid !== exp_accept) begin
                    $display("FAIL: en=%b c(v%b u%b%b r%0d/%0d) p(v%b we%b ld%b rd%0d) mw=%b b=%b j=%b -> ds=%b fs=%b acc=%b red=%b flush=%b miv=%b",
                             enable_forwarding, c_valid, c_uses_rs1, c_uses_rs2, c_rs1, c_rs2,
                             p_valid, p_we, p_is_load, p_rd, muldiv_wait, branch_taken, jump_taken,
                             data_stall, front_stall, ex_accept, redirect, if_flush, mem_in_valid);
                    $fatal(1);
                end
                if (redirect && front_stall) begin
                    $display("FAIL: redirect 与 front_stall 同时为 1（契约 §13.2 不变量被破坏）");
                    $fatal(1);
                end
            end
        end
    endtask

    // 地址降维映射：0..3 原样，4 -> 5，便于让消费地址与生产 rd 相互命中
    function [4:0] addr5;
        input [2:0] v;
        begin
            addr5 = (v == 3'd4) ? 5'd5 : {3'b0, v[1:0]};
        end
    endfunction

    integer en, ld, u1, u2, a1, a2, pr, mw, bv, jv;
    reg [4:0] c1, c2, p0;

    initial begin
        checks = 0;
        enable_forwarding = 1; c_valid = 1; c_uses_rs1 = 1; c_uses_rs2 = 0;
        c_rs1 = 5'd5; c_rs2 = 5'd0; p_valid = 1; p_we = 1; p_is_load = 0; p_rd = 5'd5;
        muldiv_wait = 0; branch_taken = 0; jump_taken = 0;

        // 1) 定向：转发开，ALU 生产者 RAW 不停顿；load 生产者停 1 拍
        p_rd = 5'd5;
        apply_and_check;                        // ds=0
        p_is_load = 1; apply_and_check;         // ds=1
        // 2) 转发关：ALU/load 生产者 RAW 都停
        enable_forwarding = 0;
        p_is_load = 0; apply_and_check;         // ds=1
        p_is_load = 1; apply_and_check;         // ds=1
        enable_forwarding = 1;
        // 3) 伪 RAW：uses_rs*=0 不停（两种模式）
        c_uses_rs1 = 0;
        p_is_load = 1; apply_and_check;         // ds=0
        enable_forwarding = 0; apply_and_check; // ds=0
        enable_forwarding = 1; c_uses_rs1 = 1;
        // 4) 生产者 p_rd=x0 / p_we=0 / p_valid=0 / 消费者 c_valid=0：都不停
        p_rd = 5'd0; apply_and_check;
        p_rd = 5'd5; p_we = 0; apply_and_check; p_we = 1;
        p_valid = 0; apply_and_check; p_valid = 1;
        c_valid = 0; apply_and_check;           // ds=0 且 ex_accept=0、redirect=0
        c_valid = 1;
        // 5) muldiv_wait：front_stall=1，ex_accept=0，redirect 被抑制
        branch_taken = 1; muldiv_wait = 1; apply_and_check;
        muldiv_wait = 0; apply_and_check;       // 恢复：无停顿 → redirect=1
        branch_taken = 0; jump_taken = 1; apply_and_check;
        jump_taken = 0;
        // 6) branch 遇 RAW 先停顿再裁决：load-use 停顿期间不得用旧值 redirect
        p_is_load = 1; branch_taken = 1; apply_and_check;   // ds=1 → redirect=0
        branch_taken = 0; p_is_load = 0;

        // 7) 降维穷举：控制位与地址域全组合，参考模型逐组合对拍
        for (en = 0; en < 2; en = en + 1)
        for (ld = 0; ld < 2; ld = ld + 1)
        for (u1 = 0; u1 < 2; u1 = u1 + 1)
        for (u2 = 0; u2 < 2; u2 = u2 + 1)
        for (a1 = 0; a1 < 5; a1 = a1 + 1)
        for (a2 = 0; a2 < 5; a2 = a2 + 1)
        for (pr = 0; pr < 5; pr = pr + 1)
        for (mw = 0; mw < 2; mw = mw + 1)
        for (bv = 0; bv < 2; bv = bv + 1)
        for (jv = 0; jv < 2; jv = jv + 1) begin
            enable_forwarding = en[0];
            c_valid = 1; p_valid = 1; p_we = 1;
            c_uses_rs1 = u1[0]; c_uses_rs2 = u2[0];
            c_rs1 = addr5(a1[2:0]);
            c_rs2 = addr5(a2[2:0]);
            p_rd  = addr5(pr[2:0]);
            p_is_load = ld[0]; muldiv_wait = mw[0];
            branch_taken = bv[0]; jump_taken = jv[0];
            apply_and_check;
        end

        // 8) 穷举补充：c_valid=0 / p_valid=0 / p_we=0 三类失格沿（抽两组代表组合）
        for (en = 0; en < 2; en = en + 1) begin
            enable_forwarding = en[0];
            c_uses_rs1 = 1; c_uses_rs2 = 1; p_is_load = 1; muldiv_wait = 0;
            branch_taken = 1; jump_taken = 0;
            c_rs1 = 5'd5; c_rs2 = 5'd5; p_rd = 5'd5;
            c_valid = 0; p_valid = 1; p_we = 1; apply_and_check;
            c_valid = 1; p_valid = 0; apply_and_check;
            c_valid = 1; p_valid = 1; p_we = 0; apply_and_check;
        end

        $display("PASS: hazard unit checks (%0d cases)", checks);
        $finish;
    end
endmodule
