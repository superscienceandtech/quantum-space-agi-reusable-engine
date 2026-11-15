# NASAQ26 Backend Staging Deployment Plan

## Status and scope

Recommendation: **Render Python web service from the source checkout, conditional on Clerk staging configuration and team access restrictions being verified before sharing a preview.**

No Clerk or Render configuration was made, and no deployment was attempted. This plan is not production approval. The application remains a synthetic educational demo; D-01 through D-06 are unchanged. Staging does not imply security, privacy, scientific/domain, operational, acceptance, or Project Owner production approval.

## Application and deployment evidence

- The integrated FastAPI application is `src/quantum_space_agi/mission_demo/api.py`; `src/quantum_space_agi/mission_demo/server.py` is a local launcher hard-coded to `127.0.0.1:8765`, so it is not the staging start command.
- The API registers health and mission routes, then mounts `arc09-ui-prototype/` at `/`. The API derives that directory from the source checkout. Running from the repository checkout retains the frontend files.
- The dashboard calls `/api/v1/missions/...` with relative same-origin paths. It is designed to work when served by this FastAPI app, without CORS.
- `pyproject.toml` requires Python `>=3.11` and declares FastAPI/Uvicorn in the `api` extra. The app has no database or persistent mission-result storage; mission state is returned to the browser and held there in memory.
- The wheel inspected at `dist/quantum_space_agi_reusable_engine-0.1.0-py3-none-any.whl` contains the Python API and server modules but not `arc09-ui-prototype/`. **Do not use wheel-only deployment for the integrated dashboard without a separately authorized packaging change.**
- No Dockerfile, Compose file, Render manifest, or Vercel configuration was found in the repository. No production deployment target is configured.

## Render evaluation

Render is the first hosting candidate because it supports a Python web service linked to a source repository with configured build and start commands. The app can remain in one source checkout and serve both dashboard and API.

| Requirement | Finding / decision |
|---|---|
| Source-checkout support | Supported by Render web services configured from a repository and branch. Use the repository root as the service root. |
| Python compatibility | Project declares `>=3.11`; local checks used Python 3.14.4. Choose and pin a Python version that Render currently offers and that the project supports. Do not rely on an unverified provider default. |
| Port binding | Render requires a web service to bind to `0.0.0.0` and recommends its `PORT` environment variable (documented default 10000). The staging start command below uses `$PORT`. |
| Health | Use `GET /health`; this route exists and returned `200 {"status":"ok"}` locally. Configure it as Render's HTTP health-check path. |
| Static assets | Present in a repository source checkout and served by the mounted `StaticFiles` app. Not present in the inspected wheel. |
| Environment | Clerk frontend configuration is required to enable protected mission routes: `CLERK_PUBLISHABLE_KEY`, `CLERK_FRONTEND_API_URL`, and exact `CLERK_ALLOWED_ORIGINS`; `CLERK_AUDIENCE` is optional. No Clerk secret key belongs in this app. Render supplies `PORT`; choose a supported Python version only after checking current availability. |
| Persistence | No persistent disk is needed for current demo behavior. Render's default filesystem is ephemeral; do not introduce runtime file persistence without a new review. |
| Execution limits | Render documents build/start command limits and free-instance sleep behavior, but the reviewed provider docs do not specify a general request-duration ceiling. The local synthetic run completed in smoke checks; production-scale duration/performance is unverified. |
| HTTPS | Render documents managed TLS for service domains and custom domains. HTTPS does not provide application authentication or access authorization. |

### Candidate Render commands

Run from the repository root:

**Build**

```sh
python -m pip install -e ".[api]"
```

**Start**

```sh
uvicorn quantum_space_agi.mission_demo.api:app --host 0.0.0.0 --port "$PORT"
```

Configure Render's health-check path as `/health`. The source-install command was previously verified in this checkout. Local server verification must bind to loopback; do not test an unauthenticated or incompletely configured service on `0.0.0.0`.

