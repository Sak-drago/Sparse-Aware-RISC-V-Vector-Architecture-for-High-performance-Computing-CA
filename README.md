# CA Project 1 - Sparse-Aware RISC-V Vector Architecture (Mid-Eval Artifact)

Baseline RVV study: dense GEMV vs CSR SpMV vs scalar CSR, across sparsity levels, patterns and vector lengths.

## Layout
- `src/kernels.c`  scalar reference, dense RVV GEMV, CSR RVV SpMV (gather `vluxei32`)
- `src/main.c`     harness: warm-up + timed call per kernel, checks vs reference, prints `RESULT ...` lines
- `scripts/gen_matrix.py`  synthetic matrices (uniform / banded / block) -> C header
- `scripts/analyze.py`     table.csv, plots, observed dense->CSR crossover
- `scripts/setup_tools.sh` builds dtc + Spike + pk into `/opt/riscv` (pinned commits)
- `docs/MEASUREMENT_NOTES.md`  what the numbers mean and what they do not mean
- `docs/`          report skeleton, PPT skeleton, test plan, reading list, schedule (templates, YOU fill in)
- `results/vlen{128,256,512}/` Spike logs, tables, plots
- `results_friend_original/`   first mid-eval run, kept for comparison (see MEASUREMENT_NOTES.md, do not report)
- `examples/sample_format_only.txt`  FAKE numbers, only to show the log format. Never report them.

## Requirements
- `riscv64-unknown-elf-gcc` with RVV intrinsics (GCC >= 14; validated with 16.1.0) in `/opt/riscv/bin`
- Spike + pk: `scripts/setup_tools.sh`
- python3 with matplotlib

The Makefile prepends `$(RISCV)/bin` (default `/opt/riscv/bin`) to `PATH`.

## Quick start
```
make host-test        # any PC with gcc+python3: validates data/harness (scalar fallback, counters = 0)
make spike            # 10 sparsity levels x 3 patterns at VLEN=512 -> results/vlen512/
make sweep            # the same for VLEN = 128, 256, 512
make spike N=64 SPARS="0.5 0.9" PATTERNS=uniform VLEN=256 OUT=/tmp/demo
```
Outputs per run: `spike_results.txt`, `table.csv`, `instret_vs_sparsity_<pattern>.png`.

Changing `N` or `SEED` regenerates the data headers and rebuilds the binaries. The binaries do not depend on
`VLEN`: the same ELF runs at every vector length, only Spike's `--isa=..._zvl<VLEN>b` changes.

## Notes / caveats (state these in your report)
- Spike is a functional simulator. `rdcycle` equals the instruction count, so the metric here is dynamic
  instructions, not time. A gather of 16 elements counts the same as an add. See `docs/MEASUREMENT_NOTES.md`.
- `instret` is the second (warm) call of each kernel. `cold_instret` is the first call and includes pk's
  page-fault handling.
- `vec_iters` and `avg_vl` are obtained by replaying the kernels' `vsetvl` sequence outside the timed region.
- For cycle numbers the same kernels have to run on a timing model (Ara under Verilator, see `docs/ARA_PORTING.md`).
