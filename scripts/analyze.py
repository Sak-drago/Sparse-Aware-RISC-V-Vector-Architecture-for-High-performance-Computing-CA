#!/usr/bin/env python3
"""Parse RESULT lines -> CSV table, plots (metric vs sparsity), and predicted/observed crossover.

Usage: analyze.py results/vlen512/spike_results.txt --metric instret --outdir results/vlen512
 --metric instret|cycles|cold_instret
   Spike is not a timing model: its 'cycles' counter is the instruction count. Use --metric cycles only
   for logs from a cycle-accurate simulator (Ara/Verilator, gem5).
"""
import argparse, csv, re, os, collections

YLABEL = {"instret": "dynamic instructions (warm run)", "cold_instret": "dynamic instructions (first call, incl. page faults)"}

def parse(path):
    rows = []
    for line in open(path):
        if not line.startswith("RESULT"): continue
        d = dict(kv.split("=", 1) for kv in line.split()[1:] if "=" in kv)
        d["status"] = "PASS" if "PASS" in line else "FAIL"
        for k in ("n", "nnz", "vlmax", "cycles", "instret", "cold_instret", "vec_iters", "gathers"):
            d[k] = int(d.get(k, 0))
        for k in ("sparsity", "avg_vl", "maxrelerr"):
            d[k] = float(d[k])
        rows.append(d)
    return rows

def crossover(xs, a, b):
    """First sparsity where b (sparse) becomes cheaper than a (dense); linear interpolation."""
    for i in range(1, len(xs)):
        d0, d1 = b[i-1] - a[i-1], b[i] - a[i]
        if d0 >= 0 > d1:
            return xs[i-1] + (xs[i] - xs[i-1]) * d0 / (d0 - d1)
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("results"); ap.add_argument("--metric", default="instret")
    ap.add_argument("--outdir", default="results")
    a = ap.parse_args()
    rows = parse(a.results)
    if not rows: raise SystemExit("no RESULT lines found")
    os.makedirs(a.outdir, exist_ok=True)
    bad = [r for r in rows if r["status"] != "PASS"]
    if bad: print(f"WARNING: {len(bad)} FAILED correctness checks")

    cols = ["pattern","kernel","n","nnz","sparsity","vlmax","cycles","instret","cold_instret","vec_iters","avg_vl","gathers","maxrelerr","status"]
    with open(os.path.join(a.outdir, "table.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore"); w.writeheader()
        for r in sorted(rows, key=lambda r: (r["pattern"], r["kernel"], r["sparsity"])): w.writerow(r)

    by = collections.defaultdict(dict)   # pattern -> kernel -> [(sparsity, metric, avg_vl)]
    for r in rows: by[r["pattern"]].setdefault(r["kernel"], []).append((r["sparsity"], r[a.metric], r["avg_vl"]))
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    for pat, ks in by.items():
        for k in ks: ks[k].sort()
        fig, ax = plt.subplots(1, 2, figsize=(11, 4))
        for k, pts in ks.items():
            ax[0].plot([p[0] for p in pts], [p[1] for p in pts], marker="o", label=k)
            if k != "scalar_csr" and pts[0][2] > 0:
                ax[1].plot([p[0] for p in pts], [p[2] for p in pts], marker="s", label=k)
        if "dense_rvv" in ks and "csr_rvv" in ks:
            xs = [p[0] for p in ks["dense_rvv"]]
            c = crossover(xs, [p[1] for p in ks["dense_rvv"]], [p[1] for p in ks["csr_rvv"]])
            msg = f"{pat}: observed dense->CSR crossover at sparsity ~ {c:.3f}" if c else f"{pat}: no crossover in range"
            print(msg)
            if c: ax[0].axvline(c, ls="--", c="gray"); ax[0].set_title(f"{pat} (crossover ~{c:.2f})")
        else: ax[0].set_title(pat)
        ax[0].set_xlabel("sparsity (fraction zeros)"); ax[0].set_ylabel(YLABEL.get(a.metric, a.metric)); ax[0].set_yscale("log"); ax[0].legend(); ax[0].grid(alpha=.3)
        ax[1].set_xlabel("sparsity"); ax[1].set_ylabel("avg vl per vector op (utilisation proxy)"); ax[1].legend(); ax[1].grid(alpha=.3)
        fig.tight_layout(); fig.savefig(os.path.join(a.outdir, f"{a.metric}_vs_sparsity_{pat}.png"), dpi=150); plt.close(fig)
    print(f"wrote {a.outdir}/table.csv and plots")

if __name__ == "__main__":
    main()
