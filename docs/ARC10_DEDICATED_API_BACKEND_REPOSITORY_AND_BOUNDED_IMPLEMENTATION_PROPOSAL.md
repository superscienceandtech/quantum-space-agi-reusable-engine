
# ARC-10 — Dedicated API/Backend Repository and Bounded Implementation Proposal

**Prepared by:** Rafi
**Date:** 14 November 2026
**Status:** PROPOSAL FOR FORMAL AUTHORIZATION
**Implementation status:** NOT AUTHORIZED

## 1. Objective

Establish a technically isolated API/backend repository that consumes the reusable `quantum-space-agi-engine` package without modifying the protected ARC-08 workstream.

The proposed first operation is:

`POST /api/v1/dataset-validations`

The initial scope is limited to synthetic-data-only, non-production validation integration.

This proposal does not authorize repository creation, implementation, ARC-08 modification, production data access, deployment, or production exposure.

## 2. Proposed Repository Structure

Proposed repository name:

`quantum-space-agi-api`

Proposed structure:

```text
quantum-space-agi-api/
├── pyproject.toml
├── README.md
├── src/
│   └── quantum_space_agi_api/
│       ├── __init__.py
│       ├── main.py
│       ├── config.py
│       ├── api/
│       │   └── v1/
│       │       ├── router.py
│       │       └── endpoints/
│       │           └── dataset_validations.py
│       ├── schemas/
│       │   ├── requests.py
│       │   └── responses.py
│       ├── services/
│       │   └── dataset_validation_service.py
│       ├── adapters/
│       │   └── engine_validation_adapter.py
│       └── errors/
│           └── handlers.py
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── contract/
│   └── fixtures/
│       └── synthetic/
└── docs/
    ├── architecture/
    ├── api/
    └── testing/
```

This is a proposed layout only. Final package naming, permitted paths, and repository conventions must be confirmed by the repository owner.

## 3. Proposed Branch Strategy

- `main`: protected integration branch.
- `feature/arc10-dataset-validation`: isolated feature-development branch, if approved.
- Pull requests should be used to merge changes into `main`.
- Required checks should include automated tests, linting, type checking, and dependency/security checks as agreed by the repository owner.
- No direct changes to protected branches.
- No branch creation before repository authorization.

The repository owner must confirm branch protection and review requirements.

## 4. Package Integration Design

The API should consume the reusable engine as a separately versioned Python package.

Proposed integration principles:

1. Do not copy ARC-08 source files into the API repository.
2. Do not modify ARC-08 to add HTTP or FastAPI responsibilities.
3. Keep transport DTOs separate from engine domain models.
4. Use an adapter/service boundary to invoke the selected existing domain validator.
5. Preserve the engine's validation semantics and report information.
6. Pin the engine dependency to an explicitly approved version or immutable source revision.
7. Avoid importing from an arbitrary local filesystem path in the implementation or tests.

The actual distributable package name, package publishing method, versioning policy, and dependency source remain unresolved and require confirmation.

## 5. Proposed API Implementation Boundary

The initial bounded operation is:

`POST /api/v1/dataset-validations`

Proposed request flow:

1. Receive and parse the API request.
2. Validate transport-level structure.
3. Resolve a schema from a static, read-only schema lookup abstraction.
4. Adapt the request into the appropriate engine domain representation.
5. Invoke exactly one selected ARC-08 schema-validation capability.
6. Map the domain report into an API response DTO.
7. Return the approved HTTP response or error representation.

Initial exclusions:

- Quality analysis unless separately selected and approved.
- Scientific eligibility or scientific correctness claims.
- NASA data authenticity verification.
- Persistence or database integration.
- External API calls.
- Background processing.
- Arbitrary caller-defined schemas.
- Production authentication or authorization.
- Public network exposure.

Exact wire fields, schema identities, unsupported-schema status, and final error envelope remain subject to contract review and approval.

## 6. Synthetic Test-Data Strategy

All initial tests must use synthetic fixtures created specifically for testing.

Test categories:

- Valid synthetic records.
- Missing required fields.
- Incorrect Python data types.
- Nullability violations.
- Unknown fields.
- Empty record collections.
- Unsupported synthetic schema identifiers.
- Provenance declaration mapping.
- Domain validation report mapping.
- Malformed request bodies.
- HTTP status and error-envelope behavior.

Test data must not contain NASA datasets, restricted data, personal information, credentials, or externally sourced scientific records.

Synthetic schema entries must remain test-only until actual schema identities, definitions, owners, and review authority are approved.

## 7. Security and Dependency Considerations

### Security boundaries

- No public deployment or production exposure.
- No unapproved authentication or authorization design.
- No production secrets or credentials.
- No persistence of submitted records.
- Avoid logging submitted record contents.
- No production CORS configuration.
- No claims of production security readiness.

The application should remain restricted to an isolated local or approved non-production test environment.

### Dependencies

Proposed runtime direction:

- Python
- FastAPI
- Uvicorn
- Pydantic, subject to exact-type and serialization compatibility testing
- The reusable engine package as an explicitly versioned dependency

Development/test dependencies should be separately declared.

Before selecting versions, verify the target repository's Python compatibility, dependency policy, vulnerability-check requirements, and package distribution method.

No dependency installation is authorized by this proposal.

## 8. Repository Ownership and Permitted Scope

The following remain unresolved:

- Repository owner and maintainer.
- Repository creation authority.
- Canonical remote location.
- Initial branch and branch protection.
- Permitted source, test, and documentation paths.
- Engine package publisher and dependency source.
- Dependency approval authority.
- Required reviewers and CI checks.

These must be recorded before repository creation or repository-specific implementation.

## 9. Required Approvals

| Decision | Required confirmation |
|---|---|
| Dedicated repository creation or existing target selection | Authorized project/repository authority |
| Repository owner and maintainers | Project/repository authority |
| Branch and permitted paths | Repository owner |
| Engine package distribution and version policy | Engine owner/repository authority |
| Synthetic-only non-production implementation | Explicit implementation authorization |
| Actual schema identities and definitions | Designated schema owner/reviewer |
| Final API contract | Identified contract approval authority |
| Security and production operations | Relevant security/platform authority |
| Production deployment and release | Formal production release authority |

## 10. Proposed Authorization Boundary

If approved, the initial implementation authorization should be limited to:

- Creating or using the formally designated API repository.
- Implementing the single dataset-validation operation.
- Using synthetic test fixtures only.
- Consuming an approved engine package version.
- Running isolated non-production tests.
- Updating implementation and test documentation.

It must exclude ARC-08 modification, NASA data access, production credentials, production deployment, public exposure, and unapproved security or data-rights decisions.

## 11. Outstanding Decisions

1. Repository creation or target designation.
2. Repository ownership and maintainers.
3. Target branch and permitted paths.
4. Engine package identity, publishing mechanism, and version policy.
5. Synthetic-only implementation authorization.
6. Schema catalog approval process.
7. Final API Contract approval authority and canonical location.
8. Security and operational approval responsibilities.

## 12. Current Readiness

**Repository creation:** NOT AUTHORIZED
**ARC-08 modification:** NOT AUTHORIZED
**Repository-specific implementation:** NOT AUTHORIZED
**Synthetic non-production implementation:** PENDING FORMAL AUTHORIZATION
**Production implementation:** BLOCKED
**Production deployment:** BLOCKED

This document is a technical proposal submitted for review and a formal authorization decision. It does not constitute approval or implementation authorization.
