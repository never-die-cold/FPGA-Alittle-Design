# -*- coding: utf-8 -*-
"""按 RISC-V Unprivileged ISA 规范独立实现 RV32I 汇编<->机器码，用于校验教程例题。"""
REGS = {f"x{i}": i for i in range(32)}
ABI = ["zero","ra","sp","gp","tp","t0","t1","t2","s0","s1","a0","a1","a2","a3","a4","a5","a6","a7",
       "s2","s3","s4","s5","s6","s7","s8","s9","s10","s11","t3","t4","t5","t6"]
for i, n in enumerate(ABI):
    REGS[n] = i

R = {"add":(0,0), "sub":(0,0x20), "sll":(1,0), "slt":(2,0),
     "sltu":(3,0), "xor":(4,0), "srl":(5,0), "sra":(5,0x20),
     "or":(6,0), "and":(7,0)}
I = {"addi":(0x13,0), "slti":(0x13,2), "sltiu":(0x13,3), "xori":(0x13,4),
     "ori":(0x13,6), "andi":(0x13,7), "jalr":(0x67,0), "lb":(0x03,0), "lh":(0x03,1),
     "lw":(0x03,2), "lbu":(0x03,4), "lhu":(0x03,5)}
S = {"sb":(0x23,0), "sh":(0x23,1), "sw":(0x23,2)}
B = {"beq":(0x63,0), "bne":(0x63,1), "blt":(0x63,4), "bge":(0x63,5), "bltu":(0x63,6), "bgeu":(0x63,7)}

def sext(v, bits):
    if v < 0: v = (1 << bits) + v
    return v & ((1 << bits) - 1)

def enc_r(op, rd, rs1, rs2):
    f3, f7 = R[op]
    return (f7<<25)|(rs2<<20)|(rs1<<15)|(f3<<12)|(rd<<7)|0x33
def enc_i(op, rd, rs1, imm):
    opc, f3 = I[op]
    return (sext(imm,12)<<20)|(rs1<<15)|(f3<<12)|(rd<<7)|opc
def enc_s(op, rs2, rs1, imm):
    opc, f3 = S[op]
    i = sext(imm,12)
    return ((i>>5)<<25)|(rs2<<20)|(rs1<<15)|(f3<<12)|((i&0x1f)<<7)|opc
def enc_b(op, rs1, rs2, imm):
    opc, f3 = B[op]
    i = sext(imm,13)
    return (((i>>12)&1)<<31)|(((i>>5)&0x3f)<<25)|(rs2<<20)|(rs1<<15)|(f3<<12)|(((i>>1)&0xf)<<8)|(((i>>11)&1)<<7)|opc
def enc_u(op, rd, imm):
    opc = 0x37 if op=="lui" else 0x17
    return ((sext(imm,20)&0xfffff)<<12)|(rd<<7)|opc
def enc_j(op, rd, imm):
    i = sext(imm,21)
    return (((i>>20)&1)<<31)|(((i>>1)&0x3ff)<<21)|(((i>>11)&1)<<20)|(((i>>12)&0xff)<<12)|(rd<<7)|0x6f

def parse_imm(s):
    return int(s, 0)

def asm_to_int(asm):
    t = asm.replace(",", " ").split()
    op = t[0]
    if op in R:
        rd, rs1, rs2 = (REGS[x] for x in t[1:4]); return enc_r(op, rd, rs1, rs2)
    if op in ("addi","slti","sltiu","xori","ori","andi"):
        return enc_i(op, REGS[t[1]], REGS[t[2]], parse_imm(t[3]))
    if op in ("slli","srli","srai"):
        f3 = 1 if op=="slli" else 5
        f7 = 0x20 if op=="srai" else 0
        return (f7<<25)|((parse_imm(t[3])&0x1f)<<20)|(REGS[t[2]]<<15)|(f3<<12)|(REGS[t[1]]<<7)|0x13
    if op in ("lb","lh","lw","lbu","lhu"):
        m = t[2].split("("); return enc_i(op, REGS[t[1]], REGS[m[1].rstrip(")")], parse_imm(m[0]))
    if op == "jalr":
        if len(t) == 3:
            m = t[2].split("("); return enc_i("jalr", REGS[t[1]], REGS[m[1].rstrip(")")], parse_imm(m[0]))
        return enc_i("jalr", REGS[t[1]], REGS[t[2]], parse_imm(t[3]))
    if op in S:
        m = t[2].split("("); return enc_s(op, REGS[t[1]], REGS[m[1].rstrip(")")], parse_imm(m[0]))
    if op in B:
        return enc_b(op, REGS[t[1]], REGS[t[2]], parse_imm(t[3]))
    if op in ("lui","auipc"):
        return enc_u(op, REGS[t[1]], parse_imm(t[2]))
    if op == "jal":
        return enc_j(op, REGS[t[1]], parse_imm(t[2]))
    raise ValueError(op)

def binstr(w):
    return format(w, "032b")

