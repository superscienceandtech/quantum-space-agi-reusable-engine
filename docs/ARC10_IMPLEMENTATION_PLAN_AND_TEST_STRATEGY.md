# ARC-10 Implementation Plan, Task Breakdown & Test Strategy

**Status:** Planning only. No architecture, API contract, framework, or implementation is approved by this plan.

## 1. Executive Summary

The refreshed ARC-10 branch starts at 19157592d389f7fbb41830379a38efc464680c94 and contains only README.md. The inspected ARC-08 checkout has reusable core, data, and ml code but no dedicated HTTP backend. Locally available origin/main includes ARC-05 simulation/optimization and the ARC-09 prototype; those are not integrated into ARC-10.

Implementation is blocked until the project selects the target repository and first use case and approves the architecture and authoritative API contract. Process health, dataset validation/quality, and dashboard summary are candidates only. This plan does not select a winner.

## 2. Evidence and Repository Baseline

**VERIFIED inspection snapshot:** ARC-08 checkout arc/08-ai-ml at de48b077571fe44b1fc8b7ab8fad6ba60016f029; one modified tracked VOTable test and eleven untracked ARC-08 paths were present. No staged paths. These remained outside the ARC-10 worktree.

**VERIFIED fetched ARC-10 snapshot:** origin/arc/10-api-integration at 19157592d389f7fbb41830379a38efc464680c94; one commit; only README.md. The branch comparison used the locally available origin/main reference, not a freshly fetched main branch. Unpushed co-owner work is not observable.

**VERIFIED reference findings:** Current ARC-08 checkout contains core, data, and ml; no API framework or routes. origin/main contains ARC-05, optimization, ARC-09 prototype, and a contract request that defines no endpoints/schemas. ARC-09 uses synthetic/conceptual sample data and no backend requests.

## 3. Readiness and Decision Gates

| Gate | Required evidence/decision | Why it blocks work | Approval role | Work unlocked | Status |
|---|---|---|---|---|---|
| Production repository/branch | Confirm official backend target and integration branch. | Avoid wrong codebase. | Project/engineering owner; process to confirm. | Repository-specific work. | BLOCKING |
| First use case | Select a product operation and consumer. | Determines contracts/security. | Project/product authority. | Focused requirements. | BLOCKING |
| Framework/runtime | Choose framework and runtime policy. | Determines app/dependencies/tests. | Architecture owner/technical lead. | Backend foundation. | BLOCKING |
| Contract owner/source | Identify authoritative versioned contract and owner. | Avoids conflicting schemas. | Project technical process. | Contract design. | BLOCKING |
| Endpoints and DTOs | Approve paths, methods, fields, types/nullability, versioning. | Required for routes/clients. | API contract owner. | Implementation. | BLOCKING |
| Scientific semantics | Units, frames, precision, uncertainty, provenance. | Prevents scientific misrepresentation. | Relevant domain/scientific owner. | Scientific mapping. | CONDITIONAL / BLOCKING if selected |
| Error/status conventions | Define validation/domain/upstream/empty behavior. | Consistent clients. | API contract owner. | Error translation. | BLOCKING |
| Auth/security/configuration | Define authz, CORS, secrets, environment. | Cannot be safely guessed. | Security/platform role to identify. | Protected operation. | BLOCKING where applicable |
| Resource limits | Define payload/compute/time budgets and long-task policy. | Protect availability. | Technical/platform owner. | Bounded execution. | BLOCKING |
| Engine integration | Identify modules and approved branch integration. | Simulation/optimization absent from ARC-10. | Relevant ARC owners/process. | Domain service. | CONDITIONAL |
| Frontend target | Confirm production client repo/stack/base URL. | Needed for client work. | Product/frontend owner to identify. | Phase 4. | CONDITIONAL |
| Test/review expectations | Define acceptance matrix and review path. | Needed for release evidence. | ARC-10 reviewer/project process. | QA/release. | BLOCKING before completion |

Repository and package structure are verified; no product/API gate is marked approved by this plan.

## 4. Conditional Architecture and Layer Responsibilities

**PROPOSED — REQUIRES APPROVAL:** Keep a framework-neutral service/use-case layer between HTTP transport and approved engine functions. Use explicit DTOs; do not expose internal engine objects directly.

| Layer | Role | Inputs/outputs | Approval dependencies |
|---|---|---|---|
| HTTP transport | Parse request, invoke service, emit status/body. | HTTP ↔ transport primitives. | Framework/route/error contract. |
| Schema/DTO | Validate transport types/nullability and map wire values. | JSON ↔ typed DTOs. | Contract; domain review for scientific fields. |
| Application service | Orchestrate selected use case. | Validated request ↔ use-case result. | Product scope and engine availability. |
| Engine/domain | Existing calculations/data APIs. | Typed domain input/output. | Module integration/domain approval. |
| Infrastructure/security | Configuration, logs, providers, auth, limits. | Operational concerns. | Security/platform policy. |
| Testing | Unit/API/integration/contract/regression coverage. | Approved examples and acceptance criteria. | Contract/test policy. |

