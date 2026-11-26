## nangate45 (clock target 2.0 ns)

### Area by stage (standard-cell µm²) and timing after routing

| unit | synth | placed | CTS | routed | util % | setup WNS (ns) | setup TNS (ns) | hold WNS (ns) | Fmax placed → routed (MHz) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pico_mul | 2454.4 | 2530.7 | 2608.7 | 2608.7 | 43.4 | +1.233 | 0.000 | +0.084 | 1122.6 → 1304.4 |
| pico_fast_mul | 8159.0 | 8141.7 | 8184.6 | 8184.6 | 40.6 | +0.202 | 0.000 | +0.108 | 555.4 → 556.1 |
| booth_d1 | 1580.3 | 1639.4 | 1658.5 | 1658.5 | 42.9 | +0.885 | 0.000 | +0.101 | 894.7 → 896.5 |
| booth_d2 | 2171.1 | 2184.9 | 2206.2 | 2206.2 | 41.2 | +0.479 | 0.000 | +0.103 | 666.5 → 657.6 |
| booth_d4 | 3016.7 | 3280.6 | 3321.5 | 3456.4 | 46.7 | +0.032 | 0.000 | +0.100 | 497.6 → 508.3 |
| pico_div | 2820.1 | 2865.9 | 2902.1 | 2902.1 | 41.9 | +1.069 | 0.000 | +0.112 | 959.5 → 1073.6 |
| restoring_b1 | 1846.8 | 1885.9 | 1905.4 | 1905.4 | 41.9 | +0.786 | 0.000 | +0.104 | 904.1 → 823.6 |
| restoring_b2 | 2249.8 | 2268.7 | 2285.7 | 2285.7 | 41.3 | +0.607 | 0.000 | +0.104 | 720.8 → 717.9 |
| restoring_b4 | 3036.4 | 3661.0 | 3773.2 | 3834.7 | 51.7 | -0.207 | -6.496 | +0.105 | 446.8 → 453.1 |

### Clock tree, routing and congestion

| unit | skew (ps) | clk bufs+invs | clk cell area (µm²) | repair bufs | wirelength (µm) | vias | GR usage % | busiest layer | overflow | DRC |
|---|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| pico_mul | 3.7 | 60+13 | 77.94 | 133 | 10182 | 8238 | 10.52 | metal2 30.81% | 0 | 0 |
| pico_fast_mul | 7.4 | 17+15 | 42.83 | 216 | 47011 | 24091 | 15.65 | metal2 47.14% | 0 | 0 |
| booth_d1 | 3.6 | 11+5 | 19.15 | 129 | 8721 | 6796 | 14.33 | metal2 40.98% | 0 | 0 |
| booth_d2 | 4.7 | 9+7 | 21.28 | 134 | 13680 | 10204 | 16.11 | metal2 46.03% | 0 | 0 |
| booth_d4 | 6.3 | 19+13 | 36.44 | 448 | 23503 | 16100 | 19.45 | metal2 48.41% | 0 | 0 |
| pico_div | 7.9 | 17+15 | 36.18 | 132 | 15284 | 11566 | 13.94 | metal2 38.66% | 0 | 0 |
| restoring_b1 | 5.4 | 9+7 | 19.42 | 128 | 10052 | 7893 | 14.23 | metal2 45.56% | 0 | 0 |
| restoring_b2 | 3.9 | 10+5 | 17.02 | 133 | 13874 | 10136 | 15.56 | metal2 43.4% | 0 | 0 |
| restoring_b4 | 5.0 | 10+6 | 20.48 | 832 | 22647 | 17037 | 19.03 | metal2 48.93% | 0 | 0 |

### Routed metal area (wire length × drawn width, from the final DEF)

