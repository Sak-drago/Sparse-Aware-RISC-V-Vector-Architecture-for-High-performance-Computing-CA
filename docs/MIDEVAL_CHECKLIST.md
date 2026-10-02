# Mid-eval checklist (maps to the spec)
- [ ] 1 Study RVV + sparse architectures summarized (report sec 2)
- [ ] 2 Baseline simulation environment set up and validated (Spike; Ara if possible) - screenshot hello-world
- [ ] 3 Baseline RVV with SpMV running (csr_rvv PASS)
- [ ] 4 >= 2 sparsity levels run (we run 6 x 3 patterns)
- [ ] 5 Execution time/performance reported (table.csv + plots)
- [ ] Demo ready: `make spike N=64 SPARS="0.5 0.9" PATTERNS=uniform OUT=/tmp/demo` completes live (OUT keeps results/ intact)
- [ ] Each member can explain every kernel line (individual viva)
