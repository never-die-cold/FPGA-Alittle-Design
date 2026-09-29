`timescale 1ns/1ps

module tb_decode;
    reg  [31:0] instr;
    wire        uses_rs1;
    wire        uses_rs2;
    integer     checks;

    decode dut (
        .instr(instr),
        .uses_rs1(uses_rs1),
        .uses_rs2(uses_rs2)
    );

    task check_use;
        input [31:0] test_instr;
        input        expected_rs1;
        input        expected_rs2;
        begin
            instr = test_instr;
            #1;
            checks = checks + 1;
            if ((uses_rs1 !== expected_rs1) ||
                (uses_rs2 !== expected_rs2)) begin
                $display("FAIL: instr=%08x uses=%b%b expected=%b%b",
                         instr, uses_rs1, uses_rs2,
                         expected_rs1, expected_rs2);
                $fatal(1);
            end
        end
    endtask

    initial begin
        checks = 0;
        check_use(32'h123450b7, 1'b0, 1'b0); // lui
        check_use(32'h12345097, 1'b0, 1'b0); // auipc
        check_use(32'h008000ef, 1'b0, 1'b0); // jal
        check_use(32'h000100e7, 1'b1, 1'b0); // jalr
        check_use(32'h00208063, 1'b1, 1'b1); // beq
        check_use(32'h00012083, 1'b1, 1'b0); // lw
        check_use(32'h00112023, 1'b1, 1'b1); // sw
        check_use(32'h00110093, 1'b1, 1'b0); // addi
        check_use(32'h002081b3, 1'b1, 1'b1); // add
        check_use(32'h022081b3, 1'b1, 1'b1); // mul
        check_use(32'h00000000, 1'b0, 1'b0); // unsupported
        $display("PASS: decode source-use flags (%0d cases)", checks);
        $finish;
    end
endmodule
