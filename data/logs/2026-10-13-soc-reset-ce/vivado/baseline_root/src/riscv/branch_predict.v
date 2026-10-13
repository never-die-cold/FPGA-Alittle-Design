module branch_predict #(
    parameter [1:0] BHT_MODE = 2'd0,
    parameter integer INDEX_BITS = 6
) (
    input wire clk, input wire rst_n,
    input wire lookup_valid, input wire [31:0] lookup_pc,
    output wire predict_taken, output wire [1:0] lookup_state,
    input wire update_valid, input wire [31:0] update_pc, input wire update_taken
);
    localparam integer ENTRIES = (1 << INDEX_BITS);
    wire [INDEX_BITS-1:0] lookup_index = lookup_pc[INDEX_BITS+1:2];
    wire [INDEX_BITS-1:0] update_index = update_pc[INDEX_BITS+1:2];
    generate
        if (BHT_MODE == 2'd1) begin : gen_bht1
            reg bht [0:ENTRIES-1];
            integer i;
            always @(posedge clk or negedge rst_n) begin
                if (!rst_n)
                    for (i = 0; i < ENTRIES; i = i + 1) bht[i] <= 1'b0;
                else if (update_valid)
                    bht[update_index] <= update_taken;
            end
            assign lookup_state = lookup_valid ? {2{bht[lookup_index]}} : 2'b00;
            assign predict_taken = lookup_state[1];
        end else if (BHT_MODE == 2'd2) begin : gen_bht2
            reg [1:0] bht [0:ENTRIES-1];
            integer i;
            always @(posedge clk or negedge rst_n) begin
                if (!rst_n)
                    for (i = 0; i < ENTRIES; i = i + 1) bht[i] <= 2'b00;
                else if (update_valid && update_taken && bht[update_index] != 2'b11)
                    bht[update_index] <= bht[update_index] + 2'b01;
                else if (update_valid && !update_taken && bht[update_index] != 2'b00)
                    bht[update_index] <= bht[update_index] - 2'b01;
            end
            assign lookup_state = lookup_valid ? bht[lookup_index] : 2'b00;
            assign predict_taken = lookup_state[1];
        end else begin : gen_bht_off
            assign lookup_state = 2'b00;
            assign predict_taken = 1'b0;
        end
    endgenerate
endmodule