Do not add queues, databases, or persistence unless the selected use case demonstrates the need.

## 5. MVP Workstream Options

No option is selected. Complexity describes likely engineering effort, not product priority.

### Option A — Process Health/Status

- **Preconditions:** Operational consumer and liveness/readiness definition.
- **Tasks:** Implement only approved semantics; include version/timestamp only if required.
- **Risks:** Process health may be mistaken for dependency or scientific readiness.
- **Tests:** Healthy response, agreed unavailable behavior, no unintended external probes.
- **Acceptance:** Response matches documented status semantics.
- **Complexity:** Low if process-only; higher with dependency checks.

### Option B — Dataset Validation/Quality

- **Preconditions:** Select use case; approve schemas, submitted-data policy, limits and output contract.
- **Tasks:** Map request to current DataSchema, validate_dataset(), and optionally analyze_quality(); map results to DTOs.
- **Risks:** Privacy, size, retention/logging, and confusing mechanical checks with scientific eligibility.
- **Tests:** Valid/invalid/empty/malformed inputs, limits, stable issue mapping, no mutation or unintended retention.
- **Acceptance:** Correct mechanical report and explicit scientific-validation boundary.
- **Complexity:** Medium; engine support exists in ARC-08, transport policy is unresolved.

### Option C — ARC-09 Dashboard Summary

- **Preconditions:** Approve summary as initial slice and define each metric/source/aggregation/unit/freshness/provenance.
- **Tasks:** Implement approved summary service/mapping; integrate only to confirmed frontend.
- **Risks:** Synthetic prototype values may be mistaken for production metrics; backing source undefined.
- **Tests:** Valid, empty, stale, malformed, error cases; no synthetic fallback as live.
- **Acceptance:** Each metric maps to approved fields; UI states remain distinct.
- **Complexity:** Medium to High depending on source/aggregation.

Simulation and optimization remain separate future workstreams pending an approved use case, branch integration, domain review, and compute bounds.

## 6. Phased Implementation Plan

| Phase | Tasks and deliverables | Exit criteria | Status |
|---|---|---|---|
| 0 — Repository readiness and evidence | Record checkout/ref boundaries, modules/dependencies/tests/status; preserve unrelated work. | Evidence distinguishes current branch from refs and lists unknowns. | Completed for this planning package; repeat before implementation. |
| 1 — API contract and architecture approval | Select target/use case; designate contract owner; approve framework, endpoints, schemas, scientific semantics, security and operations. | Versioned contract and decisions recorded. | Blocking/incomplete. |
| 2 — Backend foundation | After approval, implement app boundary, validation, service layer, config, error mapping and test harness. | App and layer boundaries covered by tests. | Blocked by Phase 1. |
| 3 — First API use case | Implement selected operation, engine mapping, limits and error translation. | Contract examples pass; no unapproved science decisions embedded. | Blocked by Phases 1–2. |
| 4 — API client and frontend integration | Confirm production target; implement client and approved UI mapping/states. | Client uses authoritative contract; no synthetic data presented as live. | Blocked by contract/frontend target. |
| 5 — Unit and integration testing | Unit, API, integration, contract, security/resource and regression tests. | Acceptance matrix passes; actual commands/results recorded. | Planning can start; execution needs implementation. |
| 6 — Implementation documentation | Document config, API, examples, operations, limits and handoff. | Docs match shipped behavior/review. | Finalization follows implementation. |

## 7. Responsibility and Review Matrix

Roles reflect task-provided ownership context; detailed allocation/authority follows project process.

| Work | Responsible role | Review/approval | Boundary |
|---|---|---|---|
| Repository/architecture investigation | Rafi, coordinating with Sonjoy as co-owner | Amran reviews | Evidence only; no implementation approval. |
| Requirements/draft schemas | Rafi prepares; Sonjoy co-owns | Yousuf's stated contract/technical role; domain owner as relevant | Draft until approved. |
| Architecture/framework decisions | ARC-10 co-owners prepare options | Yousuf's technical-direction role; project process determines final authority | No framework assumed. |
| Backend/client implementation | ARC-10 co-owners; Rafi's client work only after contract approval | Amran reviewer; Yousuf's stated final review | Starts after gates. |
| Metric definitions/mapping | Requirements owner coordinates | Yousuf's stated metric responsibility; relevant domain owner | Prototype labels not authoritative. |
| Tests | Rafi's stated testing responsibility, coordinating with Sonjoy | Amran reviewer | Record actual results. |
| Documentation/handoff | Rafi's stated responsibility | Amran reviewer; Yousuf's final review role | Separate technical completion from approval. |