def decode(w):
    opc = w & 0x7f; rd = (w>>7)&0x1f; f3 = (w>>12)&7; rs1=(w>>15)&0x1f; rs2=(w>>20)&0x1f; f7=(w>>25)&0x7f
    rn = lambda r: f"x{r}"
    if opc==0x33:
        m = {(0,0):"add",(0,0x20):"sub",(1,0):"sll",(2,0):"slt",(3,0):"sltu",(4,0):"xor",(5,0):"srl",(5,0x20):"sra",(6,0):"or",(7,0):"and"}
        o = m[(f3,f7)]; return f"{o} {rn(rd)}, {rn(rs1)}, {rn(rs2)}"
    if opc==0x13:
        if f3 in (1,5):
            shamt = (w>>20)&0x1f
            o = "slli" if f3==1 else ("srai" if (w>>30)&1 else "srli")
            return f"{o} {rn(rd)}, {rn(rs1)}, {shamt}"
        imm = w>>20; imm = imm-(1<<12) if imm&(1<<11) else imm
        m={0:"addi",2:"slti",3:"sltiu",4:"xori",6:"ori",7:"andi"}
        return f"{m[f3]} {rn(rd)}, {rn(rs1)}, {imm}"
    if opc==0x03:
        imm = w>>20; imm = imm-(1<<12) if imm&(1<<11) else imm
        m={0:"lb",1:"lh",2:"lw",4:"lbu",5:"lhu"}
        return f"{m[f3]} {rn(rd)}, {imm}({rn(rs1)})"
    if opc==0x23:
        imm = ((w>>25)<<5)|((w>>7)&0x1f); imm = imm-(1<<12) if imm&(1<<11) else imm
        m={0:"sb",1:"sh",2:"sw"}
        return f"{m[f3]} {rn(rs2)}, {imm}({rn(rs1)})"
    if opc==0x63:
        i = (((w>>31)&1)<<12)|(((w>>7)&1)<<11)|(((w>>25)&0x3f)<<5)|(((w>>8)&0xf)<<1)
        i = i-(1<<13) if i&(1<<12) else i
        m={0:"beq",1:"bne",4:"blt",5:"bge",6:"bltu",7:"bgeu"}
        return f"{m[f3]} {rn(rs1)}, {rn(rs2)}, {i}"
    if opc in (0x37,0x17):
        o = "lui" if opc==0x37 else "auipc"; return f"{o} {rn(rd)}, 0x{w>>12:x}"
    if opc==0x6f:
        i=(((w>>31)&1)<<20)|(((w>>12)&0xff)<<12)|(((w>>20)&1)<<11)|(((w>>21)&0x3ff)<<1)
        i = i-(1<<21) if i&(1<<19) else i
        return f"jal {rn(rd)}, {i}"
    if opc==0x67:
        imm = w>>20; imm = imm-(1<<12) if imm&(1<<11) else imm
        return f"jalr {rn(rd)}, {imm}({rn(rs1)})"
    raise ValueError(hex(w))

# ---------- 教程例题（手工算出的答案）----------
ASM_CASES = [
    ("E1",  "add x5, x6, x7",       "007302b3", "R-type"),
    ("E2",  "sub x10, x11, x12",    "40c58533", "R-type funct7=0x20"),
    ("E3",  "and x13, x14, x15",    "00f776b3", "R-type"),
    ("E4",  "addi x5, x6, -1",      "fff30293", "I-type 负立即数"),
    ("E5",  "addi x15, x15, 42",    "02a78793", "I-type"),
    ("E6",  "lw x10, 12(x11)",      "00c5a503", "I-type 访存"),
    ("E7",  "lbu x7, 8(x8)",        "00844383", "I-type funct3=4"),
    ("E8",  "sw x12, -4(x13)",      "fec6ae23", "S-type 负立即数"),
    ("E9",  "beq x5, x6, 16",       "00628863", "B-type"),
    ("E10", "bne x9, x0, -8",       "fe049ce3", "B-type 负偏移"),
    ("E11", "lui x5, 0x12345",      "123452b7", "U-type"),
    ("E12", "auipc x6, 0xabcde",    "abcde317", "U-type"),
    ("E13", "jal x1, 2048",         "001000ef", "J-type"),
    ("E14", "jalr x0, 0(x1)",       "00008067", "ret"),
    ("E15", "sll x5, x6, x7",       "007312b3", "R-type 移位"),
    ("E16", "sra x8, x9, x10",      "40a4d433", "R-type funct7=0x20"),
    ("E17", "slt x11, x12, x13",    "00d625b3", "R-type funct3=2"),
    ("E18", "xori x14, x15, 0xff",  "0ff7c713", "I-type 逻辑"),
    ("E19", "sh x7, 2(x9)",         "00749123", "S-type funct3=1"),
    ("E20", "blt x10, x11, 32",     "02b54063", "B-type funct3=4"),
    ("E21", "jal x1, -4",           "ffdff0ef", "J-type 负偏移"),
    ("E22", "sltiu x5, x6, 10",     "00a33293", "I-type funct3=3"),
]
DISASM_CASES = [
    ("D1", "007302b3"), ("D2", "40c58533"), ("D3", "fff28293"), ("D4", "00c5a503"),
    ("D5", "fec52c23"), ("D6", "00628863"), ("D7", "123452b7"), ("D8", "00008067"),
    ("D9", "800000ef"), ("D10","00279693"),
]

ok = True
print("== 校验：汇编 -> 机器码 ==")
for name, asm, expect, note in ASM_CASES:
    got = asm_to_int(asm)
    status = "OK " if format(got, "08x") == expect else "MISMATCH"
    if status != "OK ": ok = False
    print(f"{name} {status}  {asm:26s} 期望0x{expect} 实际0x{got:08x}  ({note})")

print("== 校验：机器码 -> 反汇编（双向一致性）==")
for name, h in DISASM_CASES:
    w = int(h, 16)
    a = decode(w)
    back = asm_to_int(a)
    status = "OK " if back == w else "MISMATCH"
    if status != "OK ": ok = False
    print(f"{name} {status}  0x{h} -> {a}")

print("ALL OK" if ok else "HAS MISMATCH")
