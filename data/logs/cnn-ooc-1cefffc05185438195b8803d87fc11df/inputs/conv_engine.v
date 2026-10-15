`timescale 1ns/1ps
// One outstanding, synchronous 1-cycle BRAM read; ce stalls the operator.
// Memory/parameter banks must share reset and remain immutable while busy.
// Writes are intermediate data: usable only after done && !error.
module conv_engine (
    input wire clk, rst_n, ce, start, abort,
    input wire [6:0] cfg_ci, cfg_co, cfg_width, cfg_height,
    input wire [1:0] cfg_kernel, cfg_stride, cfg_padding,
    input wire cfg_relu,
    input wire [31:0] cfg_cycle_limit,
    output wire ready,
    output reg busy, done, error,
    output reg [31:0] cycles,
    output wire memory_enable,
    output reg [15:0] input_address, weight_address,
    input wire [63:0] input_data,
    input wire [1023:0] weight_data,
    output wire parameter_enable,
    output wire [1:0] output_block,
    input wire [511:0] bias_data, multiplier_data,
    input wire [95:0] shift_data,
    output wire write_enable,
    output wire [15:0] write_address,
    output wire [63:0] write_data
);
    localparam IDLE=0, PARAM_REQ=1, PARAM_USE=2, READ_REQ=3, MAC_USE=4,
               QUANT=5, WRITE_LOW=6, WRITE_HIGH=7, ADVANCE=8, QUANT_WAIT=10,
               GEOMETRY=11, ADDRESS_USE=12, SETUP=13;
    reg [3:0] state;
    reg [6:0] ci, co, width, height, ow, oh;
    reg [1:0] kernel, stride, padding, ob;
    reg [3:0] ib, blocks;
    reg [1:0] ky, kx;
    reg [6:0] oy, ox;
    reg relu;
    reg [31:0] limit_last;
    reg [511:0] accumulators, multipliers, bias_latched;
    reg [95:0] shifts;
    reg [127:0] quantized;
    wire [511:0] next_accumulators, sum_accumulators;
    wire [15:0] mac_overflow, sum_overflow, active_outputs;
    wire [15:0] quant_results;
    wire mac_valid;
    wire [1:0] quant_valid, quant_errors;
    reg mac_issue;
    reg [2:0] mac_pending, q_send, q_receive;
    wire [63:0] activations;
    reg padding_pixel;
    reg signed [8:0] iy, ix;
    reg [8:0] input_row;
    reg [5:0] weight_row;
    reg [12:0] plane_words;
    reg [15:0] pixel_row, block_base, output_address_low;
    function [7:0] output_size;
        input [6:0] size;
        input [1:0] k, s, p;
        reg [7:0] span;
        begin
            // Launch validation rejects size+2*p<k; legal spans are unsigned.
            span = {1'b0,size}+{5'd0,p,1'b0}-{6'd0,k};
            output_size = s == 2'd2 ? (span >> 1)+8'd1 : span+8'd1;
        end
    endfunction
    assign ready = ce && !busy && !abort;
    assign output_block = ob;
    assign active_outputs = co >= ob*16+16 ? 16'hffff : (16'h1 << (co-ob*16))-1;
    assign activations = padding_pixel ? 64'd0 : ci == 1 ? {56'd0,input_data[7:0]} : input_data;
    assign memory_enable = rst_n && ce && busy && state == READ_REQ && cycles < limit_last;
    assign parameter_enable = rst_n && ce && busy && state == PARAM_REQ && cycles < limit_last;
    assign write_enable = rst_n && ce && busy && cycles < limit_last
                       && (state == WRITE_LOW || state == WRITE_HIGH);
    assign write_address = output_address_low+(state==WRITE_HIGH ? plane_words : 13'd0);
    assign write_data = state == WRITE_HIGH ? quantized[127:64] : quantized[63:0];
    always @* begin
        iy = $signed({2'd0,oy})*(stride==2 ? 9'sd2 : 9'sd1)+$signed({7'd0,ky})-$signed({7'd0,padding});
        ix = $signed({2'd0,ox})*(stride==2 ? 9'sd2 : 9'sd1)+$signed({7'd0,kx})-$signed({7'd0,padding});
    end
    // A read is followed by its MAC launch on the next enabled edge.
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n) mac_issue<=0;
        else if(abort || !busy) mac_issue<=0;
        else if(ce) mac_issue<=state==READ_REQ;
    end
    mac_array_pipeline array_mac (.clk(clk),.rst_n(rst_n),.ce(ce),.abort(abort || !busy),
        .in_valid(busy && mac_issue),.out_valid(mac_valid),
        .activation_lanes(activations), .weight_lanes(weight_data),
        .accumulator_lanes(512'd0), .result_lanes(next_accumulators), .overflow(mac_overflow));
    genvar lane;
    generate for(lane=0;lane<16;lane=lane+1) begin: accumulate_lanes
        wire signed [32:0] total = {accumulators[lane*32+31],accumulators[lane*32 +: 32]}
                                  + {next_accumulators[lane*32+31],next_accumulators[lane*32 +: 32]};
        assign sum_accumulators[lane*32 +: 32]=total[31:0];
        assign sum_overflow[lane]=total[32]^total[31];
    end endgenerate
    // Two II=1 pipelines process all sixteen channels in eight CE beats.
    generate for (lane=0; lane<2; lane=lane+1) begin: requant_lanes
        wire signed [7:0] q;
        wire [3:0] channel={q_send,1'b0}+lane;
        int8_requant_pipeline requant (.clk(clk),.rst_n(rst_n),.ce(ce),.abort(abort),
            .in_valid(busy && state==QUANT),.out_valid(quant_valid[lane]),
            .accumulator(accumulators[channel*32 +: 32]),
            .multiplier(multipliers[channel*32 +: 32]), .shift(shifts[channel*6 +: 6]),
            .relu(relu), .result(q), .error(quant_errors[lane]));
        assign quant_results[lane*8 +: 8] = q;
    end endgenerate
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state<=IDLE; busy<=0; done<=0; error<=0; cycles<=0;
            ci<=0; co<=0; width<=0; height<=0; ow<=0; oh<=0;
            kernel<=0; stride<=0; padding<=0; ob<=0; ib<=0; blocks<=0;
            ky<=0; kx<=0; oy<=0; ox<=0; relu<=0; limit_last<=0;
            accumulators<=0; multipliers<=0; shifts<=0; quantized<=0; bias_latched<=0;
            mac_pending<=0; q_send<=0; q_receive<=0;
            padding_pixel<=0; input_row<=0; weight_row<=0; plane_words<=0;
            pixel_row<=0; block_base<=0; output_address_low<=0; input_address<=0; weight_address<=0;
        end else begin
            if (busy) cycles<=cycles+1;
            if(abort) begin busy<=0; done<=0; error<=0; state<=IDLE; end
            else if (busy && cycles >= limit_last) begin
                busy<=0; done<=0; error<=1; state<=IDLE;
            end else if (ce && busy && mac_valid && mac_pending!=0
                         && |((mac_overflow | sum_overflow) & active_outputs)) begin
                busy<=0; done<=0; error<=1; state<=IDLE;
            end else if (ce) begin
                if(busy) begin
                    if(mac_valid && mac_pending!=0) accumulators<=sum_accumulators;
                    case({state==READ_REQ,mac_valid && mac_pending!=0})
                        2'b10: mac_pending<=mac_pending+1;
                        2'b01: mac_pending<=mac_pending-1;
                        default: begin end
                    endcase
                end
                case (state)
                IDLE: if (start) begin
                    done<=0; error<=0; cycles<=0;
                    if (cfg_ci == 0 || cfg_ci > 64 || (cfg_ci != 1 && cfg_ci[2:0] != 0)
                        || cfg_co == 0 || cfg_co > 64 || cfg_width == 0 || cfg_width > 64
                        || cfg_height == 0 || cfg_height > 64
                        || (cfg_kernel != 1 && cfg_kernel != 3)
                        || (cfg_stride != 1 && cfg_stride != 2) || cfg_padding > 1
                        || cfg_width+2*cfg_padding < cfg_kernel || cfg_height+2*cfg_padding < cfg_kernel
                        || output_size(cfg_width,cfg_kernel,cfg_stride,cfg_padding) > 64
                        || output_size(cfg_height,cfg_kernel,cfg_stride,cfg_padding) > 64
                        || cfg_cycle_limit == 0) error<=1;
                    else begin
                        ci<=cfg_ci; co<=cfg_co; width<=cfg_width; height<=cfg_height;
                        kernel<=cfg_kernel; stride<=cfg_stride; padding<=cfg_padding; relu<=cfg_relu;
                        ow<=output_size(cfg_width,cfg_kernel,cfg_stride,cfg_padding);
                        oh<=output_size(cfg_height,cfg_kernel,cfg_stride,cfg_padding);
                        blocks<=cfg_ci == 1 ? 1 : cfg_ci >> 3;
                        ob<=0; ib<=0; ky<=0; kx<=0; oy<=0; ox<=0;
                        mac_pending<=0; q_send<=0; q_receive<=0;
                        limit_last<=cfg_cycle_limit-32'd1; busy<=1; state<=SETUP;
                    end
                end
                SETUP: begin plane_words<=ow*oh; state<=PARAM_REQ; end
                PARAM_REQ: state<=PARAM_USE;
                PARAM_USE: begin
                    accumulators<=bias_data; bias_latched<=bias_data;
                    multipliers<=multiplier_data; shifts<=shift_data;
                    state<=GEOMETRY;
                end
                GEOMETRY: begin
                    padding_pixel<=iy<0 || iy>=height || ix<0 || ix>=width;
                    input_row<=ib*height+iy;
                    weight_row<=(ob*kernel+ky)*kernel+kx;
                    pixel_row<=oy*ow; block_base<={plane_words,1'b0}*ob;
                    state<=ADDRESS_USE;
                end
                ADDRESS_USE: begin
                    input_address<=padding_pixel ? 16'd0 : input_row*width+ix;
                    weight_address<=weight_row*blocks+ib;
                    output_address_low<=block_base+pixel_row+ox;
                    state<=READ_REQ;
                end
                READ_REQ: begin
                    if (ib+1 < blocks) begin ib<=ib+1; state<=GEOMETRY; end
                    else begin
                        ib<=0;
                        if (kx+1 < kernel) begin kx<=kx+1; state<=GEOMETRY; end
                        else begin
                            kx<=0;
                            if (ky+1 < kernel) begin ky<=ky+1; state<=GEOMETRY; end
                            else begin ky<=0; state<=MAC_USE; end
                        end
                    end
                end
                MAC_USE: if(mac_valid && mac_pending==1) begin
                    q_send<=0; q_receive<=0; state<=QUANT;
                end
                QUANT, QUANT_WAIT: begin
                if(state==QUANT) begin
                    q_send<=q_send+1;
                    if(q_send==7) state<=QUANT_WAIT;
                end
                if(&quant_valid) begin
                if (|(quant_errors & active_outputs[q_receive*2 +: 2])) begin
                    busy<=0; done<=0; error<=1; state<=IDLE;
                end else begin
                    quantized[q_receive*16 +: 16] <= {
                        active_outputs[q_receive*2+1] ? quant_results[15:8] : 8'd0,
                        active_outputs[q_receive*2] ? quant_results[7:0] : 8'd0};
                    q_receive<=q_receive+1;
                    if(q_receive==7) state<=WRITE_LOW;
                end
                end
                end
                WRITE_LOW: state <= co > ob*16+8 ? WRITE_HIGH : ADVANCE;
                WRITE_HIGH: state<=ADVANCE;
                ADVANCE: begin
                    if (ox+1 < ow) begin ox<=ox+1; accumulators<=bias_latched; state<=GEOMETRY; end
                    else begin
                        ox<=0;
                        if (oy+1 < oh) begin oy<=oy+1; accumulators<=bias_latched; state<=GEOMETRY; end
                        else begin
                            oy<=0;
                            if ((ob+1)*16 < co) begin ob<=ob+1; state<=PARAM_REQ; end
                            else begin busy<=0; done<=1; state<=IDLE; end
                        end
                    end
                end
                default: begin busy<=0; done<=0; error<=1; state<=IDLE; end
            endcase
            end
        end
    end
endmodule
