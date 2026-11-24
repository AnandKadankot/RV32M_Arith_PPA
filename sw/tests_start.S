# tests_start.S - runs the riscv-tests (as packaged with PicoRV32) back to back.
# Each test is assembled as a function: it prints its name, then "OK" on pass
# and jumps to <name>_ret, or prints "ERROR" and executes ebreak on failure
# (the testbench stops on the resulting trap). Exit code 0 = all passed.
	.section .text.start
	.global _start
_start:
	la	sp, _stack_top
#define TEST(n) .global n; .global n##_ret; jal zero, n; n##_ret:
	TEST(lui)
	TEST(auipc)
	TEST(j)
	TEST(jal)
	TEST(jalr)
	TEST(beq)
	TEST(bne)
	TEST(blt)
	TEST(bge)
	TEST(bltu)
	TEST(bgeu)
	TEST(lb)
	TEST(lh)
	TEST(lw)
	TEST(lbu)
	TEST(lhu)
	TEST(sb)
	TEST(sh)
	TEST(sw)
	TEST(addi)
	TEST(slti)
	TEST(xori)
	TEST(ori)
	TEST(andi)
	TEST(slli)
	TEST(srli)
	TEST(srai)
	TEST(add)
	TEST(sub)
	TEST(sll)
	TEST(slt)
	TEST(xor)
	TEST(srl)
	TEST(sra)
	TEST(or)
	TEST(and)
	TEST(simple)
	TEST(mul)
	TEST(mulh)
	TEST(mulhsu)
	TEST(mulhu)
	TEST(div)
	TEST(divu)
	TEST(rem)
	TEST(remu)
	li	t0, 0x20000000
	sw	zero, 0(t0)
1:	j	1b