| unit | signal wire (µm) | signal metal (µm²) | signal metal / cell area | clock wire (µm) | clock metal (µm²) | signal metal by layer (µm²) |
|---|---:|---:|---:|---:|---:|---|
| pico_mul | 8644 | 631.9 | 0.24 | 1539 | 141.7 | metal2 297, metal3 281, metal4 34, metal5 9, metal6 10 |
| pico_fast_mul | 45693 | 3537.5 | 0.43 | 1318 | 127.5 | metal2 1517, metal3 1342, metal4 570, metal5 79, metal6 30 |
| booth_d1 | 8044 | 625.2 | 0.38 | 677 | 59.8 | metal2 259, metal3 242, metal4 102, metal5 3, metal6 19 |
| booth_d2 | 12945 | 1041.7 | 0.47 | 735 | 67.5 | metal2 406, metal3 364, metal4 222, metal5 20, metal6 28 |
| booth_d4 | 22567 | 1796.3 | 0.52 | 936 | 78.9 | metal2 623, metal3 740, metal4 291, metal5 124, metal6 19 |
| pico_div | 14248 | 1063.5 | 0.37 | 1036 | 88.7 | metal2 437, metal3 494, metal4 94, metal5 30, metal6 8 |
| restoring_b1 | 9349 | 707.7 | 0.37 | 703 | 60.0 | metal2 334, metal3 267, metal4 89, metal5 7, metal6 11 |
| restoring_b2 | 13147 | 1017.7 | 0.45 | 728 | 62.8 | metal2 413, metal3 410, metal4 156, metal5 19, metal6 20 |
| restoring_b4 | 21993 | 1755.9 | 0.46 | 655 | 55.1 | metal2 616, metal3 707, metal4 295, metal5 109, metal6 29 |

### Power (simulation-annotated) and energy per operation

| unit | internal (mW) | switching (mW) | leakage (µW) | total (mW) | clock tree (mW) | nets annotated | cycles/op | energy/op (pJ) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| pico_mul | 1.070 | 0.398 | 52.1 | 1.520 | 0.545 | 1744/1746 | 62.78 | 190.85 |
| pico_fast_mul | 1.020 | 0.760 | 146 | 1.930 | 0.357 | 4989/4991 | 5.0 | 19.31 |
| booth_d1 | 0.648 | 0.386 | 34.8 | 1.070 | 0.184 | 1240/1242 | 21.0 | 44.94 |
| booth_d2 | 0.771 | 0.569 | 48.4 | 1.390 | 0.209 | 1694/1696 | 13.0 | 36.15 |
| booth_d4 | 1.080 | 0.872 | 82.2 | 2.040 | 0.286 | 2673/2675 | 9.0 | 36.73 |
| pico_div | 0.901 | 0.431 | 62.2 | 1.390 | 0.340 | 2144/2146 | 39.0 | 108.43 |
| restoring_b1 | 0.535 | 0.293 | 41.5 | 0.870 | 0.191 | 1461/1463 | 36.0 | 62.64 |
| restoring_b2 | 0.613 | 0.388 | 49.3 | 1.050 | 0.175 | 1794/1796 | 20.0 | 42.0 |
| restoring_b4 | 0.954 | 0.672 | 91.8 | 1.720 | 0.195 | 3189/3191 | 12.0 | 41.29 |

### Gate-level simulation of the routed netlist (tb_unit, zero delay)

| unit | flip-flops start at X | all start at 0 | all start at 1 | note |
|---|---|---|---|---|
| pico_mul | PASS (2024 checks) | PASS (2024 checks) | PASS (2024 checks) |  |
| pico_fast_mul | PASS (2024 checks) | PASS (2024 checks) | PASS (2024 checks) |  |
| booth_d1 | PASS (2024 checks) | PASS (2024 checks) | PASS (2024 checks) |  |
| booth_d2 | FAIL (2024 checks, 1 errors) | PASS (2024 checks) | PASS (2024 checks) | X-pessimism only: passes with any defined power-up state (FAIL f3=0 a=00000000 b=00000000 got=00X00000 exp=00000000 ready=1 lat=10) |
| booth_d4 | PASS (2024 checks) | PASS (2024 checks) | PASS (2024 checks) |  |
| pico_div | PASS (2024 checks) | PASS (2024 checks) | PASS (2024 checks) |  |
| restoring_b1 | PASS (2024 checks) | PASS (2024 checks) | PASS (2024 checks) |  |
| restoring_b2 | PASS (2024 checks) | PASS (2024 checks) | PASS (2024 checks) |  |
| restoring_b4 | PASS (2024 checks) | PASS (2024 checks) | PASS (2024 checks) |  |

### Critical path (after routing)

