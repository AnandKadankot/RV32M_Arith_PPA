# Firmware images:
#   build/riscv_tests.hex - 45 riscv-tests (rv32ui + rv32um) from PicoRV32's tests/
#   build/bench.hex       - M-extension benchmark kernels (rv32imc)
TOOLCHAIN ?= $(HOME)/AMD/2025.2/gnu/riscv/lin/bin/riscv64-unknown-elf-
CC      = $(TOOLCHAIN)gcc
OBJCOPY = $(TOOLCHAIN)objcopy
OBJDUMP = $(TOOLCHAIN)objdump
TESTDIR = ../third_party/picorv32/tests
TESTS   = lui auipc j jal jalr beq bne blt bge bltu bgeu lb lh lw lbu lhu sb sh sw addi slti xori ori andi slli srli srai add sub sll slt xor srl sra or and simple mul mulh mulhsu mulhu div divu rem remu
CFLAGS  = -mabi=ilp32 -O2 -ffreestanding -fno-builtin -nostdlib -Wall -Wextra
LDFLAGS = -T link.ld -Wl,--gc-sections,--no-warn-rwx-segments -Wl,--build-id=none -lgcc
OUT     = build

all: $(OUT)/riscv_tests.hex $(OUT)/bench.hex

$(OUT)/test_%.o: $(TESTDIR)/%.S | $(OUT)
	$(CC) -march=rv32im -mabi=ilp32 -c -I$(TESTDIR) -DTEST_FUNC_NAME=$* \
		-DTEST_FUNC_TXT='"$*"' -DTEST_FUNC_RET=$*_ret $< -o $@

$(OUT)/riscv_tests.elf: tests_start.S $(patsubst %,$(OUT)/test_%.o,$(TESTS)) link.ld
	$(CC) -march=rv32im $(CFLAGS) tests_start.S $(patsubst %,$(OUT)/test_%.o,$(TESTS)) -o $@ $(LDFLAGS)

$(OUT)/bench.elf: start.S bench.c link.ld | $(OUT)
	$(CC) -march=rv32imc $(CFLAGS) start.S bench.c -o $@ $(LDFLAGS)

$(OUT)/%.hex: $(OUT)/%.elf
	$(OBJCOPY) -O binary $< $(OUT)/$*.bin
	python3 ../scripts/bin2hex.py $(OUT)/$*.bin $@
	$(OBJDUMP) -d $< > $(OUT)/$*.lst

$(OUT):
	mkdir -p $@

clean:
	rm -rf $(OUT)
.PHONY: all clean
