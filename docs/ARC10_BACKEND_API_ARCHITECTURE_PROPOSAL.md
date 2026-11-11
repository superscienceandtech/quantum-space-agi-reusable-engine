# ARC-10 Backend/API Architecture Proposal

**Status:** Proposal only. The architecture, framework, runtime, endpoint scope, and deployment approach below are not team-approved and do not authorize implementation.

## 1. Executive Summary

The refreshed arc/10-api-integration branch starts at the repository initialization commit and contains only README.md. The inspected arc/08-ai-ml checkout contains reusable core, data, and ml Python libraries but no HTTP backend. Locally available origin/main contains additional ARC-05 simulation, optimization, and ARC-09 prototype materials; these are not integrated into the ARC-10 branch.

**PROPOSED — REQUIRES ARCHITECTURE OWNER APPROVAL:** If a first service use case is approved, use a small modular monolith with separate transport, request/response schema, application-service, engine, and infrastructure responsibilities. Keep scientific code framework-neutral and expose only product-approved capabilities.

No framework is selected here. FastAPI, Flask, and Django REST Framework remain options for evaluation.

## 2. Audit Findings Used as Architectural Evidence

| Evidence | Finding | Scope |
|---|---|---|
| src/quantum_space_agi/core/results.py in inspected ARC-08 checkout | Immutable Result and ErrorInfo conventions exist, but they are not HTTP error contracts. | Current ARC-08 checkout. |
| src/quantum_space_agi/data/models.py, schemas.py, provenance.py | Dataset and provenance/schema APIs exist; nested Dataset containers are not deeply frozen. | Current ARC-08 checkout. |
| src/quantum_space_agi/ml/ | Reusable ML preparation/evaluation/readiness functions exist. | Current ARC-08 checkout. |
| pyproject.toml at ARC-08 HEAD | Runtime dependencies are empty; no web framework is declared. | Current ARC-08 checkout, not ARC-10 base. |
| docs/ARC09_BACKEND_DATA_CONTRACT_REQUEST.md | Requests an authoritative contract; explicitly supplies no paths, methods, or response schemas. | Locally available origin/main only. |
| arc09-ui-prototype/ | Isolated plain HTML/CSS/JS prototype; synthetic data; no API integration. | Locally available origin/main only. |
| src/quantum_space_agi/simulation/ and optimization/ | Potential engine integration surfaces, but absent from refreshed ARC-10 branch. | Locally available origin/main only. |

## 3. Architecture Goals and Non-Goals

**PROPOSED goals:**

- Separate HTTP parsing/status behavior from engine logic.
- Validate request data at a transport boundary and preserve domain-level validation.
- Keep an application/use-case layer responsible for orchestration.
- Preserve approved scientific units, frames, precision, provenance, timestamps, and nullability.
- Provide test seams at service and HTTP boundaries.

**Non-goals:** This proposal does not define endpoints, DTO fields, authentication, a database, a queue, deployment, or production frontend behavior. It does not require every module to become an API endpoint.

## 4. Proposed High-Level Architecture

ILLUSTRATIVE — NOT APPROVED:

    Approved frontend/client
            |
    HTTP transport and routing
            |
    Request/response DTO validation
            |
    Application services / use cases
            |
    Approved engine APIs: core, data, ml
            |                    \
    Approved provider adapters   Simulation/optimization only after branch integration

This is a proposal, not an existing or approved package architecture.

## 5. Layer Responsibilities

| Layer | Proposed purpose | Inputs/outputs | Approval/dependency |
|---|---|---|---|
| API / transport | Parse HTTP requests, route operations, format response primitives, apply approved status codes. | HTTP request ↔ transport response. | Framework and endpoint contract. |
| Request/response schemas | Enforce approved types, nullability, limits, and transport constraints. | JSON/primitives ↔ typed request/result DTOs. | Contract owner and domain review for scientific fields. |
| Application/service | Coordinate one use case and convert between transport and engine boundaries. | Validated request → service result. | Selected product use case. |
| Engine/domain | Perform scientific or data operations without HTTP dependencies. | Domain inputs → domain results. | Relevant module available and approved for exposure. |
| Infrastructure | Explicit runtime configuration, logging, provider calls, and approved persistence/security integration. | Operational dependencies. | Security, deployment, and data-use decisions. |
| Testing | Unit, API, integration, contract, and regression coverage. | Defined contract examples and service dependencies. | Contract and acceptance policy. |

