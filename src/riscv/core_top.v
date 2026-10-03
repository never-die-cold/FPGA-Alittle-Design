// core_top.v —— RV32IM 两级流水核顶层：IF / ID+EX+MEM+WB
// 对外接口见 src/riscv/design_v0.md §5.7；v0 特性见 §2（无 RAW/load-use 停顿，跳转 1 拍气泡）
module core_top #(
    parameter ENABLE_FORWARDING = 1'b1
) (
    input  wire        clk,
    input  wire        rst_n,
    output wire [31:0] imem_addr,
    input  wire [31:0] imem_rdata,
    output wire [31:0] dmem_addr,
    output wire [31:0] dmem_wdata,
    output wire [3:0]  dmem_be,
    output wire        dmem_we,
    input  wire [31:0] dmem_rdata
);

    // ---------- 取指 ----------
    wire [31:0] pc, pc_id;
    wire [1:0]  pc_sel;
    wire        stall;
    wire        branch_taken, jump_taken, flush;
    wire        data_stall, front_stall, ex_accept, redirect, mem_in_valid;
    wire [31:0] pc_target, branch_target;
    wire [31:0] instr;
    wire        instr_valid;

    assign imem_addr = pc;
    assign flush     = redirect;
    assign pc_sel    = flush ? 2'b01 : 2'b00;

    pc u_pc (
        .clk      (clk),
        .rst_n    (rst_n),
        .pc_sel   (pc_sel),
        .stall    (stall),
        .pc_target(pc_target),
        .pc       (pc),
        .pc_plus4 ()
    );

    if_stage u_if_stage (
        .clk       (clk),
        .rst_n     (rst_n),
        .pc        (pc),
        .imem_rdata(imem_rdata),
        .flush     (flush),
        .stall     (stall),
        .instr     (instr),
        .instr_valid(instr_valid),
        .pc_id     (pc_id)
    );

    // ---------- 译码 ----------
    wire [4:0]  rs1_addr, rs2_addr, rd_addr;
    wire [31:0] imm;
    wire [2:0]  imm_type;
    wire [3:0]  alu_op;
    wire [1:0]  alu_a_sel, alu_b_sel, wb_sel;
    wire        reg_write, mem_read, mem_write, sign_ext;
    wire [1:0]  mask_sel;
    wire [2:0]  branch_type;
    wire [1:0]  jump_type;
    wire [2:0]  muldiv_op;
    wire        muldiv_valid, uses_rs1, uses_rs2;

    decode u_decode (
        .instr      (instr),
        .rs1_addr   (rs1_addr),
        .rs2_addr   (rs2_addr),
        .rd_addr    (rd_addr),
        .imm        (imm),
        .imm_type   (imm_type),
        .alu_op     (alu_op),
        .alu_a_sel  (alu_a_sel),
        .alu_b_sel  (alu_b_sel),
        .wb_sel     (wb_sel),
        .reg_write  (reg_write),
        .mem_read   (mem_read),
        .mem_write  (mem_write),
        .mask_sel   (mask_sel),
        .sign_ext   (sign_ext),
        .branch_type(branch_type),
        .jump_type  (jump_type),
        .muldiv_valid(muldiv_valid),
        .muldiv_op  (muldiv_op),
        .uses_rs1   (uses_rs1),
        .uses_rs2   (uses_rs2)
    );

    // ---------- 寄存器堆 ----------
    wire [31:0] rdata1, rdata2, rs1_fwd, rs2_fwd, wb_data;
    wire        rf_we;
    wire        mem_valid;
    wire [31:0] mem_instr, mem_pc, mem_result, mem_addr, mem_store_data;
    wire [4:0]  mem_rd;
    wire        mem_reg_write, mem_mem_read, mem_mem_write;
    wire [1:0]  mem_wb_sel, mem_mask_sel;
    wire        mem_sign_ext;

    regfile u_regfile (
        .clk    (clk),
        .raddr1 (rs1_addr),
        .raddr2 (rs2_addr),
        .rdata1 (rdata1),
        .rdata2 (rdata2),
        .waddr  (mem_rd),
        .wdata  (wb_data),
        .we     (rf_we)
    );

    // ---------- 多拍乘除 ----------
    reg         muldiv_pending;
    wire [31:0] muldiv_result;
    wire        muldiv_busy, muldiv_done;
    wire        muldiv_wait = instr_valid && muldiv_valid && !muldiv_done;
    wire        muldiv_start = instr_valid && muldiv_valid && !data_stall &&
                               !muldiv_pending && !muldiv_busy;

    assign stall = front_stall;
    assign rf_we = mem_valid && mem_reg_write && (mem_rd != 5'd0);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            muldiv_pending <= 1'b0;
        else if (muldiv_done)
            muldiv_pending <= 1'b0;
        else if (muldiv_start)
            muldiv_pending <= 1'b1;
    end

    muldiv u_muldiv (
        .clk(clk), .rst_n(rst_n), .op(muldiv_op), .start(muldiv_start),
        .a(rs1_fwd), .b(rs2_fwd), .result(muldiv_result),
        .busy(muldiv_busy), .done(muldiv_done)
    );


    // ---------- forwarding and hazard control ----------
    wire [1:0] rs1_sel, rs2_sel;
    forwarding u_forwarding (
        .enable(ENABLE_FORWARDING), .uses_rs1(uses_rs1), .uses_rs2(uses_rs2),
        .rs1_addr(rs1_addr), .rs2_addr(rs2_addr), .rs1_data(rdata1), .rs2_data(rdata2),
        .ex_valid(mem_valid && !mem_mem_read), .ex_we(mem_reg_write), .ex_ready(1'b1),
        .ex_rd(mem_rd), .ex_data(wb_data),
        .mem_valid(mem_valid && mem_mem_read), .mem_we(mem_reg_write), .mem_ready(1'b1),
        .mem_rd(mem_rd), .mem_data(wb_data),
        .wb_valid(mem_valid), .wb_we(mem_reg_write), .wb_rd(mem_rd), .wb_data(wb_data),
        .rs1_fwd(rs1_fwd), .rs2_fwd(rs2_fwd), .rs1_sel(rs1_sel), .rs2_sel(rs2_sel)
    );

    hazard u_hazard (
        .enable_forwarding(ENABLE_FORWARDING),
        .c_valid(instr_valid), .c_uses_rs1(uses_rs1), .c_uses_rs2(uses_rs2),
        .c_rs1(rs1_addr), .c_rs2(rs2_addr),
        .p_valid(mem_valid), .p_we(mem_reg_write), .p_is_load(mem_mem_read), .p_rd(mem_rd),
        .muldiv_wait(muldiv_wait), .branch_taken(branch_taken), .jump_taken(jump_taken),
        .data_stall(data_stall), .front_stall(front_stall), .ex_accept(ex_accept),
        .redirect(redirect), .if_flush(), .mem_in_valid(mem_in_valid)
    );

    // ---------- ALU ----------
    wire [31:0] alu_a = (alu_a_sel == 2'b01) ? pc_id :
                        (alu_a_sel == 2'b10) ? 32'd0 : rs1_fwd;
    wire [31:0] alu_b = (alu_b_sel == 2'b00) ? rs2_fwd : imm;
    wire [31:0] alu_y;
    wire        alu_zero, alu_lt, alu_ltu;

    alu u_alu (
        .a     (alu_a),
        .b     (alu_b),
        .alu_op(alu_op),
        .y     (alu_y),
        .zero  (alu_zero),
        .lt    (alu_lt),
        .ltu   (alu_ltu)
    );

    // ---------- 分支/跳转裁决 ----------
    assign branch_target = pc_id + imm;

    wire cond_taken = (branch_type == 3'd1) ?  alu_zero :
                      (branch_type == 3'd2) ? ~alu_zero :
                      (branch_type == 3'd3) ?  alu_lt   :
                      (branch_type == 3'd4) ? ~alu_lt   :
                      (branch_type == 3'd5) ?  alu_ltu  :
                      (branch_type == 3'd6) ? ~alu_ltu  : 1'b0;

    assign branch_taken = (branch_type != 3'd0) && cond_taken;
    assign jump_taken   = (jump_type != 2'd0);
    assign pc_target    = (jump_type == 2'd2) ? (alu_y & 32'hFFFF_FFFE) : branch_target;

    // ---------- ID+EX / MEM+WB boundary ----------
    wire [31:0] ex_result = (wb_sel == 2'b10) ? (pc_id + 32'd4) :
                            (wb_sel == 2'b11) ? muldiv_result : alu_y;
    mem_wb_stage u_mem_wb (
        .clk(clk), .rst_n(rst_n), .in_valid(mem_in_valid),
        .in_instr(instr), .in_pc(pc_id), .in_rd(rd_addr),
        .in_result(ex_result), .in_addr(alu_y), .in_store_data(rs2_fwd),
        .in_reg_write(reg_write), .in_mem_read(mem_read), .in_mem_write(mem_write),
        .in_wb_sel(wb_sel), .in_mask_sel(mask_sel), .in_sign_ext(sign_ext),
        .mem_valid(mem_valid), .mem_instr(mem_instr), .mem_pc(mem_pc), .mem_rd(mem_rd),
        .mem_result(mem_result), .mem_addr(mem_addr), .mem_store_data(mem_store_data),
        .mem_reg_write(mem_reg_write), .mem_mem_read(mem_mem_read),
        .mem_mem_write(mem_mem_write), .mem_wb_sel(mem_wb_sel),
        .mem_mask_sel(mem_mask_sel), .mem_sign_ext(mem_sign_ext)
    );

    // ---------- MEM+WB: unique architectural side effects ----------
    assign dmem_addr  = mem_addr;
    assign dmem_wdata = (mem_mask_sel == 2'b00) ? {4{mem_store_data[7:0]}} :
                        (mem_mask_sel == 2'b01) ? {2{mem_store_data[15:0]}} :
                        mem_store_data;
    wire [3:0] be_w = (mem_mask_sel == 2'b00) ? (4'b0001 << mem_addr[1:0]) :
                      (mem_mask_sel == 2'b01) ? (mem_addr[1] ? 4'b1100 : 4'b0011) :
                      4'b1111;
    assign dmem_we = mem_valid && mem_mem_write;
    assign dmem_be = dmem_we ? be_w : 4'b0000;

    wire [7:0] byte_lane = (mem_addr[1:0] == 2'b00) ? dmem_rdata[7:0] :
                           (mem_addr[1:0] == 2'b01) ? dmem_rdata[15:8] :
                           (mem_addr[1:0] == 2'b10) ? dmem_rdata[23:16] : dmem_rdata[31:24];
    wire [15:0] half_lane = mem_addr[1] ? dmem_rdata[31:16] : dmem_rdata[15:0];
    wire [31:0] load_data = (mem_mask_sel == 2'b00) ?
        (mem_sign_ext ? {{24{byte_lane[7]}}, byte_lane} : {24'b0, byte_lane}) :
        (mem_mask_sel == 2'b01) ?
        (mem_sign_ext ? {{16{half_lane[15]}}, half_lane} : {16'b0, half_lane}) : dmem_rdata;
    assign wb_data = mem_mem_read ? load_data : mem_result;

endmodule
