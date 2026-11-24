/* bench.c - kernels that exercise each class of RV32M instruction.
 *
 *   matmul32  16x16 int32 matrix multiply           -> MUL
 *   fixmul    Q16.16 fixed-point products, N=1024   -> MUL + MULH
 *   radix     256 uint32 values printed in a random
 *             base (2..36) chosen at run time       -> DIVU + REMU
 *   sdiv      1024 signed quotients and remainders  -> DIV + REM
 *
 * Divisors are run-time values on purpose: GCC replaces division by a
 * constant with a multiply-high sequence, which would not exercise DIV at all.
 *
 * Output: "RESULT <kernel> cycles=<n> value=<checksum>". Checksums are verified
 * on the host by scripts/run_system.py against an independent Python model.
 */
#include <stdint.h>

#define MM 16
#define NF 1024
#define NR 256
#define ND 1024

#define CONSOLE (*(volatile uint32_t *)0x10000000)

static void putstr(const char *s) { while (*s) CONSOLE = *s++; }

/* print without using division (the divider is one of the units under test) */
static void putdec(uint32_t u)
{
	static const uint32_t p10[10] = {1000000000u, 100000000u, 10000000u, 1000000u,
	                                 100000u, 10000u, 1000u, 100u, 10u, 1u};
	int started = 0;
	for (int i = 0; i < 10; i++) {
		char d = '0';
		while (u >= p10[i]) { u -= p10[i]; d++; }
		if (d != '0' || started || i == 9) { CONSOLE = d; started = 1; }
	}
}

static inline uint32_t rdcycle(void)
{
	uint32_t c;
	__asm__ volatile ("rdcycle %0" : "=r"(c));
	return c;
}

static int32_t  ma[MM][MM], mb[MM][MM], mc[MM][MM];
static int32_t  fx[NF], fy[NF];
static uint32_t rv[NR], rb[NR];
static int32_t  da[ND], db[ND];

static uint32_t lcg_state = 12345u;
static uint32_t lcg(void) { lcg_state = lcg_state * 1103515245u + 12345u; return lcg_state; }

static void init_data(void)
{
	for (int i = 0; i < MM; i++)
		for (int j = 0; j < MM; j++) { ma[i][j] = (int32_t)lcg(); mb[i][j] = (int32_t)lcg(); }
	for (int i = 0; i < NF; i++) { fx[i] = (int32_t)lcg(); fy[i] = (int32_t)lcg(); }
	for (int i = 0; i < NR; i++) { rv[i] = lcg(); rb[i] = 2 + (lcg() >> 16) % 35; }
	for (int i = 0; i < ND; i++) { da[i] = (int32_t)lcg(); db[i] = ((int32_t)lcg() >> 20) | 1; }
}

__attribute__((noipa)) static uint32_t matmul32(void)
{
	uint32_t chk = 0;
	for (int i = 0; i < MM; i++)
		for (int j = 0; j < MM; j++) {
			int32_t s = 0;
			for (int k = 0; k < MM; k++) s += ma[i][k] * mb[k][j];
			mc[i][j] = s;
			chk = chk * 31u + (uint32_t)s;
		}
	return chk;
}

__attribute__((noipa)) static uint32_t fixmul(const int32_t *x, const int32_t *y, int n)
{
	uint32_t acc = 0;
	for (int i = 0; i < n; i++)
		acc += (uint32_t)(int32_t)(((int64_t)x[i] * y[i]) >> 16);
	return acc;
}

__attribute__((noipa)) static uint32_t radix(const uint32_t *v, const uint32_t *base, int n)
{
	uint32_t chk = 0;
	for (int i = 0; i < n; i++) {
		uint32_t x = v[i], b = base[i];
		do {
			chk = chk * 31u + x % b;
			x /= b;
		} while (x);
	}
	return chk;
}

__attribute__((noipa)) static uint32_t sdiv(const int32_t *a, const int32_t *b, int n)
{
	uint32_t acc = 0;
	for (int i = 0; i < n; i++)
		acc += (uint32_t)(a[i] / b[i]) * 3u + (uint32_t)(a[i] % b[i]);
	return acc;
}

static void report(const char *name, uint32_t cycles, uint32_t value)
{
	putstr("RESULT "); putstr(name);
	putstr(" cycles="); putdec(cycles);
	putstr(" value="); putdec(value);
	putstr("\n");
}

#define BENCH(name, expr) do {                  \
		uint32_t t0 = rdcycle();                \
		uint32_t v = (expr);                    \
		uint32_t t1 = rdcycle();                \
		report(name, t1 - t0, v);               \
	} while (0)

int main(void)
{
	init_data();
	BENCH("matmul32", matmul32());
	BENCH("fixmul",   fixmul(fx, fy, NF));
	BENCH("radix",    radix(rv, rb, NR));
	BENCH("sdiv",     sdiv(da, db, ND));
	putstr("BENCH DONE\n");
	return 0;
}
