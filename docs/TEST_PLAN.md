# Test / Experiment Plan (edit as you go)
| ID | Kernel | Matrix | Check |
|----|--------|--------|-------|
| T1 | all | identity-like, n=32, 0.97 sparsity | PASS vs yref |
| T2 | all | fully dense (sparsity 0.0) | PASS; csr_rvv slower than dense_rvv expected |
| T3 | all | rows with 0 nnz (high sparsity) | no hang, PASS |
| T4 | all | n not a multiple of VLEN elems (e.g. n=100) | tail handling correct |
| T5 | all | banded / block / uniform @ same sparsity | compare cycles + avg_vl |
| T6 | all | sparsity sweep 0,0.5,0.8,0.9,0.95,0.99 | crossover point |
| T7 | all | 3 different seeds | variance small |
| T8 | csr_rvv | 1-2 SuiteSparse matrices (convert .mtx -> header; extend gen_matrix.py) | PASS |
Mid-eval minimum from the spec: >= 2 sparsity levels, baseline execution time reported.
