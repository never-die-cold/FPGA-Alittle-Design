`timescale 1ns / 1ps
module pynq_z2_smoke_tb;
    parameter integer DIV_CYCLES = 5;
    reg clk = 0;
    reg btn0 = 0;
    wire [3:0] led;
    integer step;
    integer tick;
    reg [3:0] expected;

    pynq_z2_smoke_top #(.DIV_CYCLES(DIV_CYCLES)) dut (
        .clk(clk), .btn0(btn0), .led(led)
    );
    always #4 clk = ~clk;

    task check_led;
        input [3:0] wanted;
        begin
            if (led !== wanted) begin
                $display("TEST FAILED: DIV=%0d time=%0t expected=%b actual=%b",
                         DIV_CYCLES, $time, wanted, led);
                $fatal(1);
            end
        end
    endtask

    // Check every clock, including the cycles on which LEDs must not move.
    task check_rotations;
        begin
            expected = 4'b0001;
            for (step = 0; step < 12; step = step + 1) begin
                for (tick = 1; tick <= DIV_CYCLES; tick = tick + 1) begin
                    @(posedge clk);
                    #1;
                    if (tick == DIV_CYCLES) begin
                        case (expected)
                            4'b0001: expected = 4'b0010;
                            4'b0010: expected = 4'b0100;
                            4'b0100: expected = 4'b1000;
                            4'b1000: expected = 4'b0001;
                            default: expected = 4'bxxxx;
                        endcase
                    end
                    check_led(expected);
                end
            end
        end
    endtask

    initial begin
        if (DIV_CYCLES < 1) begin
            $display("TEST FAILED: DIV_CYCLES must be positive");
            $fatal(1);
        end
        // Configuration initial state, without an external reset pulse.
        #1;
        check_led(4'b0001);
        repeat (2) begin
            @(posedge clk); #1; check_led(4'b0001);
        end
        check_rotations;

        // Reach a noninitial LED and interrupt a partly completed interval.
        repeat (DIV_CYCLES + DIV_CYCLES / 2) @(posedge clk);
        @(negedge clk); #1; btn0 = 1;
        repeat (4) begin
            @(posedge clk); #1; check_led(4'b0001);
        end
        @(negedge clk); #1; btn0 = 0;
        repeat (2) begin
            @(posedge clk); #1; check_led(4'b0001);
        end
        check_rotations;
        $display("TEST PASSED: DIV_CYCLES=%0d, startup/reset/24 steps", DIV_CYCLES);
        $finish;
    end

    initial begin
        #(8 * (40 * DIV_CYCLES + 100));
        $display("TEST FAILED: watchdog timeout");
        $fatal(1);
    end
endmodule
