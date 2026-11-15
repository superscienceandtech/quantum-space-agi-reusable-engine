# ARC-10 Independent Review Request Messages

These are copy-ready request drafts. They have not been sent. Add recipient details only after the appropriate reviewer authority is identified.

## 1. Security review request

**Subject:** Request for independent ARC-10 security review

Please review the ARC-10 security review package at `docs/ARC10_SECURITY_REVIEW_PACKAGE.md` and complete `docs/ARC10_SECURITY_REVIEW_RESPONSE_TEMPLATE.md`. The review should assess the evidence and gaps for authentication/authorization, input validation, error disclosure, secrets/configuration, logging/audit, dependencies, and network/deployment assumptions. This is a request for review; no security audit or approval is represented as completed. The current baseline is a local synthetic demo and is not production approved.

## 2. Privacy review request

**Subject:** Request for independent ARC-10 privacy review

Please review `docs/ARC10_PRIVACY_REVIEW_PACKAGE.md` and complete `docs/ARC10_PRIVACY_REVIEW_RESPONSE_TEMPLATE.md`. Please assess data processing, sensitive-data exposure, retention/deletion, logging/telemetry, sharing, NASA data provenance/reuse boundaries, and synthetic-versus-real separation. This is a request for review; no privacy approval or compliance claim is represented as completed. The current baseline is not production approved.

## 3. Scientific/domain review request

**Subject:** Request for independent ARC-10 scientific/domain review

Please review `docs/ARC10_SCIENTIFIC_DOMAIN_REVIEW_PACKAGE.md` and complete `docs/ARC10_SCIENTIFIC_REVIEW_RESPONSE_TEMPLATE.md`. Please assess simulation and resource-evaluation assumptions, feasibility criteria, collision metadata scope, scientific-validation requirements, data provenance, uncertainty, and the `scientific_eligibility` boundary. Structural validation must not imply scientific eligibility, and synthetic execution is not scientific validation. This is a request for review; no scientific or NASA-data validation approval is represented as completed.

## 4. Deployment/operations review request

**Subject:** Request for independent ARC-10 deployment/operations review

Please review `docs/ARC10_DEPLOYMENT_OPERATIONS_REVIEW_PACKAGE.md` and complete `docs/ARC10_DEPLOYMENT_REVIEW_RESPONSE_TEMPLATE.md`. Please assess local-versus-production architecture, environment configuration, hosting/network exposure, authentication/secrets, monitoring/logging, backup/recovery, availability/failure handling, ownership/rollback, and operational acceptance requirements. This is a request for review only; it does not authorize or imply deployment.

## 5. Acceptance/QA review request

**Subject:** Request for independent ARC-10 acceptance/QA review

Please review `docs/ARC10_ACCEPTANCE_QA_REVIEW_PACKAGE.md` and complete `docs/ARC10_QA_REVIEW_RESPONSE_TEMPLATE.md`. Please assess available test evidence, route/DTO behavior, mission execution, error handling, synthetic reproducibility, ARC-05/ARC-08 boundaries, ARC-09 compatibility, accessibility/usability evidence, and missing acceptance evidence. Record exact commands and results only when verified. This is a request for review; no QA acceptance is represented as completed.

## Shared boundary

All five requests concern independent reviews of the `LOCAL_SYNTHETIC_DEMO_BASELINE — NOT PRODUCTION APPROVED`. Project Owner final contract approval remains a separate decision. No implementation, external integration, or deployment is authorized by these requests.
