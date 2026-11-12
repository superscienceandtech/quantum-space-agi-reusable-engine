# Work Order Draft v2 — Rafi — ARC-10 Register Recovery and API Readiness

**Dispatch state:** SENT.  
**Assignment state:** PROPOSED; acknowledgement not recorded.  
**Responsible scope:** ARC-10 backend/API coordination, register recovery, contract documentation, and authorized evidence collection, as proposed in the Project Owner responsibility model.  
**Purpose:** Recover and reconcile existing records, map dependencies and report readiness. This work order does not authorize API implementation or ARC-08 scientific work.

## Deliverables

1. **Canonical ARC-10 Decision & Approval Register:** search available authorized repositories and document locations independently of whether decision-makers are known. Report exact canonical title/path/URL, revision/branch/commit, owner if known, date checked, and why it is authoritative. Reconcile D-01 through D-16 individually with the owner topic list and local `NASAQ26_APPROVAL_DEPENDENCY_REGISTER.csv`; include recorded status, evidence, proposer, actual decision-maker if evidenced, conditions, review feedback, and decision reference. If no canonical register is located, report `NOT LOCATED` with sources searched and preserve the local tracker as a working mirror only. Do not upgrade any status without explicit authorized decision evidence.
2. **Four previously prepared planning reports:** locate and identify each by exact title, canonical path/URL, revision/date, author/owner if known, and recorded status. State whether draft, sent, reviewed, or approved only where evidence supports it. Provide originals/links and map their relevance to D-01..D-16. Search and report this independently of decision-maker identification. If reports are absent, say `NOT LOCATED` with search scope; do not create replacements or relabel ARC-08/09 material as ARC-10 reports.
3. **Current backend repository/branch:** identify canonical production backend URL, owner if evidenced, active checkout path, branch, HEAD/base, date/time/timezone checked, and designation evidence. Separate active checkout from local remote-tracking refs; if production designation or current state is unknown, say so.
4. **API contract ownership:** identify the proposed contract author, canonical document/source and version, consumer/reviewer roles, actual approval owner, and evidence for each. Drafting responsibility does not establish authority to approve.
5. **First-use-case requirements and endpoint proposal:** first establish whether an approved first use case exists and cite its decision record. If none is evidenced, return `NOT IDENTIFIED / BLOCKED` and list the use-case decision needed; do not propose concrete endpoint paths, methods, DTOs, or schemas. If a use case is approved, document requirements and clearly label all unapproved endpoint details as proposals: purpose, data/provenance, identifiers, types/nullability, errors, versioning, empty/success/failure behavior, and acceptance examples.
6. **Framework/runtime dependency analysis:** record any existing candidate framework/runtime evidence, source/revision, D-05 dependency, compatibility/security constraints and actual decision-maker if known. Mark unresolved choices `PROPOSED` or `UNCONFIRMED`.
7. **Architecture/security decision-maker map:** list actual named persons/roles and authority evidence where available for repositories, framework, contract, scientific semantics/provenance, authN/authZ, CORS/secrets/environment, resource limits, persistence/background work, testing, implementation authorization and release. Unknown decision-makers remain `UNIDENTIFIED`; describe a routing need without assigning authority by role assumption.
8. **API implementation readiness report:** return `READY_FOR_AUTHORIZED_IMPLEMENTATION`, `NOT_READY`, or `BLOCKED_EXTERNAL_DECISION`, with evidence by D-topic, unresolved dependencies, security review, acceptance/testing needs and the exact authorization still required. Missing decisions keep readiness blocked. A readiness recommendation is not itself authorization.

## Acceptance criteria

- Register/report discovery is completed or explicitly recorded as `NOT LOCATED`, regardless of missing decision-maker identities.
- D-01..D-16 are accounted for individually; current statuses are preserved absent authorized approval evidence.
- The four reports are identified from authoritative sources or not-found scope is recorded; unrelated documents are not reclassified.
- Repository/branch, contract ownership and framework choices are evidenced or marked unknown/proposed.
- Concrete endpoint proposals are withheld if no approved first use case is evidenced; any proposal remains clearly unapproved.
- Contract author, reviewers and approval authorities are distinct; authority is evidenced rather than inferred.
- API production implementation remains blocked until required decisions and explicit implementation authorization are recorded. Release remains a separate gate.

## Independence, ARC-08, and evidence boundaries

Register/report recovery, repository identification, and authority mapping are separate deliverables. Unknown authority does not prevent Rafi from locating records; record the gap for routing.

ARC-08 evidence coordination does not authorize NASA data acquisition/reuse, restricted archive access, notebook execution, experiments, or modifications to frozen ARC-08.4/08.5/08.6 evidence. Those gates remain unchanged and real-data research remains blocked until required approvals/evidence are in place. No approval or decision may be inferred from a proposal, draft, role, or conversation.

The local project snapshot previously showed no ARC-10 register/four reports and an initial-commit `origin/arc/10-api-integration` ref; these are stale-capable local observations, not a current remote check. The ARC-09 contract request is not an ARC-10 register or approved API contract. Recheck authorized sources and report the exact evidence found.

**Prohibited in this order:** no stage/commit/push, API production implementation, deployment, NASA data acquisition, archive access, notebook execution, or experiments.
