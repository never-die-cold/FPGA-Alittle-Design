// core_top.v —— RV32IM 两级流水核顶层：IF / ID+EX+MEM+WB
// 对外接口见 src/riscv/design_v0.md §5.7；v0 特性见 §2（无 RAW/load-use 停顿，跳转 1 拍气泡）
module core_top (
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
    wire [31:0] pc_target, branch_target;
    wire [31:0] instr;
    wire        instr_valid;

    assign imem_addr = pc;
    assign flush     = branch_taken | jump_taken;
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
    wire        muldiv_valid;

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
        .muldiv_op  (muldiv_op)
    );

    // ---------- 寄存器堆 ----------
    wire [31:0] rdata1, rdata2, wb_data;
    wire        rf_we;

    regfile u_regfile (
        .clk    (clk),
        .raddr1 (rs1_addr),
        .raddr2 (rs2_addr),
        .rdata1 (rdata1),
        .rdata2 (rdata2),
        .waddr  (rd_addr),
        .wdata  (wb_data),
        .we     (rf_we)
    );

    // ---------- 多拍乘除 ----------
    reg         muldiv_pending;
    wire [31:0] muldiv_result;
    wire        muldiv_busy, muldiv_done;
    wire        muldiv_start = instr_valid && muldiv_valid &&
                               !muldiv_pending && !muldiv_busy;

    assign stall = muldiv_valid && !muldiv_done;
    assign rf_we = reg_write && (!muldiv_valid || muldiv_done);

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
        .a(rdata1), .b(rdata2), .result(muldiv_result),
        .busy(muldiv_busy), .done(muldiv_done)
    );

    // ---------- ALU ----------
    wire [31:0] alu_a = (alu_a_sel == 2'b01) ? pc_id :
                        (alu_a_sel == 2'b10) ? 32'd0 : rdata1;
    wire [31:0] alu_b = (alu_b_sel == 2'b00) ? rdata2 : imm;
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

    // ---------- 访存 ----------
    assign dmem_addr  = alu_y;
    assign dmem_wdata = (mask_sel == 2'b00) ? {4{rdata2[7:0]}}  :
                        (mask_sel == 2'b01) ? {2{rdata2[15:0]}} : rdata2;

    wire [3:0] be_w = (mask_sel == 2'b00) ? (4'b0001 << alu_y[1:0]) :
                      (mask_sel == 2'b01) ? (alu_y[1] ? 4'b1100 : 4'b0011) :
                      4'b1111;
    assign dmem_be = mem_write ? be_w : 4'b0000;
    assign dmem_we = mem_write;

    // ---------- 读数据扩展与写回 ----------
    wire [7:0]  byte_lane = (alu_y[1:0] == 2'b00) ? dmem_rdata[7:0]   :
                            (alu_y[1:0] == 2'b01) ? dmem_rdata[15:8]  :
                            (alu_y[1:0] == 2'b10) ? dmem_rdata[23:16] : dmem_rdata[31:24];
    wire [15:0] half_lane = alu_y[1] ? dmem_rdata[31:16] : dmem_rdata[15:0];

    wire [31:0] load_data = (mask_sel == 2'b00) ? (sign_ext ? {{24{byte_lane[7]}}, byte_lane}  : {24'b0, byte_lane})  :
                            (mask_sel == 2'b01) ? (sign_ext ? {{16{half_lane[15]}}, half_lane} : {16'b0, half_lane}) :
                            dmem_rdata;

    assign wb_data = (wb_sel == 2'b01) ? load_data :
                     (wb_sel == 2'b10) ? (pc_id + 32'd4) :
                     (wb_sel == 2'b11) ? muldiv_result : alu_y;

endmodule
