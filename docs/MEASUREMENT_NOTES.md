# Measurement notes

## What is measured
Each kernel is called twice. The second call is bracketed by `rdinstret` and reported as `instret`.
The first call is reported as `cold_instret`. On Spike `rdcycle` advances by one per instruction, so
`cycles` carries no extra information.

Setup: Spike 1.1.1-dev (609dbe0b), pk (9c61d298), GCC 16.1.0, `-O2 -march=rv64gcv_zicntr -mabi=lp64d`,
SEW=32, LMUL=1, N=128, seed 1.

## Why the first mid-eval numbers were replaced
`results_friend_original/` holds the first run. Two effects inflated it.

1. Page faults. pk maps the ELF lazily, so the first touch of each 4 KiB page traps and the handler's
   instructions are counted by `rdinstret`. `A_dense` is 64 KiB = 16 pages and only the dense kernel touches
   it. `scalar_csr` ran first and paid for the CSR arrays, so `csr_rvv` ran warm. A Spike trace
   (`spike -l`) of the old binary shows 50 load page faults, about 5100 handler instructions each. In the
   current harness the same cost is visible as `cold_instret - instret` for `dense_rvv`: 95383 - 13458 = 81925,
   i.e. 16 pages. The old dense numbers alternate between 104606 and 99614 because array alignment decides
   whether 16 or 15 new pages are touched.
2. Counters inside the kernels. `-DSTATS` put 9 (dense) or 12 (CSR) load/add/store instructions inside a
   12-instruction inner loop.

N=128, VLEN=512, uniform, sparsity 0:

| kernel     | first run | warm, no counters |
|------------|-----------|-------------------|
| scalar_csr | 324037    | 149645            |
| dense_rvv  | 104605    | 13458             |
| csr_rvv    | 26006     | 13713             |

The first run said CSR-RVV is 4x cheaper than dense on a fully dense matrix. It is not: the two are equal.

The old `table.csv` also has an N=32 row at sparsity 0.5 (stale header from a smoke test). The Makefile now
regenerates headers when `N` or `SEED` changes.

## Instruction-count model
Both vector inner loops compile to 12 instructions per chunk (`objdump -d bin/uniform_s0.0`):

- dense: `12 * N * ceil(N / VLMAX) + 9 * N + 18`
- CSR:   `12 * sum_rows ceil(nnz_row / VLMAX) + 11 * N + 17`
- scalar CSR: `9 * nnz + 17 * N + 13` (less when rows are empty)

The two vector formulas match all 180 vector rows of `results/vlen*/table.csv` to within one instruction.

## What instruction count hides
- `vluxei32` (gather) is one instruction here. On hardware it is VL separate memory accesses (check how Ara
  handles indexed loads before quoting this). The crossover sparsities printed by `analyze.py` (0.5% to 8%) are
  therefore a lower bound, not a prediction.
- No cache, no memory latency. `x[col[k]]` is a random access; `A[i][j]` is a stream.
- `vfredusum` over VLMAX elements is one instruction per row, independent of row length.

## What it does show
- Work per non-zero for CSR-RVV at VLEN=512 goes from 0.84 instructions (sparsity 0) to 13.96 (sparsity 0.99).
  Rows hold fewer non-zeros than VLMAX, so each row still pays one chunk plus the fixed row overhead.
- `avg_vl` falls from 16 to 1.95 over the same range: the vector unit is 12% used.
- Longer vectors stop helping: at sparsity 0.99, VLEN 128 -> 512 changes CSR-RVV from 2578 to 2554 instructions.
- Pattern matters: at about 0.977 sparsity and VLEN=512, block (8x8) needs 1905 instructions with avg_vl 9.6,
  banded needs 2962 with avg_vl 2.98.
- At sparsity 0.99 scalar CSR (3530) is within 1.4x of CSR-RVV (2554).

## Validation done
- 270 runs in `results/` (3 VLEN x 3 patterns x 10 sparsities x 3 kernels): all PASS against the Python reference.
- N=100 and N=37 (not multiples of VLMAX, block pattern leaves empty rows), seeds 2 and 3, at VLEN 128 and 512:
  720 further runs, all PASS. Seed-to-seed spread of CSR-RVV instructions (uniform, VLEN=512) is below 3%.
