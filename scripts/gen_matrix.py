#!/usr/bin/env python3
"""Generate a synthetic sparse matrix and emit a C header (dense + CSR + x + reference y).

Usage: gen_matrix.py --n 128 --sparsity 0.9 --pattern uniform --seed 1 --out data/m.h
Patterns: uniform | banded | block
Sparsity = fraction of ZERO entries (0.9 -> 10% nonzero).
"""
import argparse, random

def build(n, sparsity, pattern, rng):
    density = 1.0 - sparsity
    A = [[0.0] * n for _ in range(n)]
    if pattern == "uniform":
        for i in range(n):
            for j in range(n):
                if rng.random() < density:
                    A[i][j] = rng.uniform(-1, 1)
    elif pattern == "banded":
        bw = max(0, int(round(density * n / 2)))
        for i in range(n):
            for j in range(max(0, i - bw), min(n, i + bw + 1)):
                A[i][j] = rng.uniform(-1, 1)
    elif pattern == "block":
        b = 8
        nb = n // b
        for bi in range(nb):
            for bj in range(nb):
                if rng.random() < density:
                    for i in range(b):
                        for j in range(b):
                            A[bi * b + i][bj * b + j] = rng.uniform(-1, 1)
    else:
        raise SystemExit("unknown pattern")
    if not any(any(r) for r in A):
        A[0][0] = 1.0  # avoid empty matrix
    return A

def emit(f, ctype, name, vals, fmt):
    f.write(f"static const {ctype} {name}[{max(1,len(vals))}] = {{\n")
    if not vals: f.write("0")
    for k in range(0, len(vals), 8):
        f.write("  " + ", ".join(fmt(v) for v in vals[k:k+8]) + ",\n")
    f.write("};\n")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=128)
    ap.add_argument("--sparsity", type=float, default=0.9)
    ap.add_argument("--pattern", default="uniform")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    rng = random.Random(a.seed)
    n = a.n
    A = build(n, a.sparsity, a.pattern, rng)
    x = [rng.uniform(-1, 1) for _ in range(n)]
    rowptr, col, val = [0], [], []
    for i in range(n):
        for j in range(n):
            if A[i][j] != 0.0:
                col.append(j); val.append(A[i][j])
        rowptr.append(len(col))
    y = [sum(A[i][j] * x[j] for j in range(n)) for i in range(n)]
    nnz = len(val)
    fl = lambda v: f"{v:.9e}f"
    with open(a.out, "w") as f:
        f.write(f"/* auto-generated: pattern={a.pattern} target_sparsity={a.sparsity} seed={a.seed} */\n")
        f.write(f"#define N {n}\n#define NNZ {nnz}\n")
        f.write(f'#define PATTERN "{a.pattern}"\n')
        f.write(f"#define SPARSITY_ACTUAL {1.0 - nnz / (n * n):.6f}\n")
        emit(f, "float", "A_dense", [v for r in A for v in r], fl)
        emit(f, "int", "rowptr", rowptr, str)
        emit(f, "unsigned int", "colidx", col, lambda v: f"{v}u")
        emit(f, "float", "vals", val, fl)
        emit(f, "float", "xvec", x, fl)
        emit(f, "float", "yref", y, fl)
    print(f"{a.out}: n={n} nnz={nnz} actual_sparsity={1 - nnz/(n*n):.4f} pattern={a.pattern}")

if __name__ == "__main__":
    main()
