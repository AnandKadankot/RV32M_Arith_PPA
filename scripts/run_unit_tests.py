#!/usr/bin/env python3
"""Run tb_unit for all 9 multiplier/divider units plus two mutation tests.

Mutation tests inject a known bug into a copy of a unit and expect the
testbench to FAIL, proving the checks are able to detect real errors.

Writes results/unit_tests.json and results/unit_tests.md.
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

RUNS = {  # name: (UNIT, P)
    "pico_mul": (0, 1), "pico_fast_mul": (1, 1),
    "booth_d1": (2, 1), "booth_d2": (2, 2), "booth_d4": (2, 4),
    "pico_div": (3, 1),
    "restoring_b1": (4, 1), "restoring_b2": (4, 2), "restoring_b4": (4, 4),
}
MUTANTS = {  # name: (description, file, original text, mutated text, UNIT, P)
    "mut_booth_plus2m": ("Booth digit +2 uses +M instead of +2M", "rtl/pcpi_mul_booth.v",
                         "3'b011:         pp =  m <<< 1;", "3'b011:         pp =  m;", 2, 1),
    "mut_booth_minus2m": ("Booth digit -2 uses -M instead of -2M", "rtl/pcpi_mul_booth.v",
                          "3'b100:         pp = -(m <<< 1);", "3'b100:         pp = -m;", 2, 1),
    "mut_booth_wrong_qm1": ("Booth carries the wrong bit into the next digit", "rtl/pcpi_mul_booth.v",
                            "q_n = l_n[1];", "q_n = l_n[0];", 2, 2),
    "mut_mulhsu_rs1_unsigned": ("MULHSU treats rs1 as unsigned", "rtl/pcpi_mul_booth.v",
                                "wire rs1_signed = f3 == 2'b01 || f3 == 2'b10;", "wire rs1_signed = f3 == 2'b01;", 2, 1),
    "mut_mulhsu_rs2_signed": ("MULHSU treats rs2 as signed", "rtl/pcpi_mul_booth.v",
                              "wire rs2_signed = f3 == 2'b01;", "wire rs2_signed = f3 == 2'b01 || f3 == 2'b10;", 2, 1),
    "mut_mul_high_select": ("MULHSU returns the low word", "rtl/pcpi_mul_booth.v",
                            "want_high <= f3 != 2'b00;", "want_high <= f3[0];", 2, 4),
    "mut_mul_no_wait": ("multiplier never raises pcpi_wait (core would trap after 16 cycles)", "rtl/pcpi_mul_booth.v",
                        "assign pcpi_wait = insn_mul;", "assign pcpi_wait = 1'b0;", 2, 1),
    "mut_div_by_zero_sign": ("signed x/0 negates the all-ones quotient", "rtl/pcpi_div_restoring.v",
                             "neg_q    <= (a_neg ^ b_neg) && pcpi_rs2 != 32'd0;", "neg_q    <= (a_neg ^ b_neg);", 4, 1),
    "mut_rem_sign": ("remainder takes the quotient's sign instead of the dividend's", "rtl/pcpi_div_restoring.v",
                     "neg_r    <= a_neg;", "neg_r    <= a_neg ^ b_neg;", 4, 2),
    "mut_div_no_restore": ("trial subtraction is kept even when it borrows", "rtl/pcpi_div_restoring.v",
                           "r_n  = diff[33] ? r_sh[31:0] : diff[31:0];", "r_n  = diff[31:0];", 4, 4),
    "mut_div_short_count": ("divider stops one iteration early", "rtl/pcpi_div_restoring.v",
                            "localparam CYCLES = 32 / BITS;", "localparam CYCLES = 32 / BITS - 1;", 4, 2),
    "mut_div_no_wait": ("divider never raises pcpi_wait (core would trap after 16 cycles)", "rtl/pcpi_div_restoring.v",
                        "assign pcpi_wait  = insn_div;", "assign pcpi_wait  = 1'b0;", 4, 1),
}


def sim(name, unit, p, files):
    work = ROOT / "build/unit" / name
    work.mkdir(parents=True, exist_ok=True)
    cmd = (f"source {SETTINGS} >/dev/null 2>&1; unset LIBRARY_PATH; "
           f"xvlog -sv {' '.join(map(str, files))} > xvlog.log 2>&1 && "
           f"xelab -debug off --timescale 1ns/1ps -generic_top UNIT={unit} -generic_top P={p} "
           f"tb_unit -s t > xelab.log 2>&1 && xsim t -R > sim.log 2>&1")
    subprocess.run(["bash", "-c", cmd], cwd=work)
    log = (work / "sim.log").read_text() if (work / "sim.log").exists() else ""
    m = re.search(r"UNIT TEST (PASS|FAIL).*?(\d+) checks", log)
    errs = re.search(r"(\d+) errors", log)
    lat = {int(f): (int(a), int(b)) for f, a, b in re.findall(r"LATENCY f3=(\d) min=(\d+) max=(\d+)", log)}
    return {"result": m.group(1) if m else "ERROR", "checks": int(m.group(2)) if m else 0,
            "errors": int(errs.group(1)) if errs else 0, "latency": lat}


def job(item):
    name, spec = item
    base = [ROOT / "third_party/picorv32/picorv32.v", ROOT / "rtl/pcpi_mul_booth.v",
            ROOT / "rtl/pcpi_div_restoring.v", ROOT / "sim/tb_unit.v"]
    if name in MUTANTS:
        _, f, orig, mut, unit, p = spec
        src = (ROOT / f).read_text()
        assert src.count(orig) == 1, f"mutation anchor not unique in {f}"
        mdir = ROOT / "build/unit" / name
        mdir.mkdir(parents=True, exist_ok=True)
        (mdir / Path(f).name).write_text(src.replace(orig, mut))
        files = [mdir / Path(f).name if b.name == Path(f).name else b for b in base]
        return name, sim(name, unit, p, files)
    unit, p = spec
    return name, sim(name, unit, p, base)


def main():
    items = list(RUNS.items()) + list(MUTANTS.items())
    with ThreadPoolExecutor(max_workers=6) as ex:
        res = dict(ex.map(job, items))
    ok = all(res[n]["result"] == "PASS" for n in RUNS) and all(res[n]["result"] == "FAIL" for n in MUTANTS)
    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    (out / "unit_tests.json").write_text(json.dumps(res, indent=2))
    lines = ["| unit | result | checks | latency (cycles) by funct3 |", "|---|---|---:|---|"]
    for n in RUNS:
        r = res[n]
        lat = ", ".join(f"{f}:{a}" if a == b else f"{f}:{a}-{b}" for f, (a, b) in sorted(r["latency"].items()))
        lines.append(f"| {n} | {r['result']} | {r['checks']} | {lat} |")
    killed = sum(res[n]["result"] == "FAIL" for n in MUTANTS)
    lines += ["", "| mutation test | injected bug | unit (P) | result | errors detected |", "|---|---|---|---|---:|"]
    for n, (desc, f, _, _, unit, p) in MUTANTS.items():
        lines.append(f"| {n} | {desc} | {'booth' if unit == 2 else 'restoring'} ({p}) | {res[n]['result']} | {res[n]['errors']} |")
    lines += ["", f"**Mutation detection rate: {killed}/{len(MUTANTS)} = {100 * killed / len(MUTANTS):.0f}%**"]
    (out / "unit_tests.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    print("\nALL UNIT TESTS AS EXPECTED" if ok else "\nUNEXPECTED UNIT TEST RESULT")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