## 8. Testing Strategy

Tests can be planned now; exact assertions/examples require an approved contract.

| Layer | Proposed coverage |
|---|---|
| Unit | Request validation, service behavior, DTO mapping, domain error mapping, units/provenance, numeric/array serialization. |
| HTTP integration | Valid/invalid/empty input, status/body, timeout/limits, provider failures only if needed. |
| Contract | Required/optional fields, types, nullability, IDs, status/error schemas, compatibility, scientific semantics. |
| Security/robustness | Oversized/malformed JSON, excessive records/dimensions, secret/sensitive-data redaction, auth boundaries. |
| Regression | Engine behavior unchanged; outputs not mutated/reinterpreted; serialization explicit. |
| Frontend | Loading/Success/Empty/Error, mapping, no synthetic fallback as live. |

Do not write or run tests in this planning task.

## 9. Dependencies and Critical Path

    Phase 0 evidence
        -> choose use case + confirm target/owner
        -> approve contract and architecture
        -> backend foundation
        -> selected operation
        -> tests/review
        -> documentation/release
                        \
                         -> client integration only after contract and frontend target

Simulation/optimization additionally require cross-ARC integration and domain review. Critical path is target/use case → contract authority → approved contract → foundation → operation → tests/review.

## 10. Risk Register

| Risk | Likelihood | Impact | Mitigation | Owner role | Trigger |
|---|---|---|---|---|---|
| Wrong repository/branch | Medium | High | Verify target/latest owner work before writing. | Project/engineering owner | Target unclear. |
| Unapproved endpoint | Medium | High | Require recorded contract approval. | ARC-10 co-owners | Draft treated as contract. |
| Synthetic metrics treated as real | Medium | High | Label prototype; test no live fallback. | Frontend/API owners | Sample copied into response. |
| Incorrect scientific semantics | Medium | High | Domain review and contract tests. | Scientific/data owner | Scientific field exposed. |
| Transport coupled to engine | Medium | Medium | Keep service and DTO boundaries. | Implementation owners | Route serializes internal object. |
| Unbounded work | Medium | High | Approve/enforce body, dimension, time budgets. | Technical/platform owner | Arbitrary workload accepted. |
| Premature auth/persistence/deployment | Medium | High | Decide only from approved needs. | Project/security/platform role | Infrastructure added without use case. |
| Cross-branch incompatibility | Medium | High | Confirm module availability/integration. | ARC owners | Simulation/optimization selected. |
| Contract drift | Medium | Medium | Version contract; review breaking changes. | Contract owner | Field semantics change. |

## 11. Acceptance Criteria and Definition of Done

**PROPOSED DoD:**

- Architecture and contract approved and traceable.
- Endpoint/schema definitions versioned.
- Engine-to-DTO mapping preserves approved units/provenance/frames/precision.
- Nullability, empty, domain errors and HTTP errors documented.
- Request/compute limits enforced and tested.
- Required security controls implemented and tested.
- Unit, integration, contract, negative and regression tests pass with actual results recorded.
- Existing engine behavior remains unchanged.
- Client targets approved frontend if in scope.
- Documentation reflects behavior and limitations.
- Reviewer feedback and project approval recorded through project process.

Software completion is not scientific validation, NASA authorization, or project approval.

## 12. Implementation Authorization Checklist

- [ ] Production backend repository/branch confirmed.
- [ ] First use case and consumer approved.
- [ ] Contract owner and authoritative versioned contract identified.
- [ ] Framework/runtime approved.
- [ ] Endpoint paths/methods and schemas approved.
- [ ] Scientific semantics reviewed where relevant.
- [ ] Error/empty/status behavior agreed.
- [ ] Auth, CORS, secrets and data access decided where applicable.
- [ ] Resource, timeout and long-running behavior agreed.
- [ ] Required ARC modules available in target branch.
- [ ] Production frontend confirmed before client work.
- [ ] Test, review and release expectations recorded.

## 13. Recommended Immediate Next Actions

1. Confirm production target and review latest co-owner branch work.
2. Select the first use case; validation and dashboard summary remain candidates.
3. Identify contract owner and obtain authoritative field/error/security requirements.
4. Review scientific mappings with domain owners.
5. Begin implementation only after gates are recorded as approved.

**Readiness conclusion:** Planning can continue. Backend and client implementation are blocked on use-case and contract approval. Framework, scientific meaning, security and operational decisions require appropriate approval. This plan does not authorize implementation.