ILLUSTRATIVE — NOT APPROVED possible package layout:

    api/
      transport/        framework-specific handlers
      schemas/          approved wire DTOs
      services/         use-case orchestration
      infrastructure/   approved runtime/provider integrations
    tests/
      api/
      contracts/

## 6. Python Backend Framework Comparison

No framework was installed or selected. Comparison is qualitative; dependency versions and maintenance costs should be evaluated before selection.

| Option | Strengths | Costs/considerations | Current fit |
|---|---|---|---|
| FastAPI | Pydantic-oriented typed request/response handling and OpenAPI/JSON Schema generation; sync and async handlers; pytest-compatible test client. | Adds framework dependencies, including its ASGI ecosystem and test-client dependencies. CPU-bound engine calls still require limits. | PROPOSED candidate; REQUIRES APPROVAL. Pydantic appears in simulation code only on origin/main, not the ARC-10 base. |
| Flask | Small routing foundation and flexible integration; test client available. | Schema validation and API-documentation conventions need separate choices; async views do not make CPU-bound work faster. | PROPOSED candidate; REQUIRES APPROVAL. Could suit a small synchronous service if the team prefers explicit assembly. |
| Django REST Framework | Mature serializers, validation, request/response behavior, and API-focused test tools within Django. | Larger framework/application model and more configuration than currently evidenced; async needs version-specific review. | PROPOSED candidate; REQUIRES APPROVAL. Better justified if broader Django capabilities become requirements. |

Official references:
- https://fastapi.tiangolo.com/features/
- https://fastapi.tiangolo.com/tutorial/testing/
- https://flask.palletsprojects.com/en/stable/async-await/
- https://flask.palletsprojects.com/en/stable/testing/
- https://www.django-rest-framework.org/api-guide/serializers/
- https://www.django-rest-framework.org/api-guide/testing/

## 7. Proposed Technology Stack

**PROPOSED — REQUIRES ARCHITECTURE OWNER APPROVAL:** Evaluate one Python HTTP framework after the product/use case and contract owner are known. Keep application services and engine APIs framework-neutral where practical. Use explicit DTO mapping and existing pytest conventions. Do not add a framework until selected and authorized.

No database, authentication provider, deployment platform, API client library, queue, or persistence layer is selected.

## 8. Scientific Engine Integration Strategy

- core — current ARC-08 checkout: reusable validation/numerical helpers and generic Result/ErrorInfo. Route handlers should not map these ad hoc in multiple places.
- data — current ARC-08 checkout: Dataset, Provenance, schemas, validators, and adapters. Structural validation is not scientific correctness.
- ml — current ARC-08 checkout: readiness/preparation/evaluation facilities. Exposing them must not imply scientific approval or real-data results absent evidence.
- simulation — origin/main only: ARC-05 workflow with Pydantic SimulationConfig/OrbitalState, SI/ECI contracts, RK4, and NumPy arrays in results. No simulation API exposure is approved; this code is absent from refreshed ARC-10.
- optimization — origin/main only: objective/constraint interfaces, optimization problem/result models, and enumerative solver. No product use case or safe workload contract is established.

Routes should call application services rather than orchestrating multiple engine modules directly. Services should preserve engine behavior and must not infer scientific semantics from transport labels.

## 9. API and Serialization Boundaries

**PROPOSED:**

1. Parse and validate transport data against an approved schema.
2. Map validated input explicitly to an engine/service input.
3. Invoke the approved use case.
4. Map results into JSON-compatible, versioned transport DTOs.
5. Convert expected errors into approved HTTP behavior; redact unexpected failures.

Pydantic can be considered at the boundary if approved. It must not silently replace domain validation. Scientific output serialization must explicitly define array shape/order, numeric precision, non-finite handling, units, reference frame, provenance, timestamps, uncertainty, and optional fields. Result and domain exceptions need an agreed mapping to transport statuses and payloads. Do not expose internal Python objects directly.

