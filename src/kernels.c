#include "kernels.h"

/* Scalar golden reference (also a scalar baseline for comparison). */
void spmv_scalar_ref(int n, const int *rowptr, const unsigned *col, const float *val,
                     const float *x, float *y) {
  for (int i = 0; i < n; i++) {
    float s = 0.f;
    for (int k = rowptr[i]; k < rowptr[i + 1]; k++) s += val[k] * x[col[k]];
    y[i] = s;
  }
}

#if defined(__riscv_vector)
#include <riscv_vector.h>

/* Baseline 1: dense GEMV. Zeros are multiplied anyway. */
void gemv_dense_rvv(int n, const float *A, const float *x, float *y) {
  size_t vlmax = __riscv_vsetvlmax_e32m1();
  for (int i = 0; i < n; i++) {
    const float *row = A + (size_t)i * n;
    vfloat32m1_t acc = __riscv_vfmv_v_f_f32m1(0.0f, vlmax);
    int j = 0;
    while (j < n) {
      size_t vl = __riscv_vsetvl_e32m1(n - j);
      vfloat32m1_t a = __riscv_vle32_v_f32m1(row + j, vl);
      vfloat32m1_t xv = __riscv_vle32_v_f32m1(x + j, vl);
      acc = __riscv_vfmacc_vv_f32m1_tu(acc, a, xv, vl);
      j += vl;
    }
    vfloat32m1_t z = __riscv_vfmv_s_f_f32m1(0.0f, 1);
    z = __riscv_vfredusum_vs_f32m1_f32m1(acc, z, vlmax);
    y[i] = __riscv_vfmv_f_s_f32m1_f32(z);
  }
}

/* Baseline 2: CSR SpMV, indexed gather on x (vluxei32), one reduction per row. */
void spmv_csr_rvv(int n, const int *rowptr, const unsigned *col, const float *val,
                  const float *x, float *y) {
  size_t vlmax = __riscv_vsetvlmax_e32m1();
  for (int i = 0; i < n; i++) {
    int k = rowptr[i], end = rowptr[i + 1];
    vfloat32m1_t acc = __riscv_vfmv_v_f_f32m1(0.0f, vlmax);
    while (k < end) {
      size_t vl = __riscv_vsetvl_e32m1(end - k);
      vuint32m1_t idx = __riscv_vle32_v_u32m1(col + k, vl);
      idx = __riscv_vsll_vx_u32m1(idx, 2, vl); /* element -> byte offset */
      vfloat32m1_t xv = __riscv_vluxei32_v_f32m1(x, idx, vl);
      vfloat32m1_t vv = __riscv_vle32_v_f32m1(val + k, vl);
      acc = __riscv_vfmacc_vv_f32m1_tu(acc, vv, xv, vl);
      k += vl;
    }
    vfloat32m1_t z = __riscv_vfmv_s_f_f32m1(0.0f, 1);
    z = __riscv_vfredusum_vs_f32m1_f32m1(acc, z, vlmax);
    y[i] = __riscv_vfmv_f_s_f32m1_f32(z);
  }
}

#else /* host fallback: scalar versions, ONLY to test harness/data on x86 */
void gemv_dense_rvv(int n, const float *A, const float *x, float *y) {
  for (int i = 0; i < n; i++) {
    float s = 0.f;
    for (int j = 0; j < n; j++) s += A[(size_t)i * n + j] * x[j];
    y[i] = s;
  }
}
void spmv_csr_rvv(int n, const int *rowptr, const unsigned *col, const float *val,
                  const float *x, float *y) {
  spmv_scalar_ref(n, rowptr, col, val, x, y);
}
#endif
