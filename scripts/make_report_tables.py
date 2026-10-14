#!/usr/bin/env python3
"""Turn results/vlen*/table.csv into LaTeX tables for the report (report/tables/*.tex).

Usage: make_report_tables.py [--results results] [--outdir report/tables]
"""
import argparse, csv, glob, os, collections

def load(path):
    rows = list(csv.DictReader(open(path)))
    for r in rows:
        for k in ("n", "nnz", "vlmax", "instret", "cold_instret", "vec_iters"):
            r[k] = int(r[k])
        for k in ("sparsity", "avg_vl"):
            r[k] = float(r[k])
    return rows

def by_sparsity(rows, pattern):
    out = collections.OrderedDict()
    for r in sorted(rows, key=lambda r: r["sparsity"]):
        if r["pattern"] == pattern:
            out.setdefault(r["sparsity"], {})[r["kernel"]] = r
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results")
    ap.add_argument("--outdir", default="report/tables")
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    tables = {}
    for d in sorted(glob.glob(os.path.join(a.results, "vlen*"))):
        vlen = int(os.path.basename(d)[4:])
        tables[vlen] = load(os.path.join(d, "table.csv"))

    # One table per pattern at each VLEN: sparsity, nnz, scalar, dense, csr, csr avg_vl, speedups.
    for vlen, rows in tables.items():
        for pat in ("uniform", "banded", "block"):
            g = by_sparsity(rows, pat)
            if not g: continue
            with open(os.path.join(a.outdir, f"{pat}_vlen{vlen}.tex"), "w") as f:
                f.write("\\begin{tabular}{rrrrrrrr}\n\\toprule\n")
                f.write("sparsity & nnz & scalar CSR & dense RVV & CSR RVV & avg vl & dense/CSR & scalar/CSR \\\\\n\\midrule\n")
                for s, k in g.items():
                    sc, de, cs = k["scalar_csr"], k["dense_rvv"], k["csr_rvv"]
                    f.write(f"{s:.3f} & {cs['nnz']} & {sc['instret']} & {de['instret']} & {cs['instret']} & "
                            f"{cs['avg_vl']:.2f} & {de['instret']/cs['instret']:.2f} & {sc['instret']/cs['instret']:.2f} \\\\\n")
                f.write("\\bottomrule\n\\end{tabular}\n")

    # Cross-VLEN table for the uniform pattern: CSR RVV instructions at each VLEN.
    vlens = sorted(tables)
    with open(os.path.join(a.outdir, "uniform_vlen_sweep.tex"), "w") as f:
        f.write("\\begin{tabular}{r" + "r" * (2 * len(vlens)) + "}\n\\toprule\n")
        f.write("sparsity" + "".join(f" & dense V{v} & CSR V{v}" for v in vlens) + " \\\\\n\\midrule\n")
        gs = {v: by_sparsity(tables[v], "uniform") for v in vlens}
        for s in gs[vlens[0]]:
            f.write(f"{s:.3f}" + "".join(f" & {gs[v][s]['dense_rvv']['instret']} & {gs[v][s]['csr_rvv']['instret']}" for v in vlens) + " \\\\\n")
        f.write("\\bottomrule\n\\end{tabular}\n")

    # Cold vs warm table (measurement section), VLEN 512 uniform sparsity 0.
    v = max(tables)
    k = by_sparsity(tables[v], "uniform")
    s0 = min(k)
    with open(os.path.join(a.outdir, "cold_warm.tex"), "w") as f:
        f.write("\\begin{tabular}{lrrr}\n\\toprule\nkernel & first call & second call & ratio \\\\\n\\midrule\n")
        for name in ("scalar_csr", "dense_rvv", "csr_rvv"):
            r = k[s0][name]; label = name.replace("_", r"\_")
            f.write(f"{label} & {r['cold_instret']} & {r['instret']} & {r['cold_instret']/r['instret']:.2f} \\\\\n")
        f.write("\\bottomrule\n\\end{tabular}\n")
    print(f"wrote tables to {a.outdir} for VLEN {vlens}")

if __name__ == "__main__":
    main()
