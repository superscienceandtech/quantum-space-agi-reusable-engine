# ARC-10 Review Submission Workflow

Status: `REVIEW SUBMISSION WORKFLOW READY — ALL REVIEWS PENDING — PRODUCTION NOT APPROVED`
Baseline: `LOCAL_SYNTHETIC_DEMO_BASELINE — NOT PRODUCTION APPROVED`

This workflow defines how to request, receive, and record the five independent reviews. It does not assign reviewers, represent that requests were sent, or authorize implementation or deployment.

## 1. Select an authorized reviewer

1. Identify a person through the project's established governance channels; do not infer authority from availability or job title alone.
2. Verify that the person is authorized for the applicable review domain:
   - Security: designated security authority.
   - Privacy: designated privacy authority.
   - Scientific/domain: reviewer with relevant domain authority.
   - Deployment/operations: designated platform or operations authority.
   - Acceptance/QA: designated QA or acceptance authority.
3. Record the reviewer's name, stated authority, and verification evidence only after confirmation. Until then, keep reviewer identity and authority unassigned/unverified.
4. Avoid assigning the same person to multiple independent approval roles unless governance explicitly permits it and independence is documented.

## 2. Prepare and submit the review request

1. Use the matching message in `docs/ARC10_INDEPENDENT_REVIEW_REQUEST_MESSAGES.md`.
2. Attach or provide access to only the corresponding review package and the relevant evidence references listed in it.
3. Include the matching response template. Do not edit the template to prefill a reviewer, decision, finding, or approval.
4. Identify the review as a request, not a completed audit or approval.
5. State the boundary: the reviewed baseline is local and synthetic; production is not approved. Project Owner final contract approval remains separate.
6. After a request is actually sent, record the date, channel/reference, and sender in the coordination and intake registers. Do not record a sent request before it occurs.

## 3. Request written feedback

Ask the reviewer to return the completed matching response template through an approved project channel. The response should include reviewer identity and authority, date, scope, evidence examined, findings and severity, unresolved risks, corrective actions, a single explicit decision, conditions/limitations, and reviewer confirmation.

Do not treat verbal discussion, silence, or an incomplete template as approval. If follow-up discussion occurs, ask the reviewer to confirm material conclusions in writing.

## 4. Receive and preserve the response

1. Preserve the response as received; do not alter reviewer wording, findings, decision, dates, or conditions.
2. Record a stable evidence reference (repository path, approved document reference, or controlled record identifier) and receipt date.
3. Verify that the response identifies the reviewer and provides sufficient evidence of their authority. Record authority as unverified until this check is complete.
4. If the response is incomplete, ambiguous, unsigned where confirmation is required, or lacks evidence references, record `INSUFFICIENT EVIDENCE` or keep the review `PENDING` as appropriate; request clarification without editing the original response.
5. Update the coordination register only from authentic received evidence. Preserve prior entries and maintain an audit trail for changes.

## 5. Record evidence references

For each review, record:

- the review package version/path and baseline reviewed
- the completed response template or controlled response location
- supporting evidence references supplied or examined by the reviewer
- receipt date and the verified reviewer authority
- decision, findings, conditions, and outstanding actions

Do not claim evidence was examined unless the reviewer or coordinator can identify it. Keep Mission Planning & Simulation API evidence separate from Dataset Validation API evidence.

## 6. Handle conditional approvals

Record `APPROVED WITH CONDITIONS` only when explicitly selected in an authentic written response from a reviewer whose authority is verified. Copy every condition, limitation, expiry, and required action exactly or faithfully without weakening it.

Track each condition with an owner role, due/closure evidence, and status. A conditional approval is not unconditional approval. Do not mark the review fully closed until all required conditions are independently evidenced as satisfied and the reviewer or approval authority confirms closure where required.

## 7. Handle rejected or incomplete reviews

- `REJECTED`: retain the decision and findings; keep the corresponding gate unresolved. Route corrective actions through the applicable governance process. Do not override or reinterpret the rejection.
- `INSUFFICIENT EVIDENCE`: record what is missing and request the specific evidence or clarification. The gate remains unresolved.
- No response or no valid decision: keep status `PENDING`.
- Conflicting or ambiguous responses: preserve each response, record the conflict, and seek resolution from the authorized approval authority; do not select a favorable interpretation.

## 8. Escalate critical findings

When a reviewer reports a critical finding:

1. Preserve the finding and its evidence reference.
2. Mark the relevant review and dependent production gates unresolved/blocked according to the decision rules.
3. Notify the Project Owner and the relevant authority through established project channels; record the notification only after it is sent.
4. Do not proceed with implementation, external integration, production exposure, or deployment on the basis of an unresolved critical finding.
5. Require documented corrective evidence and the appropriate reviewer/authority disposition before changing the status.

## 9. Governance boundary and next action

All five reviews remain pending until authentic responses are received and reviewer authorities verified. Project Owner final contract approval remains a separate gate. No review request or completed review authorizes production implementation or deployment.

Next action: the Project Owner or designated coordinator identifies authorized reviewers, sends the corresponding requests, and records each actual submission and response in the coordination registers.
