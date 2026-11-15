# ARC-10 Approval Layer Matrix

Repository: `/mnt/e/nasa26/nasaq26-develop-worktree`
Branch: `develop`
Full HEAD: `6a44af34a649a1138cf577b3b16dbaf436c8a203`
Current status: `FORMAL REVIEW PREPARATION COMPLETE — PRODUCTION NOT APPROVED`
Baseline: `LOCAL_SYNTHETIC_DEMO_BASELINE — NOT PRODUCTION APPROVED`

This matrix separates review preparation from approval. No layer below implies another approval layer. Each layer is treated as independent.

## 1. Approval layers

| Layer | Purpose | Required evidence | Responsible role | Current status | What it does NOT authorize |
|---|---|---|---|---|---|
| 1. Technical evidence verification | verify the local demo implementation and evidence trail | source files, tests, and review docs | technical reviewers / architecture owner | PARTIALLY VERIFIED | production approval or implementation authority |
| 2. Contract drafting / reconstruction | assemble a draft contract from actual evidence and document missing artifacts | source + review records + reconstruction proposal | contract owner | PARTIALLY VERIFIED | canonical contract approval or deployment |
| 3. Security approval | validate access, trust boundaries, and risk controls | security review package and findings | Security authority | PENDING | production deployment or public API approval |
| 4. Privacy / data-retention approval | review retention, exposure, and handling policies | privacy review and retention policy | Privacy authority | PENDING | data handling or deployment approval |
| 5. Scientific / domain approval | review scientific integrity, mission semantics, and domain classification | domain review record and acceptance notes | Scientific/domain reviewers | PENDING | scientific claim or production readiness |
| 6. Deployment / operations approval | review runtime environment, runbooks, rollback and operations governance | deployment review, runbook, ops evidence | Platform/operations authority | PENDING | production deployment or release |
| 7. Acceptance / QA approval | review evidence and readiness for release or contract adoption | QA evidence and acceptance report | QA owner / acceptance authority | PARTIALLY VERIFIED | production launch or contract approval |
| 8. Project Owner final contract approval | decide contract authority and formal contract baseline | approved review package and governance decisions | Project Owner | PENDING FOR PRODUCTION BASELINE | implementation, integration, or deployment |
| 9. Implementation authorization | authorize source changes beyond the current review package | project statement and formal approval record | Project Owner | NOT AUTHORIZED | production contract approval or deployment |
| 10. Deployment authorization | authorize runtime rollout or operational release | full security, privacy, deployment, and acceptance approvals | Project Owner + operations authority | NOT AUTHORIZED | review preparation or draft-only work |

## 2. Layer-specific notes

### 1. Technical evidence verification
This layer confirms source and evidence integrity. It supports the current review package only and does not grant any production reserve or approval authority.

### 2. Contract drafting / reconstruction
Draft reconstruction is allowed as proposal-only work under D-03. It must remain labeled `DRAFT — RECONSTRUCTED FROM AVAILABLE EVIDENCE` and must preserve uncertainty and missing information.

### 3. Security approval
Security approval is independent of technical evidence. Approval is required before any production exposure or public API claim can be considered.

### 4. Privacy / data-retention approval
Privacy review is independent of technical evidence. It does not authorize contract adoption or deployment.

### 5. Scientific / domain approval
Scientific approval is independent of technical verification. Synthetic execution must remain clearly labeled as synthetic and not scientific validation.

### 6. Deployment / operations approval
Operations approval is independent of contract maturity and must be granted before any operational rollout or public exposure.

### 7. Acceptance / QA approval
Acceptance review confirms evidence quality but does not itself authorize deployment or production readiness.

### 8. Project Owner final contract approval
This is the final governance gate for a formal contract baseline. It does not authorize implementation or deployment by itself.

### 9. Implementation authorization
Implementation authorization is a separate governance action and is explicitly not granted by this review-preparation package.

### 10. Deployment authorization
Deployment authorization is the last and most restrictive gate. It requires all preceding approvals and remains explicitly not authorized here.

## 3. Decision boundary

The review package keeps the current work in the following state:

`FORMAL REVIEW PREPARATION COMPLETE — PRODUCTION NOT APPROVED`
