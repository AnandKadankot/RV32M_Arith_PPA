| unit | result | checks | latency (cycles) by funct3 |
|---|---|---:|---|
| pico_mul | PASS | 21024 | 0:36, 1:68, 2:68, 3:68 |
| pico_fast_mul | PASS | 21024 | 0:2, 1:2, 2:2, 3:2 |
| booth_d1 | PASS | 21024 | 0:18, 1:18, 2:18, 3:18 |
| booth_d2 | PASS | 21024 | 0:10, 1:10, 2:10, 3:10 |
| booth_d4 | PASS | 21024 | 0:6, 1:6, 2:6, 3:6 |
| pico_div | PASS | 21024 | 4:36, 5:36, 6:36, 7:36 |
| restoring_b1 | PASS | 21024 | 4:33, 5:33, 6:33, 7:33 |
| restoring_b2 | PASS | 21024 | 4:17, 5:17, 6:17, 7:17 |
| restoring_b4 | PASS | 21024 | 4:9, 5:9, 6:9, 7:9 |

| mutation test | injected bug | unit (P) | result | errors detected |
|---|---|---|---|---:|
| mut_booth_plus2m | Booth digit +2 uses +M instead of +2M | booth (1) | FAIL | 14887 |
| mut_booth_minus2m | Booth digit -2 uses -M instead of -2M | booth (1) | FAIL | 15855 |
| mut_booth_wrong_qm1 | Booth carries the wrong bit into the next digit | booth (2) | FAIL | 19760 |
| mut_mulhsu_rs1_unsigned | MULHSU treats rs1 as unsigned | booth (1) | FAIL | 2587 |
| mut_mulhsu_rs2_signed | MULHSU treats rs2 as signed | booth (1) | FAIL | 2567 |
| mut_mul_high_select | MULHSU returns the low word | booth (4) | FAIL | 5180 |
| mut_mul_no_wait | multiplier never raises pcpi_wait (core would trap after 16 cycles) | booth (1) | FAIL | 126144 |
| mut_div_by_zero_sign | signed x/0 negates the all-ones quotient | restoring (1) | FAIL | 19 |
| mut_rem_sign | remainder takes the quotient's sign instead of the dividend's | restoring (2) | FAIL | 2502 |
| mut_div_no_restore | trial subtraction is kept even when it borrows | restoring (4) | FAIL | 20849 |
| mut_div_short_count | divider stops one iteration early | restoring (2) | FAIL | 19530 |
| mut_div_no_wait | divider never raises pcpi_wait (core would trap after 16 cycles) | restoring (1) | FAIL | 441504 |

**Mutation detection rate: 12/12 = 100%**
