/* Mid-eval baseline harness: runs scalar CSR, dense-RVV GEMV and CSR-RVV SpMV,
 * checks correctness against the generated reference, prints one RESULT line each.
 * Build with -DDATA_HEADER='"data/xxx.h"'.
 *
 * Measurement rules (see docs/MEASUREMENT_NOTES.md):
 *  - every kernel is called once untimed (warm-up) and then timed. Under pk the first
 *    touch of each 4 KiB page traps into the kernel, and those handler instructions
 *    land in rdinstret. `cold_instret` is the first call, `instret` the warm one.
 *  - no counters inside the kernels. vec_iters/avg_vl are obtained by replaying the
 *    same vsetvl sequence outside the timed region. */
#include <stdio.h>
#include <math.h>
#include "kernels.h"
#include DATA_HEADER

#if defined(__riscv)
static inline unsigned long rd_cycle(void)  { unsigned long c; __asm__ volatile("rdcycle %0" : "=r"(c)); return c; }
static inline unsigned long rd_instret(void){ unsigned long c; __asm__ volatile("rdinstret %0" : "=r"(c)); return c; }
#else
static inline unsigned long rd_cycle(void)  { return 0; }
static inline unsigned long rd_instret(void){ return 0; }
#endif

#if defined(__riscv_vector)
#include <riscv_vector.h>
static size_t vl_for(size_t avl) { return __riscv_vsetvl_e32m1(avl); }
static size_t vl_max(void)       { return __riscv_vsetvlmax_e32m1(); }
#else
static size_t vl_for(size_t avl) { return avl; }
static size_t vl_max(void)       { return 0; }
#endif

static float y[N];
static unsigned long vec_iters, vl_sum;

/* Replay of the inner loops of gemv_dense_rvv / spmv_csr_rvv: one vsetvl per chunk. */
static void stats_chunks(size_t len) {
  if (!vl_max()) return; /* host fallback: no vector unit */
  while (len > 0) {
    size_t vl = vl_for(len);
    vec_iters++; vl_sum += vl;
    len -= vl;
  }
}
static void stats_none(void)  { vec_iters = vl_sum = 0; }
static void stats_dense(void) { stats_none(); for (int i = 0; i < N; i++) stats_chunks(N); }
static void stats_csr(void)   { stats_none(); for (int i = 0; i < N; i++) stats_chunks(rowptr[i + 1] - rowptr[i]); }

static float max_rel_err(void) {
  float m = 0.f;
  for (int i = 0; i < N; i++) {
    float d = fabsf(y[i] - yref[i]) / (fabsf(yref[i]) + 1e-3f);
    if (d > m) m = d;
  }
  return m;
}

#define RUN(name, call, stats, gathers)                                          \
  do {                                                                           \
    for (int i = 0; i < N; i++) y[i] = 0.f;                                      \
    unsigned long w0 = rd_instret();                                             \
    call; /* warm-up: pays the page faults */                                    \
    unsigned long w1 = rd_instret();                                             \
    for (int i = 0; i < N; i++) y[i] = 0.f;                                      \
    unsigned long c0 = rd_cycle(), i0 = rd_instret();                            \
    call;                                                                        \
    unsigned long c1 = rd_cycle(), i1 = rd_instret();                            \
    float err = max_rel_err();                                                   \
    stats();                                                                     \
    double avg_vl = vec_iters ? (double)vl_sum / vec_iters : 0.0;                \
    printf("RESULT kernel=%s pattern=%s n=%d nnz=%d sparsity=%.4f vlmax=%lu "     \
           "cycles=%lu instret=%lu cold_instret=%lu vec_iters=%lu avg_vl=%.2f "   \
           "gathers=%lu maxrelerr=%.2e %s\n",                                    \
           name, PATTERN, N, NNZ, SPARSITY_ACTUAL, (unsigned long)vl_max(),      \
           c1 - c0, i1 - i0, w1 - w0, vec_iters, avg_vl,                         \
           (gathers) ? vec_iters : 0UL, err, err < 1e-3f ? "PASS" : "FAIL");     \
  } while (0)

int main(void) {
  RUN("scalar_csr", spmv_scalar_ref(N, rowptr, colidx, vals, xvec, y), stats_none, 0);
  RUN("dense_rvv",  gemv_dense_rvv(N, A_dense, xvec, y), stats_dense, 0);
  RUN("csr_rvv",    spmv_csr_rvv(N, rowptr, colidx, vals, xvec, y), stats_csr, 1);
  return 0;
}
