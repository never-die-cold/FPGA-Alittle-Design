`timescale 1ns/1ps
module tb_branch_predict;
    reg clk, rst_n, lookup_valid, update_valid, update_taken;
    reg [31:0] lookup_pc, update_pc;
    wire p0_taken, p1_taken, p2_taken;
    wire [1:0] p0_state, p1_state, p2_state;
    integer checks, lookups, hits, misses;
    branch_predict #(.BHT_MODE(0), .INDEX_BITS(2)) p0 (
        .clk(clk),.rst_n(rst_n),.lookup_valid(lookup_valid),.lookup_pc(lookup_pc),.predict_taken(p0_taken),.lookup_state(p0_state),.update_valid(update_valid),.update_pc(update_pc),.update_taken(update_taken));
    branch_predict #(.BHT_MODE(1), .INDEX_BITS(2)) p1 (
        .clk(clk),.rst_n(rst_n),.lookup_valid(lookup_valid),.lookup_pc(lookup_pc),.predict_taken(p1_taken),.lookup_state(p1_state),.update_valid(update_valid),.update_pc(update_pc),.update_taken(update_taken));
    branch_predict #(.BHT_MODE(2), .INDEX_BITS(2)) p2 (
        .clk(clk),.rst_n(rst_n),.lookup_valid(lookup_valid),.lookup_pc(lookup_pc),.predict_taken(p2_taken),.lookup_state(p2_state),.update_valid(update_valid),.update_pc(update_pc),.update_taken(update_taken));

    always #5 clk = ~clk;
    task check; input ok; input [255:0] label; begin
        checks = checks + 1;
        if (!ok) begin $display("FAIL: %0s", label); $finish; end
    end endtask
    task observe; input actual; begin
        lookups = lookups + 1;
        if (p2_taken == actual) hits = hits + 1; else misses = misses + 1;
        check(hits + misses == lookups, "hit+miss equals lookup each cycle");
    end endtask
    task train; input actual; begin
        update_taken = actual; update_valid = 1'b1; #1; observe(actual);
        @(posedge clk); #1; update_valid = 1'b0;
    end endtask

    initial begin
        clk=0; rst_n=0; lookup_valid=1; lookup_pc=0; update_valid=0;
        update_pc=0; update_taken=0; checks=0; lookups=0; hits=0; misses=0;
        repeat (2) @(posedge clk); rst_n=1; #1;
        check(!p0_taken && !p1_taken && !p2_taken && p2_state==0, "reset predicts not taken");
        update_taken=1; update_valid=1; #1; observe(1);
        check(p1_state==0 && p2_state==0, "read before write exposes old state");
        @(posedge clk); #1; update_valid=0;
        check(p0_state==0 && p1_state==3 && p2_state==1, "first taken update and off mode");
        train(1); check(p2_state==2, "weak taken");
        train(1); check(p2_state==3, "strong taken");
        train(1); check(p2_state==3, "taken saturation");
        train(0); check(p1_state==0 && p2_state==2, "direction flip starts fallback");
        train(0); check(p2_state==1, "weak not taken");
        train(0); check(p2_state==0, "strong not taken");
        train(0); check(p2_state==0, "not-taken saturation");
        lookup_pc=4; #1; check(p1_state==0 && p2_state==0, "independent reset entry");
        check(lookups==8 && hits==4 && misses==4, "per-cycle hit accounting");
        lookup_valid=0; #1; check(!p1_taken && !p2_taken, "invalid lookup is not taken");
        $display("PASS: tb_branch_predict (%0d checks)", checks); $finish;
    end
endmodule