## 10. Configuration and Security Strategy

**PROPOSED; choices remain TBD:**

- Keep environment-specific configuration explicit and separate from source.
- Use an approved secret-management mechanism; do not select a provider here.
- Define authentication/authorization only after access requirements are known.
- Configure CORS only if the approved browser client requires cross-origin requests.
- Bound request sizes, record counts, array dimensions, simulation steps, and solver workloads according to the selected use case.
- Avoid logging credentials, full payloads, or sensitive scientific data by default.

## 11. Reliability and Performance Strategy

**PROPOSED:** Begin with bounded synchronous requests only if the selected operation fits a request lifecycle. Define timeouts, cancellation, safe retries, error propagation, and correlation IDs. Measure workloads before considering background jobs. CPU-intensive simulation/optimization may block request workers; do not add queues or workers without evidence and approval.

## 12. Frontend Integration Boundary

The ARC-09 prototype in origin/main is a visual reference only. Its values are synthetic/conceptual, its state examples make no requests, and no production frontend repository/stack was identified. Prototype names must not become API fields by assumption.

Before client integration, confirm the production frontend repository, technology/build process, API base URL configuration, auth/session behavior, approved data mapping, and Loading/Success/Empty/Error states. Never present synthetic fallback data as live.

## 13. Architecture Options Comparison

| Option | Advantages | Trade-offs | Assessment |
|---|---|---|---|
| Modular monolith | One deployable service; straightforward Python engine reuse, local testing, and module separation. | Requires discipline to keep transport out of engine code; CPU work must be bounded. | PROPOSED simplest candidate if a single service is approved. |
| Service-oriented split | Independent deployment/scaling and ownership boundaries where demonstrated needs exist. | Adds network contracts, security, observability, deployment, and compatibility overhead. | FUTURE; no current requirement supports this complexity. |

## 14. Recommended MVP Architecture

**PROPOSED — REQUIRES APPROVAL:** If a single service is selected, use a modular monolith: thin HTTP transport, explicit DTO mapping, a small service/use-case layer, framework-independent engine calls, centralized error translation, and tests at each boundary. The product owner must select the first operation. No route is prescribed here.

## 15. Future Expansion Strategy

**FUTURE, conditional on evidence:** background jobs for operations that exceed agreed request budgets; persistence for an approved durable-state requirement; service separation for independent scaling or ownership; and generated clients from an approved OpenAPI contract. None is an MVP requirement established by inspected evidence.

## 16. Risks and Trade-offs

- Choosing the wrong branch/repository could duplicate or conflict with co-owner work.
- Prototype data could be mistaken for real product or scientific data.
- Incorrect unit, frame, provenance, nullability, or precision mappings could mislead users.
- Direct route-to-engine coupling could expose unstable internal contracts.
- Unbounded input or computation could exhaust resources.
- Premature auth, persistence, or deployment choices add unsupported scope.
- Framework selection changes dependencies and maintenance burden.

## 17. Decisions Requiring Approval

REQUIRES APPROVAL / TBD: target repository/branch; first product operation; framework/runtime; contract owner; endpoint paths/methods; DTO and versioning policy; scientific semantics; error/status conventions; authentication/authorization/CORS/secrets; request and compute limits; deployment; frontend target; and cross-ARC module integration.

Task context identifies Sonjoy and Rafi as co-owners, Amran as reviewer, and Yousuf as technical direction/contract reviewer/project approver. Per-decision authority must follow project process; no additional authority is assigned here.

## 18. Implementation Readiness Gates

Do not implement until the target and first use case are confirmed; an authoritative contract owner/location is identified; architecture and framework decisions are recorded; scientific mappings and security/operational constraints are reviewed; and test/acceptance criteria are agreed. If simulation/optimization is in scope, first establish branch integration and domain approval.

## 19. Final Recommendation

Prepare an implementation proposal only after product owners choose the first slice and contract authority. A modular monolith is the simplest architecture candidate for evaluation. No framework is selected, no production backend exists on the refreshed ARC-10 branch, and this proposal does not authorize implementation.
