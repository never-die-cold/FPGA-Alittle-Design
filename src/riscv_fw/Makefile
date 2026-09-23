# RV32IM / RV32I 冒烟固件构建（统一工具链：MSYS2 ucrt64 riscv32-unknown-elf-gcc）
# 用法：mingw32-make
#   hello.*     —— RV32IM 全量冒烟（含 mul/divu，待 Part A 收尾补 M 后上核）
#   hello_v0.*  —— v0 核 RV32I 子集冒烟（当前核冒烟用）
#   mingw32-make clean

CROSS   := riscv32-unknown-elf-
CC      := $(CROSS)gcc
OBJDUMP := $(CROSS)objdump
OBJCOPY := $(CROSS)objcopy

COMMON  := -mcmodel=medany -mno-relax -O2 -Wall -Wextra -ffreestanding -nostdlib -nostartfiles -Wl,--build-id=none
ARCH_IM := -march=rv32im -mabi=ilp32
ARCH_I  := -march=rv32i  -mabi=ilp32

# CoreMark 构建（契约 docs/coremark_tb_contract.md §4.1；输出 coremark.hex/.dis 入库）
CM_SRCS  := start.S coremark/core_main.c coremark/core_portme.c \
            coremark/vendor/core_list_join.c coremark/vendor/core_matrix.c \
            coremark/vendor/core_state.c coremark/vendor/core_util.c
CM_FLAGS := -DTOTAL_DATA_SIZE=2000 -DITERATIONS=32 -Icoremark -Icoremark/vendor
CM_LD    := coremark/link_coremark.ld

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
all: $(TARGET).hex $(TARGET).dis $(V0_TARGET).hex $(V0_TARGET).dis $(TS_TARGET).hex $(TS_TARGET).dis coremark.hex coremark.dis

$(TARGET).elf: $(SRCS) link.ld
	$(CC) $(ARCH_IM) $(COMMON) -T link.ld $(SRCS) -o $@

$(V0_TARGET).elf: $(V0_SRCS) link.ld
	$(CC) $(ARCH_I) $(COMMON) -T link.ld $(V0_SRCS) -o $@

$(TS_TARGET).elf: $(TS_SRCS) link.ld
	$(CC) $(ARCH_I) $(COMMON) -T link.ld $(TS_SRCS) -o $@

coremark.elf: $(CM_SRCS) $(CM_LD)
	$(CC) $(ARCH_IM) $(COMMON) $(CM_FLAGS) -T $(CM_LD) $(CM_SRCS) -o $@

%.bin: %.elf
	$(OBJCOPY) -O binary $< $@

%.hex: %.bin bin2hex.py
	python bin2hex.py $< $@

%.dis: %.elf
	$(OBJDUMP) -d $< > $@

clean:
	-$(RM) $(TARGET).elf $(TARGET).bin $(TARGET).hex $(TARGET).dis $(V0_TARGET).elf $(V0_TARGET).bin $(V0_TARGET).hex $(V0_TARGET).dis $(TS_TARGET).elf $(TS_TARGET).bin $(TS_TARGET).hex $(TS_TARGET).dis coremark.elf coremark.bin coremark.hex coremark.dis