### Official Render sources

- [Web Services](https://render.com/docs/web-services)
- [Deploys](https://render.com/docs/deploys)
- [Health Checks](https://render.com/docs/health-checks)
- [Python Version](https://render.com/docs/python-version)
- [Disks](https://render.com/docs/disks)
- [Free Services](https://render.com/docs/free)
- [Private Services](https://render.com/docs/private-services)
- [Team Members](https://render.com/docs/team-members)
- [SAML SSO](https://render.com/docs/saml-sso)
- [Inbound IP Rules](https://render.com/docs/inbound-ip-rules)
- [TLS](https://render.com/docs/tls)

Provider documentation states that Render web services are internet-reachable; private services are reachable only within Render's private network. Inbound IP rules and some workspace identity features have plan requirements. Workspace access controls should not be confused with authentication of people using a public app.

## Security and private-staging gate

The mission routes now require a verified Clerk session token. Missing or invalid tokens receive `401`, a disallowed authorized party receives `403`, and unavailable verification fails closed with `503`. The dashboard, static assets, `/health`, and `/api/v1/auth/config` remain public. The auth code is covered by controlled-key tests, but real Clerk sign-in, user access restrictions, and provider deployment have not been verified.

Before sharing a staging preview, configure Clerk so only intended team members can authenticate (for example, invite-only access with public sign-up disabled, if supported by the selected Clerk application settings). Verify this restriction using an authorized team account and an account that should not have access. If the requirement is to hide even the dashboard and health route, separately configure and verify a provider-level access gate; mission-route authentication alone does not restrict those public resources.

Render Private Services are not a browser-accessible team preview by themselves; they are reachable by services on the same Render private network. A public Render web service must not be shared until Clerk access restrictions and HTTPS have been verified. No Clerk/Render settings, credentials, or access policy have been configured here.

The integrated dashboard uses same-origin relative API URLs, so no cross-origin browser request is needed. `CLERK_ALLOWED_ORIGINS` must nevertheless contain the exact browser origin(s), without paths or wildcards; it is used for authorized-party validation and CORS. If a separate Vercel frontend is later authorized, add only its exact origin after that architecture is reviewed.

The app logs unexpected exception details server-side and returns a generic error to callers. A production access/audit logging policy and retention have not been established; review them before staging exposure. Do not place credentials or secrets in source, request messages, or this plan.

## Clerk staging setup and verification

The following are user actions; none have been performed:

1. Create or select a **staging-only** Clerk application. In its Dashboard, obtain the publishable key and Frontend API URL for that application. Configure sign-in and restrict account creation/access to intended reviewers or team members; do not enable unrestricted public sign-up for a team-only preview.
2. In Render, create a Python web service from the authorized repository and branch, using the repository root. Add these environment variables using the actual staging values in Render's secure settings:
   - `CLERK_PUBLISHABLE_KEY` — the staging application's publishable key.
   - `CLERK_FRONTEND_API_URL` — that application's HTTPS Frontend API origin.
   - `CLERK_ALLOWED_ORIGINS` — the exact HTTPS staging service origin, with no path or wildcard. Use comma-separated exact origins only if multiple origins are explicitly needed.
   - `CLERK_AUDIENCE` — optional; set only when the Clerk token audience is intentionally configured.
   - `PORT` — supplied by Render at runtime; do not invent or commit a value.
   - Do **not** configure or expose a Clerk secret key; the browser needs only the publishable key, while the API verifies tokens against Clerk JWKS.
3. Use the build/start commands above and set the Render health-check path to `/health`. Confirm the service uses HTTPS before sign-in.
4. Before sharing the URL, verify `/health`, `/`, and the dashboard load over HTTPS; confirm each of the three mission endpoints returns `401` without a token; then sign in with an authorized team account and verify destination loading, validation, and a synthetic mission run. Also test that an unauthorized account cannot obtain a usable session. If those access restrictions cannot be verified, do not share the preview.
5. Authenticated API tests use controlled signing keys and are not proof of real Clerk integration. Real Clerk sign-in/logout, Render environment configuration, remote health, HTTPS, and team access restrictions remain pending until verified in the provider.

The placeholder-only variable names and safe defaults are listed in [`.env.example`](../.env.example). Never request or paste live credentials into chat or commit them.

## Vercel frontend decision

**A separate Vercel frontend is not needed for the first staging deployment.** The current FastAPI service already serves the integrated dashboard and API from one origin, and the dashboard uses relative API URLs. Keeping that arrangement avoids new frontend configuration and CORS requirements.

The standalone `arc09-ui-prototype/` is an isolated static concept prototype, not a separately built production frontend. No `package.json`, frontend build command, Vercel output configuration, backend URL setting, or Vercel rewrite is present. If a Vercel frontend is later required, its source directory would be `arc09-ui-prototype/`; its build/output and a backend-origin configuration mechanism must be agreed and verified first. No environment-variable name is configured or proposed here, and no Vercel configuration should be added until that need is confirmed.

Official Vercel reference: [Frontend frameworks](https://vercel.com/docs/frameworks/frontend).

## Confirmed blockers and external requirements

### Confirmed technical/security blockers

- Real Clerk authentication and team-only account access have not been configured or verified; do not share a staging preview until both are confirmed.
- `/health`, the dashboard, static assets, and auth configuration are public unless a provider-level gate is added.
- The local launcher binds only to loopback; staging must use the Render start command and host/port contract.
- Wheel-only deployment omits required dashboard assets.
- Python version availability and runtime compatibility must be selected and confirmed with the chosen Render service.
- Production-grade access logging, monitoring, backup/recovery, and request-duration behavior are not established.

### External access and user decisions required

- Explicit authorization and access to create a **staging-only** Render service and connect the selected repository/branch. No provider account or service access was available here.
- A staging-only Clerk application, its publishable key and Frontend API URL, and verified invitation/sign-up restrictions. Enter live values only in the provider's secure settings, never this repository or chat.
- The exact HTTPS staging origin for `CLERK_ALLOWED_ORIGINS`, determined after Render assigns the service URL.
- Select Render workspace/region/plan and confirm which Python version is supported there.
- Decide whether public dashboard/health visibility is acceptable; if not, select and verify a provider-level access gate before sharing the URL.
- Confirm whether free-instance sleep/cold starts are acceptable or choose an appropriate plan.
- Confirm who may access the staging preview and how access will be tested.

No credentials, actual domains, reviewer identities, or account details are recorded. Provider deployment remains unauthorized until explicit authorization and all required staging access controls are available.

## Verification actually performed

Using `/home/yousuf/.venvs/nasaq26-develop-worktree/bin/python` in the current checkout:

- `python -m pip check` — succeeded with no broken requirements.
- `python -m pytest tests/mission_demo -q` — 90 passed.
- Loopback Uvicorn smoke check with all Clerk variables unset — `/health`, `/`, and `/mission-demo.css` returned `200`; `/api/v1/auth/config` returned `200 {"enabled":false}`; the destinations, validation, and run routes each returned `401`.
- The focused changed-code lint and `mypy --python-version 3.14` checks passed. The planned repository-wide Ruff command reports 21 existing lint findings in the pre-existing untracked `tests/mission_demo/test_arc09_visualization.py`; that unrelated file was not changed. Default `mypy` stops on the installed NumPy stub's Python 3.12+ `type` statement; the Python 3.14-targeted check passed.
- `node --check` could not run because neither `node` nor `nodejs` is installed. The dashboard/browser tests execute the auth and mission JavaScript with controlled Clerk stubs.
- `git diff --check` — passed.
- The server was bound only to `127.0.0.1`; no public interface was used.
- Real Clerk sign-in/logout, Render environment configuration, remote health, HTTPS, and team access restrictions were not verified. No provider deployment, staging URL, or Vercel deployment was performed.
