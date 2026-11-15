# ARC-10 Authoritative Source Discovery

**Verification snapshot:** 2026-11-15T07:38:04Z (2026-11-15 13:38 +06:00)
**Verification role:** Independent read-only discovery and verification
**Scope:** ARC-10 API Integration — authoritative repository and six-artifact discovery
**Permissions exercised:** read repositories, inspect history, run tests, run the documented local backend, create reports. **No commit, push, merge, reset, delete, or implementation change was made.**

## 1. Executive finding

The only complete Mission API implementation found in the accessible workspace is the **local educational mission demo** in:

- Path: `/mnt/e/nasa26/nasaq26-develop-worktree`
- Branch: `develop`
- HEAD: `6a44af34a649a1138cf577b3b16dbaf436c8a203`
- Upstream: `origin/develop` is at `19157592d389f7fbb41830379a38efc464680c94` (the repository's initial commit), so the implementation is **47 commits ahead of the cached remote-tracking branch** and is not represented by `origin/develop`.

That checkout is a suitable **read-only operational verification source** because it contains the complete source, tests, dashboard adapter, and documentation for the local demo. It is **not** evidence of a formally designated production API repository, branch, contract owner, or approval. The Mission API owner decision register records this exact issue as `MAPI-02 **OPEN / BLOCKED**`.

**Authority conclusion:** operational source identified; formal/production authority **NOT ESTABLISHED**.

## 2. Phase 1 — Environment discovery

### 2.1 Host and operating system

| Item | Observed value |
|---|---|
| Host | `DESKTOP-1CEQVS7` |
| Platform | WSL2, `6.18.33.2-microsoft-standard-WSL2`, `x86_64` |
| Distribution | Ubuntu 26.04.1 LTS (Resolute Raccoon) |
| Shell | Bash |
| Working directory | `/mnt/e/nasa26/nasaq26-develop-worktree` |
| Mounted drives | `c d e f g h wsl wslg` |
| Time zone | `+06:00` at verification time |

### 2.2 Tools

| Tool | Observed value |
|---|---|
| Python | 3.14.7 (`/home/yousuf/miniconda3/bin/python3`) |
| Node.js | v24.21.0 |
| npm | 11.19.0 |
| git | 2.53.0 |
| pytest | 9.1.1 |
| FastAPI | 0.141.1 |
| Uvicorn | 0.54.0 |
| Pydantic | 2.13.4 |
| NumPy | 2.5.3 |
| Google Chrome | `/usr/bin/google-chrome` (browser-backed ARC-09 tests ran, not skipped) |
| Fresh verification venv | `$HOME/.venvs/nasaq26-arc10-verify` (Python 3.14.7) |

### 2.3 Git worktrees

`git worktree list` from the shared git directory:

```text
/mnt/e/nasa26/quantum-space-agi-reusable-engine   8b8f21f [arc/03-data-engineering]
/mnt/e/nasa26/nasaq26-develop-worktree            6a44af3 [develop]
/mnt/e/nasa26/nasaq26-docs-worktree               874d3e8 [docs/arc09-arc10-governance-sync]
/mnt/e/nasa26/nasaq26-integration-worktree        d7ac272 [integration/nasaq26-branch-reconciliation]
/mnt/e/nasa26/nasaq26-local-mission-demo-worktree dd79bc2 [feat/nasaq26-local-mission-demo]
```

Remote: `https://github.com/superscienceandtech/quantum-space-agi-reusable-engine.git`

### 2.4 Candidate worktree state

| Candidate | Branch | HEAD | Git status summary |
|---|---|---|---|
| `nasaq26-develop-worktree` | `develop` | `6a44af3` | Ahead 47 of `origin/develop`; 4 modified (`arc09-ui-prototype/app.js`, `charts.js`, `mission-demo.js`, `styles.css`); 22 untracked docs/tests **before** the six reports in this verification set were added |
| `nasaq26-integration-worktree` | `integration/nasaq26-branch-reconciliation` | `d7ac272` | Ahead 41 of `origin/develop`; 5 untracked docs |
| `nasaq26-docs-worktree` | `docs/arc09-arc10-governance-sync` | `874d3e8` | In sync with its upstream; 2 modified and 10 untracked governance reports |
| `nasaq26-local-mission-demo-worktree` | `feat/nasaq26-local-mission-demo` | `dd79bc2` | 2 untracked directories (`src/quantum_space_agi/mission_demo/`, `tests/mission_demo/`) |
| `quantum-space-agi-reusable-engine` | `arc/03-data-engineering` | `8b8f21f` | In sync with its upstream; 3 modified ARC-03 files |

No implementation or existing file in any candidate worktree was changed by this verification. This verification only added new reports under `develop/docs/`.

## 3. Phase 2 — Source-of-truth matrix

### 3.1 Candidates and evidence

| # | Candidate | Branch / ref | HEAD | Relationship to `develop` | ARC-10 / mission files | Actual Mission API implementation? | Read-only verification suitable? | Authority finding |
|---:|---|---|---|---|---|---|---|---|
| 1 | Project Owner written designation | — | — | — | — | — | — | **NOT LOCATED.** No written owner statement designating a canonical repository/branch was found. `CONTRIBUTING.md:18-20` says to target `develop` for pull requests "until maintainers specify otherwise"; that is a contribution instruction, not a production API approval. |
| 2 | Develop worktree | `develop` | `6a44af3` | itself | Complete `src/quantum_space_agi/mission_demo/`, `tests/mission_demo/`, local demo doc, ARC-10 draft matrix/registers | **Yes — complete local demo** | **Yes** | Operational integration source; **not formally approved** for production API. |
| 3 | Integration worktree | `integration/nasaq26-branch-reconciliation` | `d7ac272` | **Ancestor** of `develop` | `api.py`, `dto.py`, `service.py`, `server.py`, `configuration.py`, API/service/dashboard tests; older dashboard views | **Yes — earlier local demo** | Yes | Superseded by `develop`; not the newest verified source. |
| 4 | Docs worktree | `docs/arc09-arc10-governance-sync` | `874d3e8` | **Not an ancestor** of `develop` (merge-base `de48b07`) | Governance reports only; no `src/quantum_space_agi/mission_demo/` | **No** | Yes, documentation only | Documentation evidence; not an implementation source. |
| 5 | Local mission-demo worktree | `feat/nasaq26-local-mission-demo` | `dd79bc2` | **Not an ancestor** of `develop`; merge-base `de48b07`; same commit as `origin/main` | Only untracked `configuration.py` and `test_configuration.py`; no API/server/DTO/service | **No — partial** | Not useful for six-artifact verification | Prototype fragment only. |
| 6 | Base repository worktree | `arc/03-data-engineering` | `8b8f21f` | Ancestor of `develop` | ARC-03 data package; **no** `mission_demo` | **No** | Not for ARC-10 | Base checkout; not the integration branch. |
| 7 | ARC-10 branch | `origin/arc/10-api-integration` | `61d8c52` | **Not an ancestor** of `develop`; merge-base `1915759` | 30 ARC-10 documents including v0.1/v0.2 contract, DTO, test plan | **No** | Yes, documentation only | Draft/non-canonical documentation; **no implementation**. |
| 8 | ARC-10 documentation v0.3 | — | — | — | — | — | — | **NOT FOUND.** |
| 9 | ARC-10 documentation v0.4 | — | — | — | — | — | — | **NOT FOUND.** |
| 10 | Loose files in `/mnt/e/nasa26` | Not a repository root | — | — | Work orders, registers, distribution reports | **No** | Yes, as governance evidence | Not a repository or implementation source. |

### 3.2 Commit-history evidence

Relevant commits on the line that became `develop`:

| Commit | Subject | What it establishes |
|---|---|---|
| `135505e` | `feat: include educational ARC-08 mission evaluation` | Adds `mission_demo/service.py` and service tests. |
| `1a48247` | `feat: expose versioned local mission API` | Adds `api.py`, `dto.py`, `server.py`, API/server tests, optional API dependencies. |
| `5f96269` | `feat: connect mission dashboard to local API` | Adds `mission-demo.js`, form HTML/CSS, dashboard tests. |
| `e221fd8` | `docs: describe local mission API and startup` | Adds/updates `NASAQ26_LOCAL_EDUCATIONAL_DEMO.md`. |
| `d7ac272` | `fix: include local mission demo package` | Adds `mission_demo/__init__.py` and `configuration.py`; tip of integration branch. |
| `2b9d529` | `merge: integrate local mission dashboard` | Brings the local demo into the develop line. |
| `c21b35e`, `beaace3` | Dashboard view and result rendering | Adds ARC-09 mission-builder ownership and multi-view result rendering on `develop`. |
| `6a44af3` | `docs: support isolated WSL development environments` | Adds WSL/fresh-venv setup guidance; current `develop` HEAD. |

`origin/arc/10-api-integration` contains only documentation commits (`69c8e71`, `61d8c52`) on top of the initial commit. It does not contain `src/quantum_space_agi/mission_demo/`.

### 3.3 Repository instructions

- `CONTRIBUTING.md:18` — do not work directly on `main`.
- `CONTRIBUTING.md:19-20` — use a short-lived branch from the designated integration branch; "Until maintainers specify otherwise, target `develop` for pull requests."
- `README.md:21-23` — describes the local educational mission demo and explicitly says it is "not a complete mission-planning game or production API."
- `docs/NASAQ26_LOCAL_EDUCATIONAL_DEMO.md:27` — local URL is `http://127.0.0.1:8765/`; the server binds only to loopback.
- `docs/NASAQ26_MISSION_API_OWNER_DECISION_REGISTER.md:22` — `MAPI-02` canonical repository/branch is **OPEN / BLOCKED**. The register says the current checkout "does not establish a canonical production target."
- `docs/ARC10_DECISION_APPROVAL_REGISTER.md` — no ARC-10 decision is approved; production API/client implementation remains blocked.

### 3.4 ARC-10 documentation version search

Searched:

- `/mnt/e/nasa26/nasaq26-develop-worktree`
- `/mnt/e/nasa26/nasaq26-integration-worktree`
- `/mnt/e/nasa26/nasaq26-docs-worktree`
- `/mnt/e/nasa26/nasaq26-local-mission-demo-worktree`
- `/mnt/e/nasa26/quantum-space-agi-reusable-engine`
- `/mnt/e/nasa26` (top-level loose files)
- `/mnt/c/Users/HP/Downloads`
- Git refs: `refs/heads` and cached `refs/remotes` (content search for `v0.3`, `v0.4`, `version 0.3`, `version 0.4`; no network fetch was performed)

Results:

- ARC-10 documentation **v0.1** and **v0.2** exist on `origin/arc/10-api-integration`.
- A **Mission Planning & Simulation API Candidate Contract Proposal v0.1** exists as an untracked file on `develop`.
- **No ARC-10 v0.3 or v0.4 document exists in any searched location or git ref.**
- No filename or commit message in the searched refs references ARC-10 v0.3/v0.4.

## 4. Authority verdict

### What is established

1. `develop` at `6a44af3` contains the only complete local Mission API implementation and its tests.
2. `integration/nasaq26-branch-reconciliation` at `d7ac272` is an ancestor of `develop`; `develop` is the newer integrated line.
3. The repository's contribution instructions designate `develop` as the default PR integration branch.
4. The local demo is explicitly labelled synthetic, local, educational, and not a production API.
5. The `origin/arc/10-api-integration` branch contains planning documentation, not implementation.

### What is not established

1. No written Project Owner designation of a canonical production API repository and branch.
2. No designated Mission API contract owner or final approver.
3. No formal approval of routes, DTOs, unified result, error map, or versioning.
4. No acceptance authority for production API/frontend/security/operations testing.
5. No ARC-10 v0.3 or v0.4 documentation to compare.
6. No evidence that `origin/develop` or `origin/arc/10-api-integration` contains the implementation.

### Exact missing information needed to close authority

- A written Project Owner or maintainer decision naming the canonical repository, branch, integration target, and permitted change boundary for the Mission API (`MAPI-02`).
- The canonical contract location, version, owner, reviewers, and approval process (`MAPI-04`, `MAPI-05`, `MAPI-07`, `MAPI-15`).
- The location or confirmation of non-existence of ARC-10 documentation v0.3 and v0.4.
- Named ARC-05, ARC-08, ARC-09, security/privacy, test-acceptance, and operations authorities (`MAPI-04` through `MAPI-13`).
- A separate implementation authorization after those approvals (`MAPI-16`-adjacent release gate; `ARC10_DECISION_APPROVAL_REGISTER.md` D-16).

## 5. Decision on proceeding

Read-only six-artifact verification proceeded against the **operational source** `develop` at `6a44af3`, because:

- it is the only complete implementation,
- it is accessible,
- it has executable tests and a runnable local backend,
- the verification does not claim production authority or approval.

Production authority remains **BLOCKED**. See `ARC10_GAP_AND_DECISION_REGISTER.md`.

## 6. Final discovery status

**B — PARTIALLY VERIFIED.**

- Repository access: **RESOLVED** (not blocked).
- Implementation source: **ESTABLISHED** (`develop`).
- Formal authority/approval: **NOT ESTABLISHED / BLOCKED**.
- ARC-10 v0.3/v0.4 comparison: **NOT POSSIBLE — documents not found**.
