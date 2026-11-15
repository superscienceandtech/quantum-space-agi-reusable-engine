# Mission Run Authentication and Synthetic Simulation Repair

## Status summary

| Deliverable | Status | Evidence |
| --- | --- | --- |
| Repository audit | VERIFIED | Repository root, framework, git baseline, frontend, API, auth, data, and tests inspected. |
| Root-cause analysis | VERIFIED | Clerk variables are absent; the existing integration intentionally fails closed. Profile loading is behind the authenticated state. |
| Clerk implementation | VERIFIED / BLOCKED | ClerkJS and server-side JWT verification already exist. Real sign-in remains blocked on configuring a Clerk application and its environment values. |
| Synthetic profile flow | IMPLEMENTED / TESTED / BLOCKED | Client validates records and reports loading, empty, and failure states. Live profile loading requires an authenticated Clerk session. |
| Mission Run readiness | IMPLEMENTED / TESTED | Button is derived from auth, profile, selection, payload, and submission state; disabled reasons are announced. |
| Backend integration | VERIFIED / TESTED | Existing authenticated FastAPI profile, validation, and run routes and the local synthetic execution service are present. |
| Automated verification | TESTED / BLOCKED | Focused tests pass; the full suite retains one baseline PyJWT test failure. |
| Real Clerk and provider verification | NOT VERIFIED / BLOCKED | No live credentials, Clerk account, or staging service were available. |

## Repository audit

- **Repository root:** `/mnt/e/nasa26/nasaq26-develop-worktree`.
- **Baseline Git state:** branch `develop`, clean before this repair, based at
  `ccc5c98` (`1`).
- **Frontend:** static HTML and vanilla JavaScript in
  [`arc09-ui-prototype/`](../arc09-ui-prototype/).
- **Backend:** Python FastAPI in
  [`src/quantum_space_agi/mission_demo/`](../src/quantum_space_agi/mission_demo/).
