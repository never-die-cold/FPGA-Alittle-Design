// mem_wb_stage.v -- Part B v1 ID+EX/MEM+WB boundary register
module mem_wb_stage (
    input wire clk, rst_n, in_valid,
    input wire [31:0] in_instr, in_pc,
    input wire [4:0] in_rd,
    input wire [31:0] in_result, in_addr, in_store_data,
    input wire in_reg_write, in_mem_read, in_mem_write,
    input wire [1:0] in_wb_sel, in_mask_sel,
    input wire in_sign_ext,
    output reg mem_valid,
    output reg [31:0] mem_instr, mem_pc,
    output reg [4:0] mem_rd,
    output reg [31:0] mem_result, mem_addr, mem_store_data,
    output reg mem_reg_write, mem_mem_read, mem_mem_write,
    output reg [1:0] mem_wb_sel, mem_mask_sel,
    output reg mem_sign_ext
);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            mem_valid <= 1'b0;
        end else begin
            mem_valid      <= in_valid;
            mem_instr      <= in_instr;
            mem_pc         <= in_pc;
            mem_rd         <= in_rd;
            mem_result     <= in_result;
            mem_addr       <= in_addr;
            mem_store_data <= in_store_data;
            mem_reg_write  <= in_reg_write;
            mem_mem_read   <= in_mem_read;
            mem_mem_write  <= in_mem_write;
            mem_wb_sel     <= in_wb_sel;
            mem_mask_sel   <= in_mask_sel;
            mem_sign_ext   <= in_sign_ext;
        end
    end
endmodule
