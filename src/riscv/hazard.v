// hazard.v -- Part B v1 combinational stall, accept and redirect control
module hazard (
    input wire enable_forwarding,
    input wire c_valid, c_uses_rs1, c_uses_rs2,
    input wire [4:0] c_rs1, c_rs2,
    input wire p_valid, p_we, p_is_load,
    input wire [4:0] p_rd,
    input wire muldiv_wait,
    input wire branch_taken, jump_taken,
    output wire data_stall, front_stall, ex_accept,
    output wire redirect, if_flush, mem_in_valid
);
    wire raw_rs1 = c_uses_rs1 && (c_rs1 == p_rd);
    wire raw_rs2 = c_uses_rs2 && (c_rs2 == p_rd);
    wire raw_dep = c_valid && p_valid && p_we && (p_rd != 0)
                 && (raw_rs1 || raw_rs2);

    assign data_stall  = raw_dep && (!enable_forwarding || p_is_load);
    assign front_stall = data_stall || muldiv_wait;
    assign ex_accept   = c_valid && !front_stall;
    assign redirect    = ex_accept && (branch_taken || jump_taken);
    assign if_flush    = redirect;
    assign mem_in_valid = ex_accept;
endmodule