| unit | start → end | logic depth | clk→Q (ns) | logic (ns) | arrival (ns) | main cells on path |
|---|---|---:|---:|---:|---:|---|
| pico_mul | `resetn` → `mul_counter[5]$_DFFE_PP_` | 5 | 0.09 | 0.32 | 0.85 | BUF×2, AOI21×2, NAND2×1 |
| pico_fast_mul | `rs1[32]$_SDFFCE_PN0P_` → `rd[60]$_DFF_P_` | 20 | 0.15 | 1.61 | 1.89 | FA×8, NOR3×2, AND2×1, BUF×1, HA×1, INV×1 |
| booth_d1 | `m[0]$_DFFE_PP_` → `h[34]$_SDFFCE_PP0P_` | 16 | 0.1 | 0.99 | 1.17 | HA×2, AND2×2, OR3×2, NAND2×1, NOR3×1, NAND3×1 |
| booth_d2 | `l[0]$_DFFE_PP_` → `h[34]$_SDFFCE_PP0P_` | 24 | 0.1 | 1.38 | 1.58 | OAI21×3, NOR3×3, HA×2, NOR2×2, AOI21×2, NAND3×2 |
| booth_d4 | `m[1]$_DFFE_PP_` → `h[32]$_SDFFCE_PP0P_` | 50 | 0.09 | 1.85 | 2.04 | BUF×7, HA×5, OAI21×5, AOI21×5, NOR2×4, NAND2×4 |
| pico_div | `pcpi_rs1[2]` → `dividend[31]$_DFFE_PP_` | 9 | 0.04 | 0.57 | 1.01 | OR4×3, AOI21×2, NOR4×1, NAND2×1, OAI211×1, MUX2×1 |
| restoring_b1 | `want_rem$_DFFE_PP_` → `pcpi_rd[30]` | 12 | 0.19 | 0.52 | 0.81 | INV×2, AOI21×2, OAI21×2, HA×1, NOR3×1, OAI221×1 |
| restoring_b2 | `r[9]$_SDFFCE_PP0P_` → `r[10]$_SDFFCE_PP0P_` | 22 | 0.11 | 1.24 | 1.45 | HA×2, NAND2×2, AND2×2, AOI21×2, OAI21×2, MUX2×2 |
| restoring_b4 | `r[18]$_SDFFCE_PP0P_` → `r[28]$_SDFFCE_PP0P_` | 49 | 0.09 | 2.06 | 2.26 | BUF×8, AOI221×5, HA×4, OAI21×4, AOI21×4, INV×3 |

## sky130hd (clock target 6.0 ns)

### Area by stage (standard-cell µm²) and timing after routing

| unit | synth | placed | CTS | routed | util % | setup WNS (ns) | setup TNS (ns) | hold WNS (ns) | Fmax placed → routed (MHz) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pico_mul | 12434.4 | 14033.5 | 14945.6 | 14948.1 | 48.9 | +3.401 | 0.000 | +0.369 | 333.4 → 384.7 |
| pico_fast_mul | 39535.4 | 45871.5 | 48094.9 | 49044.5 | 50.4 | -1.234 | -45.944 | +0.498 | 134.8 → 138.2 |
| booth_d1 | 8460.6 | 9882.0 | 10227.3 | 10227.3 | 49.9 | +1.080 | 0.000 | +0.526 | 204.2 → 203.2 |
| booth_d2 | 11432.2 | 14501.4 | 15087.0 | 15436.1 | 55.3 | -0.330 | -1.465 | +0.528 | 155.3 → 158.0 |
| booth_d4 | 17372.9 | 23900.4 | 25604.6 | 26366.5 | 62.2 | -3.892 | -86.028 | +0.545 | 98.4 → 101.1 |
| pico_div | 13211.4 | 14805.4 | 15444.8 | 15444.8 | 47.5 | +2.340 | 0.000 | +0.495 | 249.2 → 273.2 |
| restoring_b1 | 8715.9 | 10118.5 | 10391.2 | 10391.2 | 49.0 | +1.329 | 0.000 | +0.518 | 232.9 → 214.1 |
| restoring_b2 | 10279.9 | 12249.2 | 12565.8 | 12642.1 | 50.2 | +0.287 | 0.000 | +0.519 | 170.2 → 175.1 |
| restoring_b4 | 14286.2 | 19842.8 | 21707.1 | 22461.5 | 64.4 | -3.979 | -131.021 | +0.509 | 94.3 → 100.2 |

### Clock tree, routing and congestion

