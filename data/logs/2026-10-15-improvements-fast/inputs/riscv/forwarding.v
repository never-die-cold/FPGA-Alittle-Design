// forwarding.v -- Part B v1 combinational operand bypass
module forwarding (
    input wire enable,
    input wire uses_rs1, uses_rs2,
    input wire [4:0] rs1_addr, rs2_addr,
    input wire [31:0] rs1_data, rs2_data,
    input wire ex_valid, ex_we, ex_ready,
    input wire [4:0] ex_rd,
    input wire [31:0] ex_data,
    input wire mem_valid, mem_we, mem_ready,
    input wire [4:0] mem_rd,
    input wire [31:0] mem_data,
    input wire wb_valid, wb_we,
    input wire [4:0] wb_rd,
    input wire [31:0] wb_data,
    output wire [31:0] rs1_fwd, rs2_fwd,
    output wire [1:0] rs1_sel, rs2_sel
);
    localparam [1:0] SEL_RF=2'b00, SEL_WB=2'b01, SEL_MEM=2'b10, SEL_EX=2'b11;

    function automatic [33:0] select_src;
        input used; input [4:0] addr; input [31:0] rf_value;
        input ev, ew, er; input [4:0] erd; input [31:0] edata;
        input mv, mw, mr; input [4:0] mrd; input [31:0] mdata;
        input wv, ww; input [4:0] wrd; input [31:0] wdata;
        begin
            if (addr == 5'd0) select_src = {SEL_RF, 32'd0};
            else if (!enable || !used) select_src = {SEL_RF, rf_value};
            else if (ev && ew && er && erd != 0 && erd == addr)
                select_src = {SEL_EX, edata};
            else if (mv && mw && mr && mrd != 0 && mrd == addr)
                select_src = {SEL_MEM, mdata};
            else if (wv && ww && wrd != 0 && wrd == addr)
                select_src = {SEL_WB, wdata};
            else select_src = {SEL_RF, rf_value};
        end
    endfunction

    assign {rs1_sel, rs1_fwd} = select_src(uses_rs1, rs1_addr, rs1_data,
        ex_valid, ex_we, ex_ready, ex_rd, ex_data,
        mem_valid, mem_we, mem_ready, mem_rd, mem_data, wb_valid, wb_we, wb_rd, wb_data);
    assign {rs2_sel, rs2_fwd} = select_src(uses_rs2, rs2_addr, rs2_data,
        ex_valid, ex_we, ex_ready, ex_rd, ex_data,
        mem_valid, mem_we, mem_ready, mem_rd, mem_data, wb_valid, wb_we, wb_rd, wb_data);
endmodule
