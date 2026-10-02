# Getting cycle-accurate numbers on Ara (Verilator)
1. Clone pulp-platform/ara, follow its README to build the toolchain and `make verilate` (heavy; start early).
2. Put the generated header and `src/*.c` into an Ara app folder (`apps/spmv/`), following how other apps (e.g. `apps/fdotproduct`) are laid out.
3. Replace `rd_cycle()` in main.c with Ara's runtime cycle counter helpers (`start_timer()/stop_timer()/get_timer()` in Ara's runtime), and `printf` with Ara's UART printf.
4. Print the same `RESULT kernel=... cycles=...` format, redirect simulator output to `results/ara_results.txt`, then:
   `python3 scripts/analyze.py results/ara_results.txt --metric cycles --outdir results/ara`
5. Ara has no data cache by default (AXI to memory). Ask the TA how "cache miss rate" should be measured.
Verify these steps against the current Ara repo; layout and helper names change between versions.