| unit | skew (ps) | clk bufs+invs | clk cell area (µm²) | repair bufs | wirelength (µm) | vias | GR usage % | busiest layer | overflow | DRC |
|---|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| pico_mul | 12.5 | 47+6 | 912.12 | 130 | 21288 | 6868 | 15.09 | met1 25.08% | 0 | 0 |
| pico_fast_mul | 21.4 | 18+14 | 566.79 | 636 | 111655 | 25446 | 25.38 | met2 39.79% | 0 | 0 |
| booth_d1 | 11.2 | 10+6 | 345.33 | 133 | 22717 | 7543 | 22.85 | met1 35.04% | 0 | 0 |
| booth_d2 | 20.0 | 9+7 | 314.05 | 379 | 38162 | 11554 | 27.81 | met2 43.81% | 0 | 0 |
| booth_d4 | 17.8 | 17+15 | 620.6 | 859 | 80062 | 21164 | 37.47 | met2 58.06% | 0 | 0 |
| pico_div | 16.6 | 17+15 | 639.36 | 129 | 32619 | 10544 | 21.17 | met2 33.62% | 0 | 1 |
| restoring_b1 | 7.0 | 12+4 | 272.76 | 130 | 21737 | 7496 | 21.16 | met2 34.61% | 0 | 0 |
| restoring_b2 | 8.9 | 9+7 | 316.55 | 196 | 27939 | 9083 | 22.51 | met1 34.39% | 0 | 0 |
| restoring_b4 | 15.9 | 10+6 | 289.03 | 722 | 54158 | 15589 | 30.26 | met2 47.2% | 0 | 0 |

### Routed metal area (wire length × drawn width, from the final DEF)

| unit | signal wire (µm) | signal metal (µm²) | signal metal / cell area | clock wire (µm) | clock metal (µm²) | signal metal by layer (µm²) |
|---|---:|---:|---:|---:|---:|---|
| pico_mul | 17752 | 2706.8 | 0.18 | 3537 | 643.7 | met1 1225, met2 1087, met3 366, met4 1, met5 28 |
| pico_fast_mul | 108358 | 16940.0 | 0.35 | 3297 | 655.6 | met1 6012, met2 7609, met3 2620, met4 699 |
| booth_d1 | 21166 | 3232.6 | 0.32 | 1550 | 276.1 | met1 1384, met2 1344, met3 372, met4 133 |
| booth_d2 | 36407 | 5577.4 | 0.36 | 1756 | 326.4 | met1 2273, met2 2404, met3 495, met4 406 |
| booth_d4 | 77911 | 12663.9 | 0.48 | 2151 | 440.6 | met1 4403, met2 4968, met3 1602, met4 1691 |
| pico_div | 30097 | 4526.1 | 0.29 | 2523 | 419.8 | met1 1927, met2 2013, met3 488, met4 98 |
| restoring_b1 | 20197 | 2991.7 | 0.29 | 1541 | 268.4 | met1 1257, met2 1427, met3 251, met4 57 |
| restoring_b2 | 26412 | 3999.0 | 0.32 | 1528 | 271.3 | met1 1749, met2 1685, met3 541, met4 24 |
| restoring_b4 | 52665 | 8179.7 | 0.36 | 1494 | 273.4 | met1 3317, met2 3350, met3 796, met4 716 |

### Power (simulation-annotated) and energy per operation

| unit | internal (mW) | switching (mW) | leakage (µW) | total (mW) | clock tree (mW) | nets annotated | cycles/op | energy/op (pJ) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| pico_mul | 3.170 | 0.844 | 0.00649 | 4.010 | 1.700 | 1161/1163 | 62.78 | 1510.44 |
| pico_fast_mul | 2.560 | 1.710 | 0.0217 | 4.270 | 1.120 | 5119/5121 | 5.0 | 128.15 |
| booth_d1 | 1.740 | 0.827 | 0.00394 | 2.570 | 0.709 | 1193/1195 | 21.0 | 323.85 |
| booth_d2 | 2.010 | 1.280 | 0.00644 | 3.290 | 0.654 | 1861/1863 | 13.0 | 256.66 |
| booth_d4 | 3.110 | 2.250 | 0.0119 | 5.360 | 1.110 | 3280/3282 | 9.0 | 289.5 |
| pico_div | 2.370 | 0.933 | 0.00629 | 3.310 | 1.240 | 1706/1708 | 39.0 | 774.58 |
| restoring_b1 | 1.380 | 0.548 | 0.00415 | 1.930 | 0.575 | 1226/1228 | 36.0 | 416.9 |
| restoring_b2 | 1.580 | 0.734 | 0.00518 | 2.310 | 0.648 | 1504/1506 | 20.0 | 277.23 |
| restoring_b4 | 2.150 | 1.260 | 0.0102 | 3.410 | 0.600 | 2619/2621 | 12.0 | 245.56 |

