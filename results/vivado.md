| unit | LUT | FF | DSP | Fmax (MHz) | latency (cyc) | op time (ns) |
|---|---:|---:|---:|---:|---:|---:|
| pico_mul | 225 | 255 | 0 | 414.9 | 36 | 86.8 |
| pico_fast_mul | 73 | 37 | 4 | 175.7 | 2 | 11.4 |
| booth_d1 | 217 | 110 | 0 | 230.6 | 18 | 78.1 |
| booth_d2 | 321 | 117 | 0 | 163.6 | 10 | 61.1 |
| booth_d4 | 533 | 116 | 0 | 105.8 | 6 | 56.7 |
| pico_div | 342 | 201 | 0 | 209.1 | 36 | 172.2 |
| restoring_b1 | 233 | 107 | 0 | 246.0 | 33 | 134.1 |
| restoring_b2 | 282 | 106 | 0 | 148.5 | 17 | 114.5 |
| restoring_b4 | 378 | 105 | 0 | 74.7 | 9 | 120.5 |

| core | LUT | FF | DSP | Fmax (MHz) | critical path end |
|---|---:|---:|---:|---:|---|
| stock_seq | 1884 | 1087 | 0 | 151.1 | cpu/mem_rdata_q_reg[28]/D |
| stock_fast | 1706 | 955 | 4 | 149.6 | cpu/decoded_rs1_reg_rep[1]/D |
| booth1 | 1729 | 854 | 0 | 146.4 | cpu/mem_rdata_q_reg[13]/CE |
| booth2 | 1859 | 849 | 0 | 141.7 | cpu/mem_rdata_q_reg[13]/CE |
| booth4 | 2201 | 851 | 0 | 73.7 | g_div.div/r_reg[0]/D |
