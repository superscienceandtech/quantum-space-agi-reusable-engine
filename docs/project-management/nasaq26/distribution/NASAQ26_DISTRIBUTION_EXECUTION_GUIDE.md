# NASAQ_26 Distribution Execution Guide

**Status:** Preparation guide only. No message has been sent; no assignment status has been changed.

## Draft messages and member-specific attachments

Prepare separate communications using only the matching work order and that member’s six acceptance-matrix rows:

| Recipient | Copy-ready draft | Work order attachment | Matrix rows |
|---|---|---|---|
| Amran | [Amran distribution draft](NASAQ26_AMRAN_DISTRIBUTION_MESSAGE.md) | [ARC-04/05 Work Order v2](NASAQ26_AMRAN_ARC04_ARC05_WORK_ORDER_v2.md) | A1–A6 only |
| Hridi | [Hridi distribution draft](NASAQ26_HRIDI_DISTRIBUTION_MESSAGE.md) | [ARC-09 Work Order v2](NASAQ26_HRIDI_ARC09_WORK_ORDER_v2.md) | H1–H6 only |
| Rafi | [Rafi distribution draft](NASAQ26_RAFI_DISTRIBUTION_MESSAGE.md) | [ARC-10 Work Order v2](NASAQ26_RAFI_ARC10_WORK_ORDER_v2.md) | R1–R6 only |

Do not include the complete cross-member matrix in any one member’s message. The shared matrix remains the project tracking record; send only the recipient’s relevant rows. The copy-ready draft and work order are separate documents; attach the work order and include/paste only their six assigned rows.

## Required distinctions

Use these states as separate events; one does not imply the next:

1. **Work Order receipt:** the member confirms they received the request. This is not acceptance of the assignment.
2. **Assignment acceptance:** the member explicitly accepts or declines the stated scope/responsibilities and identifies constraints. Do not infer acceptance from receipt or silence.
3. **Work commencement:** the member states that work has begun or gives a start date. Assignment acceptance does not prove work began.
4. **Deliverable submission:** the member supplies the requested evidence package with paths/links, source revisions, dates, and outcomes. A submission is not yet verified or accepted.
5. **Project Owner acceptance:** Yousuf reviews the submission against its acceptance criteria and records acceptance, changes requested, or a blocker. Submission or technical review by another member is not Project Owner acceptance.

## Status recording

Before sending, all matrix rows remain `PROPOSED / NOT_SENT / NOT_RECEIVED / NOT_STARTED / NOT_STARTED / NOT_REVIEWED` across assignment, dispatch, acknowledgement, deliverable, verification and acceptance fields.

After an event, update only the supported field and add a date/evidence reference. Preserve the other fields. A sent message requires dispatch evidence; acknowledgement requires the member’s actual response; deliverable status requires receipt; verification requires review notes; acceptance requires Yousuf’s explicit decision. Never record an approval in a status field merely because the member accepted the assignment.

## Governance and preservation

- **ARC-08:** Real NASA-data research remains blocked until required approvals and evidence are in place. No data access, restricted archive access, notebook execution, experiment, or frozen-evidence change is authorized by these messages.
- **ARC-10:** Planning/register recovery may proceed. Production implementation remains blocked pending required D-01..D-16 decisions and explicit authorized implementation approval. Architecture, security, data-rights/scientific and release authorities remain with their proper decision-makers.
- **ARC-09:** Synthetic prototype data remains explicitly separate from NASA research and production data. Production integration is not authorized by a handover or assignment acceptance.
- **ARC-03:** Preserve `src/quantum_space_agi/data/__init__.py`, `src/quantum_space_agi/data/loader.py`, and `tests/test_data_loader.py` as existing modified files. Do not restore, overwrite, stage, or commit them.
- No message is sent by this preparation. All drafts remain `NOT_SENT`; acknowledgements remain `NOT_RECEIVED`.