- **Mission Run UI:** [`index.html`](../arc09-ui-prototype/index.html#L139),
  controlled by [`mission-demo.js`](../arc09-ui-prototype/mission-demo.js#L1).
- **Clerk frontend controller:** [`auth.js`](../arc09-ui-prototype/auth.js#L1).
  The app is not React and has no `ClerkProvider`; it loads ClerkJS from the
  configured Clerk Frontend API (Clerk UI v1 and ClerkJS v6). These are
  CDN-loaded, not installed npm dependencies.
- **Auth configuration and verification:** [`auth.py`](../src/quantum_space_agi/mission_demo/auth.py#L59),
  with public configuration and protected routes in
  [`api.py`](../src/quantum_space_agi/mission_demo/api.py#L230).
- **Synthetic profile source:** [`configuration.py`](../src/quantum_space_agi/mission_demo/configuration.py#L67).
  The authenticated profile endpoint is in
  [`api.py`](../src/quantum_space_agi/mission_demo/api.py#L315).
- **Mission validation and execution:** [`api.py`](../src/quantum_space_agi/mission_demo/api.py#L335),
  and [`run_mission`](../src/quantum_space_agi/mission_demo/api.py#L343), with
  simulation orchestration in
  [`service.py`](../src/quantum_space_agi/mission_demo/service.py#L1).
- **Related tests:** [`tests/mission_demo/`](../tests/mission_demo/), including
  API auth, service, dashboard, and browser-driven JavaScript tests.
- **Protected ARC-03 files:** none were changed.

## Root cause

The UI symptom has two related causes:

1. The repository has Clerk integration, but this runtime has no
   `CLERK_PUBLISHABLE_KEY`, `CLERK_FRONTEND_API_URL`, or
   `CLERK_ALLOWED_ORIGINS`. [`ClerkAuthSettings.from_environment`](../src/quantum_space_agi/mission_demo/auth.py#L102)
   reads these names, and `configured` requires frontend settings and an allowed
   origin ([`auth.py`](../src/quantum_space_agi/mission_demo/auth.py#L139)).
   The auth configuration route therefore returns `{"enabled": false}`
   ([`api.py`](../src/quantum_space_agi/mission_demo/api.py#L231)).
2. The browser only requests profiles after receiving a configured,
   authenticated Clerk state
   ([`mission-demo.js`](../arc09-ui-prototype/mission-demo.js#L403)).
   With Clerk unset, the profile request is correctly skipped, leaving the
   mission flow disabled. The backend separately rejects the protected mission
   routes without a verified token.

There was also a frontend readiness defect: after profile loading, the old code
enabled every form control, including Run with no payload selected. The profile
response was only checked for an array and a non-empty list, not for individual
profile validity or synthetic classification.

## Changes implemented

1. Added an accessible readiness message and changed the profile placeholder so
   it no longer remains stuck on “Loading” when authentication is unavailable.
2. Derived form and Run availability from authentication, successful profile
   loading, a currently listed profile selection, a supported payload selection,
   and whether a submission is in progress.
3. Added explicit empty-profile and malformed-profile handling. Profile records
   must have positive finite simulation values, valid assumptions, and the
   `synthetic educational profile` classification before they are exposed as
   selectable options.
4. Prevented duplicate form submissions. The existing server validation request
   still runs before the mission execution request; errors do not display a
   success-shaped result.
5. Added browser tests for payload readiness, empty and invalid profile
   responses, invalid profile selection, duplicate submission, successful
   synthetic result display, and mobile-width layout.
6. Documented local Clerk setup and this handover.

### Exact changed files

- [`arc09-ui-prototype/index.html`](../arc09-ui-prototype/index.html)
- [`arc09-ui-prototype/mission-demo.js`](../arc09-ui-prototype/mission-demo.js)
- [`tests/mission_demo/test_frontend_error_handling.py`](../tests/mission_demo/test_frontend_error_handling.py)
- [`docs/NASAQ26_LOCAL_EDUCATIONAL_DEMO.md`](./NASAQ26_LOCAL_EDUCATIONAL_DEMO.md)
- [`docs/MISSION_RUN_AUTHENTICATION_REPAIR_REPORT.md`](./MISSION_RUN_AUTHENTICATION_REPAIR_REPORT.md)

No backend auth, mission API, ARC-08, or protected ARC-03 source files were
changed.

## Clerk configuration and authentication flow

**Configuration status: BLOCKED pending environment setup.** The current
environment has none of the required Clerk variables set. No credentials were
invented, committed, or requested in chat. `.env.example` contains placeholders;
the application does not automatically load `.env`.

Configure these values in the process environment for local use or in the
provider's secure environment settings for staging:

- `CLERK_PUBLISHABLE_KEY` — the Clerk application's publishable key.
- `CLERK_FRONTEND_API_URL` — the Clerk Frontend API origin; HTTPS outside
  loopback.
- `CLERK_ALLOWED_ORIGINS` — exact browser origin(s), without paths or
  wildcards. Local default: `http://127.0.0.1:8765`.
- `CLERK_AUDIENCE` — optional, only if the Clerk token is configured with an
  audience.
- `PORT` — supplied by a hosting provider where required.

`CLERK_SECRET_KEY` is not used or read by this integration. The browser requests
`/api/v1/auth/config`, loads ClerkJS from the configured Frontend API, and
retrieves a session token in memory. It sends that token as a Bearer token to
the mission API. FastAPI verifies the token's signature against Clerk JWKS and
validates required claims; an authorized-party claim is restricted to the
configured origins when present. Missing, invalid, forbidden, or temporarily
unverifiable tokens fail closed. Authenticated test fixtures use controlled
signing keys and are not proof of real Clerk sign-in.

The existing detailed staging handover is
[`NASAQ26_BACKEND_STAGING_DEPLOYMENT_PLAN.md`](./NASAQ26_BACKEND_STAGING_DEPLOYMENT_PLAN.md).
Before sharing a staging URL, configure access restrictions and verify real
sign-in, sign-out, HTTPS, and allowed/denied accounts there.

## Local development and workflow

Follow the isolated environment and server commands in
[`NASAQ26_LOCAL_EDUCATIONAL_DEMO.md`](./NASAQ26_LOCAL_EDUCATIONAL_DEMO.md).
After setting Clerk variables, start the server with the same
environment-specific Python executable used for installing the API dependencies.

The app's flow is:

1. The public auth config route reports whether the required Clerk settings are
   present. The browser mounts Clerk sign-in or the signed-in user button.
2. After sign-in, the browser requests the protected synthetic profile list.
   The client verifies the response shape and classification before enabling
   selection.
3. The user selects a listed profile and at least one supported payload. The UI
   enables Run only when these inputs and the auth/profile states are ready.
4. On submit, the existing `/api/v1/missions/validate` route verifies and
   validates the request. Only after success does the browser call
   `/api/v1/missions/run`, which independently verifies authorization and runs
   the local `MissionDemoService`.
5. The displayed result is the successful synthetic response. ARC-08 resource
   evaluation remains informational and does not gate ARC-05 execution.

The UI does not probe the execution route separately: that route performs the
simulation. Its availability is confirmed by the actual request, and network
or server failures are reported without displaying a result.

## Verification results

| Command | Result |
| --- | --- |
| `python -m pytest tests/mission_demo/test_frontend_error_handling.py tests/mission_demo/test_dashboard.py -q` | **PASSED** — 25 passed. |
| `python -m pytest tests/mission_demo -q -k 'not test_pyjwkclient_refreshes_jwks_for_rotated_key'` | **PASSED** — 100 passed, 1 deselected. |
| `python -m ruff check tests/mission_demo/test_frontend_error_handling.py` | **PASSED**. |
| `git diff --check` | **PASSED**. |
| Live loopback Uvicorn smoke check with Clerk variables unset | **PASSED** — auth config returned `200 {"enabled":false}`; destinations, validation, and run returned `401`. |
| `python -m pytest -q` | **BLOCKED by one baseline failure** — 1,146 passed, 1 failed, 4 subtests passed. |

The remaining failure is
`tests/mission_demo/test_auth.py::test_pyjwkclient_refreshes_jwks_for_rotated_key`.
It fails while patching `jwt.jwks_client.time`, because the installed
`jwt.jwks_client` module has no `time` attribute. The same failure occurred in
the pre-change test run; auth code and this unrelated test were not modified.
The browser tests execute the dashboard JavaScript in headless Chrome; a
separate Node syntax check was not run.

## Remaining blockers and unverified items

- **BLOCKED:** Real Clerk sign-in, sign-out, token issuance, and session expiry
  behavior until valid Clerk settings and an authorized Clerk application are
  configured.
- **NOT VERIFIED:** Live synthetic profile retrieval and mission execution
  against a running, Clerk-configured server. Local API behavior is tested via
  the ASGI test client and simulated browser responses.
- **NOT VERIFIED:** Provider-side user restrictions, staging HTTPS, remote
  health, and team access policy.
- **BLOCKED:** Full suite is not entirely green due to the pre-existing
  PyJWT-test compatibility failure described above.
- No NASA data, production deployment, scientific validation, or external
  approval is claimed.
