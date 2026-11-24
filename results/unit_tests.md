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

| mutation test | expected | result | errors detected |
|---|---|---|---:|
| mut_booth_plus2m | FAIL | FAIL | 14887 |
| mut_div_by_zero_sign | FAIL | FAIL | 19 |
