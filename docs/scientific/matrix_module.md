# Scientific Matrix Module

## Overview

The matrix module provides validated Float64 matrix operations for scientific computing.

## Data Representation

- NumPy Float64 arrays.
- Two-dimensional matrices.
- Input values are copied.
- NaN, infinity, complex and boolean components are rejected.
- Broadcasting is not allowed for addition and subtraction.

## Public API

Import:

    from quantum_space_agi.scientific import matrix

Functions:

- create_matrix(values): Create a validated Float64 matrix.
- add(left, right): Add matrices with identical shapes.
- subtract(left, right): Subtract matrices with identical shapes.
- multiply(left, right): Standard matrix multiplication.
- transpose(values): Return a transposed copy.
- determinant(values): Calculate a square matrix determinant.
- inverse(values): Calculate the inverse of a well-conditioned square matrix.
- solve(coefficients, right_hand_side): Solve Ax = b.

## Numerical Conditioning

Inverse and solve use singular values to evaluate numerical rank and conditioning.

The default maximum condition number is 1e12. This is a provisional module default, not a universal accuracy guarantee.

Numerically rank-deficient matrices raise SINGULAR_MATRIX.
Matrices exceeding the condition limit raise UNCERTAIN_RESULT.

## Error Handling

Operations use ScientificError and structured error codes, including:

- INVALID_SHAPE
- INVALID_STATE
- NON_FINITE_VALUE
- SINGULAR_MATRIX
- UNCERTAIN_RESULT

## Limitations

- Real Float64 matrices only.
- Inverse and solve require square matrices.
- No physical units or coordinate-frame metadata.
- No claim of flight readiness or operational spacecraft accuracy.
