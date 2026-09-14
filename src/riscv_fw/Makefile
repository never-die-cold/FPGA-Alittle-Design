# RV32IM / RV32I 冒烟固件构建（统一工具链：MSYS2 ucrt64 riscv32-unknown-elf-gcc）
# 用法：mingw32-make
#   hello.*     —— RV32IM 全量冒烟（含 mul/divu，待 Part A 收尾补 M 后上核）
#   hello_v0.*  —— v0 核 RV32I 子集冒烟（当前核冒烟用）
#   mingw32-make clean

CROSS   := riscv32-unknown-elf-
CC      := $(CROSS)gcc
OBJDUMP := $(CROSS)objdump
OBJCOPY := $(CROSS)objcopy

COMMON  := -mcmodel=medany -mno-relax -O2 -Wall -Wextra -ffreestanding -nostdlib -nostartfiles -T link.ld -Wl,--build-id=none
ARCH_IM := -march=rv32im -mabi=ilp32
ARCH_I  := -march=rv32i  -mabi=ilp32

TARGET    := hello
SRCS      := start.S main.c
V0_TARGET := hello_v0
V0_SRCS   := start.S main_v0.c
TS_TARGET := hello_test
TS_SRCS   := start.S test_rv32i.S

ifeq ($(OS),Windows_NT)
RM := del /q
else
RM := rm -f
endif

.PHONY: all clean
all: $(TARGET).hex $(TARGET).dis $(V0_TARGET).hex $(V0_TARGET).dis $(TS_TARGET).hex $(TS_TARGET).dis

$(TARGET).elf: $(SRCS) link.ld
	$(CC) $(ARCH_IM) $(COMMON) $(SRCS) -o $@

$(V0_TARGET).elf: $(V0_SRCS) link.ld
	$(CC) $(ARCH_I) $(COMMON) $(V0_SRCS) -o $@

$(TS_TARGET).elf: $(TS_SRCS) link.ld
	$(CC) $(ARCH_I) $(COMMON) $(TS_SRCS) -o $@

%.bin: %.elf
	$(OBJCOPY) -O binary $< $@

%.hex: %.bin bin2hex.py
	python bin2hex.py $< $@

%.dis: %.elf
	$(OBJDUMP) -d $< > $@

clean:
	-$(RM) $(TARGET).elf $(TARGET).bin $(TARGET).hex $(TARGET).dis $(V0_TARGET).elf $(V0_TARGET).bin $(V0_TARGET).hex $(V0_TARGET).dis $(TS_TARGET).elf $(TS_TARGET).bin $(TS_TARGET).hex $(TS_TARGET).dis
