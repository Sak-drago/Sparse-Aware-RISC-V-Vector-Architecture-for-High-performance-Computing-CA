#ifndef KERNELS_H
#define KERNELS_H
#include <stdint.h>
#include <stddef.h>

void spmv_scalar_ref(int n, const int *rowptr, const unsigned *col, const float *val,
                     const float *x, float *y);
void gemv_dense_rvv(int n, const float *A, const float *x, float *y);
void spmv_csr_rvv(int n, const int *rowptr, const unsigned *col, const float *val,
                  const float *x, float *y);
#endif
