# ARC-10 Project Owner Decision Matrix

## Current status

Status: B — PARTIALLY VERIFIED

The Mission API is implemented, tested, and reproducible as a local synthetic educational demo. The controlling missing fact is formal Project Owner approval for the production-facing contract and authority model.

## Decision table

| Decision required | Technical evidence | Risk if unapproved | Recommended option | Authority | Consequence |
|---|---|---|---|---|---|
| Confirm canonical source repository/branch | `develop` at `6a44af3` is the verified worktree; `origin/develop` is not the authoritative implementation source | Wrong branch or wrong repo may be treated as official | Record the worktree as the operational verification source, but not as production authority | Project Owner / maintainers | Avoids false claims of canonical deployment |
| Name the contract owner and canonical contract path | Route definitions and DTOs exist in source; no formal owner or canonical document was found | Contract cannot become binding | Assign a single owner and path; keep current doc set as draft input | Project Owner | Creates a controllable contract lifecycle |
| Decide whether ARC-10 v0.3/v0.4 exist or are superseded | Only v0.1/v0.2 were found; v0.3/v0.4 are absent | Inability to compare versions or determine controlling baseline | Demand the missing versions or designate a different approved baseline | Project Owner / document owner | Prevents drift and stale-version decisions |
| Separate Mission API from Dataset Validation API | `docs/NASAQ26_LOCAL_EDUCATIONAL_DEMO.md:46-59` and source layout clearly separate responsibilities | Inferred scientific validation or dataset acceptance could be mistaken for mission readiness | Explicitly maintain separation and do not infer `scientific_eligibility` from mission validation | Project Owner + domain owners | Preserves scientific boundary integrity |
| Decide whether collision metadata is public API contract or internal detail | ARC-05 returns both values; external mission result omits them | Field-loss at contract boundary may mislead downstream consumers | Explicitly decide to expose or omit these fields and document the rationale | Contract owner + ARC-05 reviewer | Eliminates hidden data-loss boundary |
| Decide whether GET on POST-only routes is 404 or 405 | Current code and tests show 404 for `GET /api/v1/missions/run` | Clients may mis-handle method mismatch | Standardize the behavior and add a test | Contract owner | Improves API contract clarity |
| Approve or block security and deployment boundaries | Local loopback launch only; no auth, secrets, or operational model | Unapproved service would be mistaken for production | Keep the current state as a local demo pending approval | Security, platform, and Project Owner authorities | Preserves safe operational boundary |

## Technical recommendation

The recommended technical position is:

- Keep the current local implementation as a verified educational demo.
- Do not present it as a production Mission API.
- Treat all route and DTO behavior as draft until the contract owner and approval chain are formally defined.
- Maintain Dataset Validation as a separate workstream.
- Keep scientific suitability and `scientific_eligibility` explicitly unassessed unless a separate domain review approves them.

## Formal approval recommendation

Formal approval should not be inferred from passing local tests or successful synthetic execution. Approval remains a separate governance action.

Recommended status for the current package: B — PARTIALLY VERIFIED, not yet approved for production or deployment.

## Consequence of approval or rejection

If approved as a local demo only:
- the evidence package can be used for controlled internal review,
- but it remains explicitly separate from production deployment or scientific approval.

If rejected or delayed:
- the implementation stays in a read-only verification state,
- and no production contract or deployment claim may be made.
