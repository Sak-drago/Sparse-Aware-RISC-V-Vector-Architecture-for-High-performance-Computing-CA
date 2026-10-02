# Mid-Eval Report Skeleton (write the prose yourselves - AI-written reports are prohibited)
1. Problem & motivation (what is lost when vector hardware meets sparse data) - your words, ~half page
2. Background: RVV (vsetvl, LMUL/SEW, masks, strided/indexed loads, reductions); sparse formats (CSR, COO, ELL, SELL-C-sigma); prior sparse architectures - cite sources
3. Experimental setup: toolchain versions, simulator(s), ISA string, matrix sizes, patterns, seeds, how metrics are measured; limitations of Spike timing
4. Baseline implementations: dense GEMV, CSR SpMV (explain each RVV instruction used, why gather, why reduction per row); correctness check method
5. Results: table (cycles/instret vs sparsity, per pattern), plot with crossover marked, avg_vl & gather counts
6. Analysis: why CSR loses at low sparsity, why avg_vl drops with sparsity, effect of structure (banded/block vs uniform), prediction of crossover from a simple model (fill in: dense ~ N*N/VLEN_elems, sparse ~ nnz*c)
7. Limitations / failure cases (small N, Spike != cycles, no cache model)
8. Plan for end-eval (chosen mechanism, risks, schedule, roles)
9. References
