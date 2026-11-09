# Algorithm Conventions (Nov 1 catch-up)

This document records local conventions used by the ARC-06/ARC-07 starter. These are implementation choices for a generic reusable engine, not official NASA requirements or team-approved architecture decisions.

## Scope and boundaries

- Keep optimization independent of mission, spacecraft, API, and UI models.
- Use Python and the standard library for this first classical baseline. The internal handbook recommends Python for the API and SciPy Optimize / OR-Tools for optimization; no runtime dependency is needed for the finite synthetic baseline.
- Keep QUBO/QAOA behind a future adapter. They are not part of the core path.
- Do not encode a complete challenge-specific mission solution here.

## Determinism and data

- Represent objective functions, constraints, domains, and results with small typed interfaces and immutable result records.
- Enumerate variable names in lexical order and values in caller-provided domain order.
- Keep the first candidate when objective values are equal within the configured comparison tolerance.
- Model-data errors such as empty domains, non-finite numbers, and missing/extra variables use `ValueError`. QUBO validators and explicitly typed example arguments use `TypeError` for runtime type mismatches; invalid values and ranges remain `ValueError`s.
- Constraint feasibility uses each constraint's explicit non-negative tolerance. Objective comparison tolerance is separate.
- A solver reports its scope and work count; it must not imply a global optimum when its algorithm does not establish one.

## Solver interface

`Solver.solve(problem)` returns a structured `OptimizationResult`. The result includes status, selected values (if feasible), objective value, per-constraint evaluations, evaluated-candidate count, and solver name. A finite-domain enumerative solver is the reference classical baseline for small synthetic problems.

## Decisions to align before integration

The repository has no existing domain/API contracts. Before connecting this package to other modules, Nini should align with Yousuf and Sonjoy on:

1. Whether optimization values use plain numbers or shared unit-aware quantities from ARC-02/ARC-04.
2. Stable variable/constraint identifiers and the serialization shape expected by the API.
3. Whether `OptimizationResult` should be translated into a shared API result envelope, and who owns that adapter.
4. The supported Python version and dependency policy for the integrated repository.

Until those choices are agreed, these types remain package-local and make no assumptions about teammate modules.
