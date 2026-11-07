# ARC-04 Scientific Computing Foundation

## Project Purpose

This foundation provides reusable, testable validation and numerical-comparison
utilities for the Quantum Space AGI educational mission-design game. It is
part of an educational research prototype, not flight software and not a
substitute for validated aerospace engineering tools.

This milestone implements numeric 2D/3D vector operations without unit or
coordinate-frame metadata. It does not implement matrix operations, unit
conversion, orbital mechanics, or ARC-05 simulation algorithms.

## Module Responsibilities

- `scientific.errors`: defines stable scientific error codes and structured
  error diagnostics.
- `scientific.validation`: validates finite numbers, supported vector
  dimensions, and rectangular matrices.
- `scientific.precision`: provides configurable absolute/relative numerical
  comparison.
- `scientific.vector`: provides Float64 2D/3D construction, arithmetic,
  products, magnitude, normalization, and distance without unit or frame
  metadata.

## Error Handling

Scientific utilities raise `ScientificError`, which is also a Python
`ValueError`. Each error has a stable machine-readable code, a useful
message, and optional field, expected, received, and diagnostic information.

The supported codes are:

- `invalid_dimension`
- `invalid_shape`
- `non_finite_value`
- `unit_mismatch`
- `frame_mismatch`
- `singular_matrix`
- `uncertain_result`
- `invalid_state`

The current implementation uses standard-library exceptions and dataclass-like
structured objects. Pydantic integration may validate public API boundaries in
a later milestone.

## Numerical Comparison Policy

`is_close(actual, expected)` uses the combined absolute/relative rule:

```text
abs(actual - expected) <= atol + rtol * max(abs(actual), abs(expected))
```

The provisional defaults are:

- `atol = 1e-12`
- `rtol = 1e-9`

These values are not approved universal scientific standards. Domain-specific
simulation, visualization, optimization, and AI/ML models may require different
tolerances.

`ComparisonTolerance` provides configurable, validated tolerance values.
Negative and non-finite tolerance values are rejected. Actual and expected
values must also be finite real numbers.

## Provisional Assumptions

- Python 3 is the implementation language.
- NumPy is retained for future numerical arrays and kernel integration.
- Pydantic is planned for API-model validation; it is not required by the
  current standard-library foundation code.
- Scientific utility APIs may evolve until reviewer conventions are approved.
- Float64 is a proposed precision policy, not an approved universal standard.
- SI units and coordinate-frame conventions are intentionally deferred from
  this foundation milestone.

## Known Limitations

- Vector validation and numeric vector arithmetic support 2D and 3D
  dimensions. Vector values remain numeric and do not imply approved physical
  units or coordinate-frame compatibility.
- Matrix validation checks rectangularity but does not perform transformations
  or linear algebra.
- Physical units, unit conversion, frame transforms, and quantity objects are
  not implemented.
- No integrator, timestep policy, orbital model, optimizer, or random-number
  stream is implemented.
- Comparisons are only for scalar real values.
- NumPy values and Python numeric types require broader integration testing
  before final public API approval.

## Running Tests

From the repository root, install the declared development dependencies, then run:

```powershell
python -m pytest
```

No package installation was performed during this milestone.

## Future ARC-04 and ARC-05 Integration Points

Future ARC-04 work should add:

- Additional NumPy/Pydantic boundary validation and performance integration
- Matrix operations and transformations
- Quantity and unit interfaces
- NumPy/Pydantic boundary adapters
- Regression and property-based numerical tests

Future ARC-05 integration may reuse:

- `ScientificError` for invalid state and numerical failures
- `ComparisonTolerance` for convergence and validation decisions
- `validate_finite`, `validate_vector`, and `validate_matrix`
- Explicit simulation state units, frames, timestep metadata, and model versions

The simulation contract must coordinate coordinate frames, integration policy,
random seeds, diagnostics, and partial-result behavior with Nini and the
backend team. Those decisions remain subject to review.
