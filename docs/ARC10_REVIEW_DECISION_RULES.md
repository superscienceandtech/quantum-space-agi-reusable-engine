# ARC-10 Review Decision Rules

Status: `REVIEW SUBMISSION WORKFLOW READY — ALL REVIEWS PENDING — PRODUCTION NOT APPROVED`

These rules govern recording independent review outcomes. They do not grant any approval or production authority.

## Decision definitions

| Decision | Definition | Review state |
|---|---|---|
| `APPROVED` | An authorized reviewer explicitly approves the defined review scope in an authentic written response, with sufficient evidence and no outstanding conditions. | May be recorded only after response and authority verification; does not approve any other layer. |
| `APPROVED WITH CONDITIONS` | An authorized reviewer explicitly approves the scope subject to stated conditions or limitations. | Record all conditions verbatim or faithfully; unresolved until required conditions are evidenced as closed and the required authority confirms closure. |
| `REJECTED` | An authorized reviewer explicitly rejects the reviewed scope or identifies reasons it is not acceptable. | Remains unresolved; preserve findings and require disposition through the proper review process. |
| `INSUFFICIENT EVIDENCE` | The reviewer cannot reach a decision because evidence, scope, or verification is inadequate. | Remains unresolved; request the missing evidence or clarification. |
| `PENDING` | No valid, complete written decision has been received, or reviewer authority is not verified. | Default state; no approval may be inferred. |

## Authenticity and authority requirements

A review cannot be marked `APPROVED` or `APPROVED WITH CONDITIONS` unless all are true:

1. A written response is received and preserved.
2. The response identifies the reviewer and review date.
3. The reviewer's authority for that review area is verified and recorded.
4. The scope and evidence examined are stated clearly enough to interpret the decision.
5. The reviewer explicitly selects one of the defined decisions.
6. Any conditions and limitations are captured without weakening them.

If any requirement is missing, keep the review `PENDING` or record `INSUFFICIENT EVIDENCE`; do not infer approval.

## Conditions, rejection, and incomplete evidence

- Conditional approval remains conditional until all required conditions have evidence of closure and any required reviewer confirmation is recorded.
- Rejection remains unresolved. Do not downgrade its severity or treat corrective work as acceptance without the authorized reviewer's disposition.
- Insufficient evidence remains unresolved until the evidence gap is addressed and a valid decision is received.
- Conflicting decisions must be preserved and escalated to the applicable approval authority; do not choose one silently.
- A critical finding blocks the relevant gate and must be escalated before any dependent work proceeds.

## Separation of approvals

Each independent review is separate from the others. Technical evidence verification, contract drafting, security, privacy, scientific/domain, deployment/operations, acceptance/QA, Project Owner final contract approval, implementation authorization, and deployment authorization do not imply one another.

Project Owner final contract approval remains separate from the five independent reviews. No review decision by itself authorizes production implementation, external integration, or deployment.

## Current state

All five independent reviews remain `PENDING`. Production remains `NOT APPROVED`.
