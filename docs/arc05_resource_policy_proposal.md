# ARC-05 Resource Policy Proposal

**Status:** Proposed; owner decision required. No runtime policy or API change
has been implemented.

**Prepared:** 2026-11-14

## Decision requested

Approve or reject an opt-in maximum-sample guard for propagation. If approved,
confirm:

1. whether the limit belongs in `SimulationConfig`, on individual workflow
   calls, or at the caller/service boundary;
2. the error type and public message for exceeding the limit;
3. whether rejection should use a conservative full-run sample bound even when
   early collision detection might stop sooner;
4. whether a sample-count cap is sufficient for this ARC or a separate memory
   budget is required; and
5. whether any downstream configuration or serialization contracts need a
   migration plan.

Until these decisions are made, ARC-05 keeps its current unbounded behavior.

## Current API and behavior

`SimulationConfig` validates finite positive duration and timestep but has no
resource fields. `run_simulation(config)` passes the initial state and scalar
parameters to `propagate_two_body(...)`, then computes trajectory diagnostics.
The public `propagate_two_body` function accepts five positional parameters and
does not preflight the number of integration steps. It appends Python objects
to lists before creating NumPy arrays. A small but advancing timestep can
therefore request very large runtime and memory use. The numerical progress
guard only rejects timesteps that cannot advance the float64 time grid.

The current documentation estimates retained arrays at roughly 112 bytes per
sample, with higher and platform-dependent transient peak use. Those estimates
are planning aids and are not suitable as exact memory admission checks.
Collision detection may shorten a run, but it cannot safely be relied upon as a
resource bound because the event may not occur.

## Candidate design

Prefer an opt-in `max_samples` limit over a universal default or a nominal
memory-byte estimate:

- Add an optional `max_samples: int | None = None` setting to
  `SimulationConfig`, subject to approval of the configuration/serialization
  change.
- Add an optional keyword-only `max_samples: int | None = None` parameter to
  `propagate_two_body` so direct callers can request the same guard without
  changing its existing five positional arguments.
- Have `run_simulation` pass the configured value through to propagation.
- Treat `None` as no cap. This preserves the behavior of existing callers and
  introduces no arbitrary global threshold. It also means callers receive no
  resource protection unless they opt in.
- Require an explicitly supplied value to be a positive integer and reject
  booleans, zero, negative values, and non-integer values.
- Before the first derivative evaluation or trajectory allocation, compare the
  limit against a conservative upper bound for the full configured run, not an
  assumed early collision. A rejected run should return no partial trajectory.
- If a typed exception is preferred, add a new resource-limit exception that
  subclasses `ValueError` so existing broad `ValueError` handlers remain
  compatible. The exact name and message require approval.

The candidate sample bound is `ceil(duration_s / time_step_s) + 1`, including
the initial state and a shortened final step. Implementation must confirm this
bound against the actual floating-point stepping and final-time snap behavior.
If it is not a guaranteed upper bound for all accepted finite inputs, derive
and test a conservative integer bound before using it for admission.

A sample cap bounds loop iterations and the number of trajectory/diagnostic
elements; it does **not** guarantee a byte-level memory ceiling across Python,
NumPy, or platforms. A byte budget should be a separate decision based on a
maintained conservative allocation model, not the current approximate
`112N`/`304N` documentation estimates.

## Backward compatibility and integration

Appending a keyword-only optional argument to `propagate_two_body` preserves
existing positional calls. A new config field with a `None` default accepts
existing input configurations, but it may change serialized model output or
schemas that reject unknown fields. Downstream owners should review that before
adding it. `run_simulation(config)` remains unchanged for callers who do not
opt in. No existing successful workload should be rejected while the limit is
`None`.

If the team chooses caller-side admission instead, ARC-05's public signatures
can remain unchanged, but each caller must implement and test its own bound.
That policy does not protect direct users of `propagate_two_body`.

## Required tests if the policy is approved

1. Existing configuration and workflow calls without a limit produce the same
   trajectory shape, times, states, diagnostics, and collision result as before.
2. `None` preserves the current unbounded behavior and adds no default cap.
3. A configured trajectory whose conservative sample bound equals the limit
   succeeds; a limit one sample below the bound fails before derivative
   evaluation or array allocation.
4. The public low-level propagation API accepts the approved keyword-only form
   while all legacy five-positional-argument calls continue to pass.
5. `run_simulation` passes a configured limit through to propagation and
   surfaces the approved resource-limit error without returning partial output.
6. Invalid values (boolean, zero, negative, float, string, and non-finite
   values where accepted by the chosen type boundary) are rejected
   deterministically.
7. Boundary cases cover duration shorter than one step, exact duration/step
   ratios, non-integral ratios, shortened final steps, and values near
   float64 representability limits. Confirm the preflight bound never
   underestimates the actual number of stored samples.
8. A case with an early collision confirms whether the policy intentionally
   checks the full configured upper bound rather than assuming the event will
   reduce resource use.
9. A spy derivative proves limit rejection happens before any integration
   work; a workflow test proves failure returns no partial trajectory.
10. Tests run with multiple NumPy error policies to ensure resource checks do
    not depend on global floating-point settings.

These are a proposed test plan, not executed tests: the corresponding behavior
does not exist until the policy is approved and implemented.

## Decision record

| Decision | Current status |
|---|---|
| Select an engine-enforced guard | Pending owner approval |
| Select `max_samples` and configuration/call placement | Proposed, not approved |
| Select any universal default or threshold | None; no arbitrary default proposed |
| Select byte-level memory budget | Deferred; current estimates are not admission-grade |
| Implement code or tests | Not authorized before the API/policy decision |