### Gate-level simulation of the routed netlist (tb_unit, zero delay)

| unit | flip-flops start at X | all start at 0 | all start at 1 | note |
|---|---|---|---|---|
| pico_mul | PASS (2024 checks) | PASS (2024 checks) | PASS (2024 checks) |  |
| pico_fast_mul | PASS (2024 checks) | PASS (2024 checks) | PASS (2024 checks) |  |
| booth_d1 | PASS (2024 checks) | PASS (2024 checks) | PASS (2024 checks) |  |
| booth_d2 | PASS (2024 checks) | PASS (2024 checks) | PASS (2024 checks) |  |
| booth_d4 | PASS (2024 checks) | PASS (2024 checks) | PASS (2024 checks) |  |
| pico_div | PASS (2024 checks) | PASS (2024 checks) | PASS (2024 checks) |  |
| restoring_b1 | PASS (2024 checks) | PASS (2024 checks) | PASS (2024 checks) |  |
| restoring_b2 | PASS (2024 checks) | PASS (2024 checks) | PASS (2024 checks) |  |
| restoring_b4 | PASS (2024 checks) | PASS (2024 checks) | PASS (2024 checks) |  |

### Critical path (after routing)

| unit | start → end | logic depth | clk→Q (ns) | logic (ns) | arrival (ns) | main cells on path |
|---|---|---:|---:|---:|---:|---|
| pico_mul | `rs1[0]$_DFFE_PP_` → `rdx[16]$_SDFFCE_PP0P_` | 8 | 0.35 | 1.96 | 2.86 | buf×2, fa×2, and2×1, a21o×1, a21oi×1, nor2×1 |
| pico_fast_mul | `rs1[14]$_DFFE_PP_` → `rd[61]$_DFF_P_` | 22 | 0.38 | 6.76 | 7.66 | fa×8, buf×3, nand3×2, o21ai×2, and2×1, ha×1 |
| booth_d1 | `m[13]$_DFFE_PP_` → `h[31]$_SDFFCE_PP0P_` | 15 | 0.51 | 4.29 | 5.15 | nand2×3, nor4×2, or4×1, and2×1, xor2×1, a211oi×1 |
| booth_d2 | `m[1]$_DFFE_PP_` → `h[34]$_SDFFCE_PP0P_` | 25 | 0.4 | 5.78 | 6.57 | a21o×4, ha×3, nand2×2, or4×2, or3×2, xor2×2 |
| booth_d4 | `m[1]$_DFFE_PP_` → `h[34]$_SDFFCE_PP0P_` | 47 | 0.43 | 9.21 | 10.12 | ha×5, o21ai×5, xnor2×3, buf×3, a31oi×3, a21oi×2 |
| pico_div | `dividend[0]$_DFFE_PP_` → `dividend[24]$_DFFE_PP_` | 10 | 0.43 | 3.06 | 3.94 | inv×1, ha×1, fa×1, nor2b×1, o2111ai×1, a21boi×1 |
| restoring_b1 | `want_rem$_DFFE_PP_` → `pcpi_rd[31]` | 10 | 0.33 | 2.76 | 3.47 | buf×1, mux2i×1, o211ai×1, nor3×1, o21ai×1, or3×1 |
| restoring_b2 | `r[0]$_SDFFCE_PP0P_` → `r[24]$_SDFFCE_PP0P_` | 23 | 0.47 | 4.96 | 5.83 | buf×3, ha×2, o31a×2, a211oi×2, nor2b×1, o2111ai×1 |
| restoring_b4 | `d[27]$_DFFE_PP_` → `r[22]$_SDFFCE_PP0P_` | 49 | 0.56 | 9.16 | 10.11 | buf×9, ha×4, nand2×4, a21oi×4, a21o×3, o31ai×3 |
