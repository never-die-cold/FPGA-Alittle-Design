// core_top.v -- RV32IM v1 three-stage core: IF / ID+EX / MEM+WB
// External ports stay compatible with design_v0; v1 contract is design_v1.md.
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
    wire [31:0] pc_target;
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

    // ---------- ID+EX interface ----------
    wire [4:0] rs1_addr, rs2_addr, rd_addr;
    wire [2:0] muldiv_op;
    wire muldiv_valid, uses_rs1, uses_rs2;
    wire [31:0] redirect_target, ex_result, ex_addr, ex_store_data;
    wire ex_reg_write, ex_mem_read, ex_mem_write, ex_sign_ext;
    wire [1:0] ex_wb_sel, ex_mask_sel;

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

    // ---------- combinational ID+EX ----------
    id_ex_stage u_id_ex (
        .in_valid(instr_valid), .in_pc(pc_id), .in_instr(instr),
        .rs1_value(rs1_fwd), .rs2_value(rs2_fwd), .muldiv_result(muldiv_result),
        .rs1_addr(rs1_addr), .rs2_addr(rs2_addr), .rd_addr(rd_addr),
        .uses_rs1(uses_rs1), .uses_rs2(uses_rs2),
        .muldiv_valid(muldiv_valid), .muldiv_op(muldiv_op),
        .branch_taken(branch_taken), .jump_taken(jump_taken),
        .redirect_target(redirect_target),
        .ex_result(ex_result), .ex_addr(ex_addr), .ex_store_data(ex_store_data),
        .ex_reg_write(ex_reg_write), .ex_mem_read(ex_mem_read),
        .ex_mem_write(ex_mem_write), .ex_wb_sel(ex_wb_sel),
        .ex_mask_sel(ex_mask_sel), .ex_sign_ext(ex_sign_ext)
    );
    assign pc_target = redirect_target;

    // ---------- ID+EX / MEM+WB boundary ----------
    mem_wb_stage u_mem_wb (
        .clk(clk), .rst_n(rst_n), .in_valid(mem_in_valid),
        .in_instr(instr), .in_pc(pc_id), .in_rd(rd_addr),
        .in_result(ex_result), .in_addr(ex_addr), .in_store_data(ex_store_data),
        .in_reg_write(ex_reg_write), .in_mem_read(ex_mem_read), .in_mem_write(ex_mem_write),
        .in_wb_sel(ex_wb_sel), .in_mask_sel(ex_mask_sel), .in_sign_ext(ex_sign_ext),
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
