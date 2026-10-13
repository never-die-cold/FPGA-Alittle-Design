`timescale 1ns/1ps
// C02 full-network operator controller, not the C03 MMIO/DMA/firmware wrapper.
// External ROI/ping/pong/parameter/weight banks: synchronous 1-cycle reads.
// Banks share reset; model and ROI are immutable for the complete busy window.
module cnn_sequencer (
    input wire clk, rst_n, ce, start,
    input wire [7:0] min_margin,
    input wire [31:0] cycle_limit,
    output wire ready,
    output reg busy, done, error,
    output reg [2:0] error_layer,
    output reg [31:0] cycles,
    output reg [1:0] result_class,
    output reg [7:0] result_margin,
    output reg [14:0] result_score,
    output reg result_low_conf,
    output reg [23:0] result_logits,
    output wire memory_enable, weight_enable, parameter_enable,
    output wire [1:0] read_bank,
    output wire [15:0] read_address, weight_address,
    output wire [7:0] parameter_address,
    input wire [63:0] input_data,
    input wire [1023:0] weight_data,
    input wire [511:0] bias_data, multiplier_data,
    input wire [95:0] shift_data,
    output wire write_enable,
    output wire [1:0] write_bank,
    output wire [15:0] write_address,
    output wire [63:0] write_data
);
    localparam IDLE=0, LAYER_START=1, LAYER_WAIT=2, GAP_REQ=3, GAP_USE=4, GAP_WRITE=5, RESULT=6;
    reg [2:0] state, layer;
    reg [31:0] limit;
    reg [7:0] margin_threshold;
    reg [10:0] gap_index;
    reg [255:0] gap_sums;
    reg [23:0] logits;
    reg [6:0] ci,co,h,w;
    reg [1:0] kernel,stride,padding,in_bank,out_bank;
    reg [15:0] weight_base;
    reg [7:0] param_base;
    wire engine_ready, engine_busy, engine_done, engine_error;
    wire engine_read, engine_parameter, engine_write;
    wire [31:0] engine_cycles;
    wire [15:0] engine_input_address,engine_weight_address,engine_write_address;
    wire [63:0] engine_write_data;
    wire [1:0] engine_block,classification;
    wire [7:0] margin;
    wire [14:0] score;
    wire low_conf,classification_error;
    wire [63:0] gap_results;
    wire [7:0] gap_errors;
    wire permitted;
    assign ready=ce && !busy;
    assign permitted=rst_n && busy && cycles < limit-1;
    always @* begin
        ci=1; co=16; h=64; w=64; kernel=3; stride=2; padding=1;
        in_bank=0; out_bank=2; weight_base=0; param_base=0;
        case(layer)
            1: begin ci=16; co=32; h=32; w=32; stride=1; in_bank=2; out_bank=1; weight_base=9; param_base=16; end
            2: begin ci=32; co=32; h=32; w=32; in_bank=1; out_bank=2; weight_base=45; param_base=48; end
            3: begin ci=32; co=64; h=16; w=16; stride=1; in_bank=2; out_bank=1; weight_base=117; param_base=80; end
            4: begin ci=64; co=3; h=1; w=1; kernel=1; stride=1; padding=0; in_bank=3; out_bank=2; weight_base=261; param_base=144; end
            default: begin end
        endcase
    end
    conv_engine engine (.clk(clk),.rst_n(rst_n),.ce(ce),.abort(!permitted),
        .start(state==LAYER_START && permitted),.cfg_ci(ci),.cfg_co(co),.cfg_width(w),.cfg_height(h),
        .cfg_kernel(kernel),.cfg_stride(stride),.cfg_padding(padding),.cfg_relu(layer!=4),
        .cfg_cycle_limit(limit),.ready(engine_ready),.busy(engine_busy),.done(engine_done),.error(engine_error),
        .cycles(engine_cycles),.memory_enable(engine_read),.input_address(engine_input_address),
        .weight_address(engine_weight_address),.input_data(input_data),.weight_data(weight_data),
        .parameter_enable(engine_parameter),.output_block(engine_block),.bias_data(bias_data),
        .multiplier_data(multiplier_data),.shift_data(shift_data),.write_enable(engine_write),
        .write_address(engine_write_address),.write_data(engine_write_data));
    assign memory_enable=permitted && ce && (state==GAP_REQ || engine_read);
    assign weight_enable=permitted && engine_read;
    assign parameter_enable=permitted && engine_parameter;
    assign read_bank=state==GAP_REQ || state==GAP_USE ? 2'd1 : in_bank;
    assign read_address=state==GAP_REQ || state==GAP_USE ? {5'd0,gap_index} : engine_input_address;
    assign weight_address=weight_base+engine_weight_address;
    assign parameter_address=param_base+engine_block*16;
    assign write_enable=permitted && ce && ((state==GAP_WRITE && !(|gap_errors)) || engine_write);
    assign write_bank=state==GAP_WRITE ? 2'd3 : out_bank;
    assign write_address=state==GAP_WRITE ? {13'd0,gap_index[10:8]} : engine_write_address;
    assign write_data=state==GAP_WRITE ? gap_results : engine_write_data;
    genvar i;
    generate for(i=0;i<8;i=i+1) begin: gap_lanes
        int8_gap average (.total(gap_sums[i*32 +: 32]),.result(gap_results[i*8 +: 8]),.error(gap_errors[i]));
    end endgenerate
    int8_logits classify (.logits(logits),.min_margin(margin_threshold),.class_id(classification),
        .margin_q(margin),.score_q15(score),.low_conf(low_conf),.error(classification_error));
    integer lane;
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n) begin
            state<=IDLE; layer<=0; busy<=0; done<=0; error<=0; cycles<=0; error_layer<=0;
            limit<=0; margin_threshold<=0; gap_index<=0; gap_sums<=0; logits<=0;
            result_class<=3; result_margin<=0; result_score<=0; result_low_conf<=1; result_logits<=0;
        end else begin
            if(busy) cycles<=cycles+1;
            if(busy && cycles>=limit-1) begin busy<=0; done<=0; error<=1; error_layer<=7; state<=IDLE; end
            else if(ce) case(state)
                IDLE: if(start) begin
                    done<=0; error<=0; cycles<=0; layer<=0; error_layer<=0; logits<=0;
                    result_class<=3; result_margin<=0; result_score<=0; result_low_conf<=1; result_logits<=0;
                    margin_threshold<=min_margin; limit<=cycle_limit;
                    if(cycle_limit==0) error<=1;
                    else begin busy<=1; state<=LAYER_START; end
                end
                LAYER_START: if(engine_ready) state<=LAYER_WAIT;
                LAYER_WAIT: if(engine_error) begin
                    busy<=0; done<=0; error<=1; error_layer<=layer; state<=IDLE;
                end else if(engine_done) begin
                    if(layer==3) begin gap_index<=0; gap_sums<=0; state<=GAP_REQ; end
                    else if(layer==4) state<=RESULT;
                    else begin layer<=layer+1; state<=LAYER_START; end
                end
                GAP_REQ: state<=GAP_USE;
                GAP_USE: begin
                    if(input_data & 64'h8080808080808080) begin
                        busy<=0; done<=0; error<=1; error_layer<=5; state<=IDLE;
                    end else begin
                        for(lane=0;lane<8;lane=lane+1)
                            gap_sums[lane*32 +: 32]<=gap_sums[lane*32 +: 32]+input_data[lane*8 +: 8];
                        if(gap_index[7:0]==255) state<=GAP_WRITE;
                        else begin gap_index<=gap_index+1; state<=GAP_REQ; end
                    end
                end
                GAP_WRITE: if(|gap_errors) begin
                    busy<=0; done<=0; error<=1; error_layer<=5; state<=IDLE;
                end else if(gap_index==2047) begin layer<=4; state<=LAYER_START; end
                else begin gap_index<=gap_index+1; gap_sums<=0; state<=GAP_REQ; end
                RESULT: if(classification_error) begin
                    busy<=0; done<=0; error<=1; error_layer<=4; state<=IDLE;
                end else begin
                    result_class<=classification; result_margin<=margin; result_score<=score;
                    result_low_conf<=low_conf; result_logits<=logits; busy<=0; done<=1; state<=IDLE;
                end
                default: begin busy<=0; done<=0; error<=1; error_layer<=7; state<=IDLE; end
            endcase
            if(permitted && engine_write && ce && layer==4) logits<=engine_write_data[23:0];
        end
    end
endmodule
