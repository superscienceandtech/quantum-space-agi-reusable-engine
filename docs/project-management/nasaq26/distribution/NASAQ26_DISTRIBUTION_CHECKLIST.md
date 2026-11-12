# NASAQ_26 Distribution Checklist — Work Order v2

**Purpose:** Pre-send and evidence-control checklist for the draft work orders. This document does not send a message or assert assignment, dispatch, acknowledgement, or approval.

## Before distribution

- [ ] Yousuf confirms intended recipients and that the proposed scope matches each member’s authorized assignment.
- [ ] Verify each recipient and approved communication channel; do not include restricted evidence in an unapproved channel.
- [ ] Confirm the linked work-order and matrix revisions are the v2 files and preserve the prior originals.
- [ ] Tell recipients the assignment remains proposed until acknowledged; no acknowledgement has been recorded by this package.
- [ ] Communicate that work orders request existing evidence. Missing checks are reported as `NOT RUN` / `NOT AVAILABLE`; they are not silently performed to make a report appear complete.
- [ ] Ensure work orders do not authorize actions outside confirmed scope or external approval authority.

## Assignment-specific checks

### Amran — ARC-04/05

- [ ] Request separate ARC-04 and ARC-05 evidence packages.
- [ ] Require exact repository, branch/base, changed-file list, diff, existing test/notebook logs, environment, manifest, PR evidence and blockers.
- [ ] Keep ARC-04 and ARC-05 results separate; no test success inferred without logs.
- [ ] Preserve the three protected ARC-03 modified paths; no staging, cleanup, or overwrite.
- [ ] Restricted/real-data notebook execution remains subject to applicable authorization.

### Hridi — ARC-09

- [ ] Request prototype handover and verification evidence independently of production contract approval.
- [ ] Assign explicit four-versus-six visualization reconciliation; local snapshot documents four, not six.
- [ ] Require per-check accessibility outcomes and distinguish source, browser, and assistive-technology evidence.
- [ ] Keep synthetic examples separate from NASA research and production data.
- [ ] Production integration remains gated on confirmed repo/use case/contract/framework/security/architecture and release decisions.

### Rafi — ARC-10

- [ ] Register and four-report discovery can proceed independently of decision-maker identification.
- [ ] Require exact source/revision and `NOT LOCATED` search scope when records cannot be found.
- [ ] Keep D-01..D-16 pending absent decision evidence from authorized owners.
- [ ] Without an approved first use case, require only a missing-decision map; no concrete endpoint/schema proposal.
- [ ] Keep architecture, security, data-rights/scientific, implementation authorization, and release approvals distinct.
- [ ] ARC-08 evidence coordination does not authorize data acquisition/reuse, archive access, notebook execution, experimentation, or frozen evidence changes.

## Status recording after routing

The acceptance matrix uses separate columns. Update only the field supported by evidence:

| Field | Initial value | Evidence for changing it |
|---|---|---|
| Assignment status | `PROPOSED` | Owner’s recorded assignment decision |
| Dispatch status | `NOT_SENT` | Preserved sent message/dispatch metadata |
| Acknowledgement status | `NOT_RECEIVED` | Member’s explicit response linked to record |
| Deliverable status | `NOT_STARTED` | Receipt of the identified deliverable |
| Verification status | `NOT_STARTED` | Reviewer’s documented evidence check/result |
| Acceptance status | `NOT_REVIEWED` | Explicit acceptance decision and reviewer record |

An acknowledgement is not approval. Dispatch is not acknowledgement. Receipt is not verification. Verification is not acceptance or external authorization.

## Governance invariants

- ARC-08 real-data research stays blocked until all required approvals and evidence are verified.
- ARC-10 production implementation stays blocked until required decisions and explicit implementation authorization are recorded.
- No external authority, team acknowledgement, architecture/security/data-rights decision, or release approval is inferred.
- Synthetic data remains separate from NASA scientific data.
- No source/scientific evidence is changed by distributing these requests.
- The protected ARC-03 modifications remain untouched.
EOF
print('Created six new v2 work-order and distribution documents; originals preserved.')
