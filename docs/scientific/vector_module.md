# ARC-04 Scientific Vector Module

## Scope

This module provides numeric Float64 2D and 3D vector operations for the
educational Quantum Space AGI prototype. It is not flight software and does not
implement physical unit safety or coordinate-frame conversion.

The vector module currently uses NumPy for storage and calculations. Values,
units, and coordinate frames are not bundled together. Callers must keep unit
and frame compatibility separate and explicit.

## Public API

```python
create_vector(values, *, field="vector") -> numpy.ndarray
add(left, right) -> numpy.ndarray
subtract(left, right) -> numpy.ndarray
scale(vector, scalar) -> numpy.ndarray
dot(left, right) -> float
cross(left, right) -> numpy.ndarray
magnitude(vector) -> float
normalize(vector) -> numpy.ndarray
distance(left, right) -> float
```

No `vector` or `construct_vector` alias is part of the package API.
`create_vector` is the public construction function.

## Mathematical Definitions

- Addition and subtraction are component-wise and require equal dimensions.
- Scalar multiplication multiplies each component by a finite real scalar.
- Dot product is the sum of component-wise products:
  `sum(left[i] * right[i])`.
- Cross product is defined only for two three-dimensional vectors and follows
  the right-hand Cartesian convention.
- Magnitude uses an overflow-resistant `math.hypot` calculation.
- Normalization divides a nonzero vector by its magnitude.
- Euclidean distance is the magnitude of `left - right`.

## Input and Output Types

Public operations accept one-dimensional sequences or NumPy arrays containing
real numeric values. Internally, vectors are validated and copied into
`numpy.float64` arrays.

Inputs are never mutated. Operations return new arrays or scalar `float`
results. Boolean values, complex values, strings, objects without real numeric
values, and unsupported dimensions are rejected.

## Error Behavior

The module uses the existing `ScientificError` and `ScientificErrorCode`
taxonomy:

- `invalid_dimension` for unsupported vector dimensions and dimension
  mismatch.
- `invalid_shape` for malformed arrays at other ARC-04 boundary helpers.
- `non_finite_value` for NaN, infinity, and operations that overflow or produce
  a non-finite result.
- `invalid_state` for booleans, malformed scalar inputs, and zero-vector
  normalization.

Invalid operation inputs or outputs raise `ScientificError` rather than
returning fallback values.

## Numerical Limitations

- Individual input components and operation results must be finite Float64
  values.
- Floating-point overflow is rejected instead of wrapped or silently clamped.
- Magnitude uses `math.hypot` for stability across small and large finite
  values.
- Dot and cross products can overflow even when inputs are finite; this is
  reported as a non-finite result.
- Subtracting large opposite-sign inputs may overflow before distance is
  calculated; this is reported instead of returning an uncertain value.
- The module does not define a near-zero magnitude threshold. Normalization
  rejects only an exactly zero magnitude.
- ARC-04 tolerance defaults are not silently applied by vector operations.

## Unit and Coordinate-Frame Limitations

This module performs dimensionless numeric operations only. It does not:

- Convert physical units.
- Detect conflicting units.
- Convert coordinate frames.
- Assume that magnitude, dot product, or cross product has physical meaning.

Those behaviors require future approved immutable quantity/vector and frame
interfaces.

## Test Status

The test suite includes construction, copy behavior, arithmetic, scalar input,
dot and cross products, stable magnitude cases, normalization, distance,
dimension mismatch, complex and boolean rejection, mutation protection, and
overflow behavior.

At the time of implementation, pytest was not available in the global
interpreter and the full pytest suite remained unexecuted. Python compilation
and focused standard-library/NumPy runtime checks were used instead.
