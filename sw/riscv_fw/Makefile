# RV32IM 冒烟固件构建（统一工具链：MSYS2 ucrt64 riscv32-unknown-elf-gcc）
# 用法：mingw32-make（产出 hello.elf / hello.dis / hello.bin / hello.hex）
#       mingw32-make clean

CROSS   := riscv32-unknown-elf-
CC      := $(CROSS)gcc
OBJDUMP := $(CROSS)objdump
OBJCOPY := $(CROSS)objcopy

ARCH    := -march=rv32im -mabi=ilp32
CFLAGS  := $(ARCH) -mcmodel=medany -mno-relax -O2 -Wall -Wextra -ffreestanding
LDFLAGS := $(ARCH) -nostdlib -nostartfiles -T link.ld -Wl,--build-id=none

TARGET  := hello
SRCS    := start.S main.c

ifeq ($(OS),Windows_NT)
RM := del /q
else
RM := rm -f
endif

.PHONY: all clean
all: $(TARGET).hex $(TARGET).dis

$(TARGET).elf: $(SRCS) link.ld
	$(CC) $(CFLAGS) $(SRCS) $(LDFLAGS) -o $@

$(TARGET).bin: $(TARGET).elf
	$(OBJCOPY) -O binary $< $@

$(TARGET).hex: $(TARGET).bin bin2hex.py
	python bin2hex.py $< $@

$(TARGET).dis: $(TARGET).elf
	$(OBJDUMP) -d $< > $@

clean:
	-$(RM) $(TARGET).elf $(TARGET).bin $(TARGET).hex $(TARGET).dis
