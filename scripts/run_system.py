#!/usr/bin/env python3
"""Run riscv-tests and the M-extension benchmark on every core configuration.

For each configuration the full PicoRV32 RTL (with the selected multiplier and
divider) is simulated in Vivado xsim twice: once with the 45 riscv-tests
(rv32ui + rv32um) and once with the benchmark firmware. Benchmark checksums
are verified against an independent Python model.

Writes results/system.json and results/system.md.
"""
import json
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SETTINGS = Path(os.environ.get("VIVADO_SETTINGS", Path.home() / "AMD/2025.2/Vivado/settings64.sh"))

# name: (generics, description)
CONFIGS = {
    "stock_seq":  ({"MUL": 1, "DIV": 1},                         "PicoRV32 ENABLE_MUL + ENABLE_DIV"),
    "stock_fast": ({"MUL": 2, "DIV": 1},                         "PicoRV32 ENABLE_FAST_MUL + ENABLE_DIV"),
    "booth1":     ({"MUL": 3, "MUL_P": 1, "DIV": 2, "DIV_P": 1}, "Booth r4 1 digit/cyc + restoring 1 bit/cyc"),
    "booth2":     ({"MUL": 3, "MUL_P": 2, "DIV": 2, "DIV_P": 2}, "Booth r4 2 digits/cyc + restoring 2 bits/cyc"),
    "booth4":     ({"MUL": 3, "MUL_P": 4, "DIV": 2, "DIV_P": 4}, "Booth r4 4 digits/cyc + restoring 4 bits/cyc"),
}
RTL = ["third_party/picorv32/picorv32.v", "rtl/pcpi_mul_booth.v",
       "rtl/pcpi_div_restoring.v", "rtl/core_top.v", "sim/tb_soc.v"]
N_TESTS = 45


# ------------------------------------------------------------ Python model
M32 = 0xFFFFFFFF


def s32(x):
    x &= M32
    return x - (1 << 32) if x & 0x80000000 else x


def tdiv(a, b):  # C semantics: truncate toward zero
    q = abs(a) // abs(b)
    return q if (a < 0) == (b < 0) else -q


def model():
    st = 12345

    def lcg():
        nonlocal st
        st = (st * 1103515245 + 12345) & M32
        return st

    ma = [[0] * 16 for _ in range(16)]
    mb = [[0] * 16 for _ in range(16)]
    for i in range(16):
        for j in range(16):
            ma[i][j] = s32(lcg()); mb[i][j] = s32(lcg())
    fx, fy = [], []
    for _ in range(1024):
        fx.append(s32(lcg())); fy.append(s32(lcg()))
    rv, rb = [], []
    for _ in range(256):
        rv.append(lcg()); rb.append(2 + (lcg() >> 16) % 35)
    da, db = [], []
    for _ in range(1024):
        da.append(s32(lcg())); db.append((s32(lcg()) >> 20) | 1)

    out = {}
    chk = 0
    for i in range(16):
        for j in range(16):
            s = s32(sum(ma[i][k] * mb[k][j] for k in range(16)))
            chk = (chk * 31 + s) & M32
    out["matmul32"] = chk
    acc = 0
    for x, y in zip(fx, fy):
        acc = (acc + s32((x * y) >> 16)) & M32
    out["fixmul"] = acc
    chk = 0
    for x, b in zip(rv, rb):
        while True:
            chk = (chk * 31 + x % b) & M32
            x //= b
            if not x:
                break
    out["radix"] = chk
    acc = 0
    for a, b in zip(da, db):
        q = tdiv(a, b)
        r = a - q * b
        acc = (acc + (q & M32) * 3 + (r & M32)) & M32
    out["sdiv"] = acc
    return out


# ------------------------------------------------------------ simulation
def sim(name):
    gens, _ = CONFIGS[name]
    work = ROOT / "build/sys" / name
    work.mkdir(parents=True, exist_ok=True)
    g = " ".join(f'-generic_top "{k}={v}"' for k, v in gens.items())
    files = " ".join(str(ROOT / f) for f in RTL)
    cmd = (f"source {SETTINGS} >/dev/null 2>&1; unset LIBRARY_PATH; "
           f"xvlog {files} > xvlog.log 2>&1 && "
           f"xelab -debug off --timescale 1ns/1ps {g} tb_soc -s soc > xelab.log 2>&1 && "
           f"xsim soc -R -testplusarg FIRMWARE={ROOT}/sw/build/riscv_tests.hex > tests.log 2>&1; "
           f"xsim soc -R -testplusarg FIRMWARE={ROOT}/sw/build/bench.hex > bench.log 2>&1")
    subprocess.run(["bash", "-c", cmd], cwd=work)
    rd = lambda f: (work / f).read_text() if (work / f).exists() else ""
    return name, rd("tests.log"), rd("bench.log")


def main():
    subprocess.run(["make", "-C", str(ROOT / "sw")], check=True, stdout=subprocess.DEVNULL)
    ref = model()
    with ThreadPoolExecutor(max_workers=len(CONFIGS)) as ex:
        runs = list(ex.map(sim, CONFIGS))

    results, ok = {}, True
    for name, tlog, blog in runs:
        passed = re.findall(r"(\w+)\.\.OK", tlog)
        tests_ok = len(passed) == N_TESTS and "EXIT code=0" in tlog
        kern = {}
        for k, c, v in re.findall(r"RESULT (\S+) cycles=(\d+) value=(\d+)", blog):
            kern[k] = {"cycles": int(c), "value": int(v),
                       "check": "PASS" if int(v) == ref[k] else "FAIL"}
        bench_ok = len(kern) == len(ref) and all(x["check"] == "PASS" for x in kern.values())
        ok &= tests_ok and bench_ok
        if not tests_ok:
            print(f"[{name}] riscv-tests: {len(passed)}/{N_TESTS} passed\n{tlog[-600:]}")
        results[name] = {"generics": CONFIGS[name][0], "description": CONFIGS[name][1],
                         "riscv_tests_passed": len(passed), "riscv_tests_total": N_TESTS,
                         "riscv_tests": passed, "kernels": kern}

    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    (out / "system.json").write_text(json.dumps(results, indent=2))
    names = list(CONFIGS)
    lines = ["| | " + " | ".join(names) + " |", "|---|" + "---:|" * len(names),
             "| riscv-tests | " + " | ".join(f"{results[n]['riscv_tests_passed']}/{N_TESTS}" for n in names) + " |"]
    for k in ref:
        lines.append(f"| {k} (cycles) | " + " | ".join(
            str(results[n]["kernels"].get(k, {}).get("cycles", "-")) for n in names) + " |")
    (out / "system.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    print("\nALL CHECKS PASS" if ok else "\nSOME CHECKS FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
