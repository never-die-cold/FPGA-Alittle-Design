// if_stage.v —— IF 级流水寄存器：锁存指令与 pc_id；flush 时下一拍注入 NOP
// 复位后首拍 flush_q=1 注入气泡，保证首条指令只执行一次
// 语义见 src/riscv/design_v0.md §2、§5.2
module if_stage (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [31:0] pc,
    input  wire [31:0] imem_rdata,
    input  wire        flush,
    input  wire        stall,
    output wire [31:0] instr,
    output wire        instr_valid,
    output wire [31:0] pc_id
);

    localparam [31:0] NOP = 32'h0000_0013; // addi x0, x0, 0

    reg [31:0] pc_id_r;
    reg        flush_q;
    reg [31:0] instr_hold;
    reg        valid_hold;
    reg        stall_q;

    assign instr       = stall_q ? instr_hold : (flush_q ? NOP : imem_rdata);
    assign instr_valid = stall_q ? valid_hold : ~flush_q;
    assign pc_id       = pc_id_r;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            pc_id_r   <= 32'h8000_0000;
            flush_q   <= 1'b1;
            instr_hold <= NOP;
            valid_hold <= 1'b0;
            stall_q    <= 1'b0;
        end else begin
            stall_q <= stall;
            if (stall && !stall_q) begin
                instr_hold <= flush_q ? NOP : imem_rdata;
                valid_hold <= ~flush_q;
            end
            if (!stall) begin
                pc_id_r <= pc;
                flush_q <= flush;
            end
        end
    end

endmodule
