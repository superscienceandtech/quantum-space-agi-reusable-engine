# Clerk Authentication for NASAQ26 Staging

## Status

Conversational design approved. Written specification is awaiting user review.
This document defines an implementation proposal; no authentication code,
provider configuration, or deployment has been changed.

## Goal and constraints

Add managed Clerk sign-in to the existing static ARC-09 dashboard and enforce
Clerk session-token authentication in the integrated FastAPI Mission Demo.
Protect mission operations even when called outside the browser UI. Prepare the
application for a staging-only Render deployment without creating a Clerk
application, configuring external services, or deploying.

Preserve the current Mission Planning & Simulation API / Dataset Validation API
separation, ARC-05 and ARC-08 boundaries, ARC-09 behavior, synthetic-only
execution labeling, and decisions D-01 through D-06. Authentication and staging
do not grant production approval.

## Existing application

- `src/quantum_space_agi/mission_demo/api.py` creates the FastAPI app, defines
  health and mission routes, and mounts `arc09-ui-prototype/` at `/`.
- The existing dashboard is plain HTML, CSS, and JavaScript; there is no
  frontend package manifest or build pipeline.
- `arc09-ui-prototype/mission-demo.js` calls the three mission endpoints with
  same-origin `fetch()` requests and does not currently attach credentials.
- The mission service executes synthetic educational ARC-05/ARC-08 operations.
- Existing API tests assume that mission routes are unauthenticated and will
  need focused updates while preserving their request/response coverage.
- The current worktree has pre-existing modifications and untracked files.
  Implementation must inspect and preserve these; it must not overwrite
  unrelated dashboard changes.

## Approaches considered

1. **ClerkJS with FastAPI token verification (selected).** Load Clerk's
   documented browser SDK and prebuilt UI from the configured Clerk Frontend API
   URL; use the existing static dashboard and add server-side JWT/JWKS
   verification. This fits the current app without introducing a frontend
   framework or build system.
2. **Add a Vite/npm frontend and integrate Clerk there.** This would add a
   separate build/dependency workflow and restructure the current static
   prototype without solving a need in the current same-origin architecture.
3. **Rely on hosting-level access protection.** This would not provide the
   requested Clerk session or enforce identity in FastAPI, so it is insufficient
   as the API authorization boundary.

The current Clerk JavaScript quickstart documents ClerkJS v6 and Clerk UI v1
loaded from the configured Frontend API URL, `Clerk.load()`,
`mountSignIn()`, and `mountUserButton()`. Clerk's session-token and manual
verification guides document session JWT claims, JWKS, issuer, expiration,
not-before, and authorized-party validation. PyJWT's `PyJWKClient` is the
selected JWKS/key-resolution mechanism; token algorithms must be restricted to
the configured Clerk asymmetric signing algorithm allowlist, not selected
solely from attacker-controlled token headers.

## Architecture and request flow

### Browser

1. Keep the dashboard shell, health endpoint, static assets, and public
   project-facing information accessible without a session.
2. Add a public runtime-auth-configuration endpoint that returns only the
   Clerk publishable key and Frontend API URL. These are public client
   configuration, not server secrets. Do not return secret keys or verification
   material.
3. Load ClerkJS and its UI bundle from the configured Frontend API URL, then use
   Clerk's supported prebuilt sign-in and user-account UI for registration,
   login, and logout.
4. Keep mission controls disabled until Clerk has loaded and reports an active
   session. Present a minimal signed-in state without exposing token contents or
   sensitive claims.
5. Immediately before each mission API call, request a short-lived token from
   the active Clerk session and send it as `Authorization: Bearer <token>`.
   Never persist tokens in localStorage or other long-lived browser storage.
6. On 401, clear displayed mission state and show an actionable reauthentication
   message. Handle 403 distinctly. Do not retry indefinitely or display raw
   tokens/provider secrets.

### FastAPI

1. Keep `GET /health`, `GET /`, the dashboard assets, and the auth runtime
   configuration public.
2. Require a verified Bearer session token on:
   - `GET /api/v1/missions/destinations`
   - `POST /api/v1/missions/validate`
   - `POST /api/v1/missions/run`
3. Verify token signatures against Clerk's configured JWKS URL using PyJWT.
   Cache the JWKS and signing keys with rotation support; refresh on an unknown
   key ID. Fix the accepted asymmetric algorithms in application configuration.
4. Validate issuer, expiration, not-before when present, required subject/session
   identity claims, optional configured audience, and the authorized party
   against configured origins when the claim is present. Require the exact
   session-token shape; never treat decoded but unverified claims as identity.
5. Missing or invalid credentials return 401 with the repository's safe API
   error envelope. A correctly authenticated token whose `azp` is outside the
   configured authorized-party policy returns 403. The current product policy
   defines no role or admin restriction, so every otherwise valid signed-in
   user is authorized for these three routes.
6. A missing provider configuration or inability to obtain/refresh required
   verification keys fails closed. Do not log bearer tokens, claims, or secrets.
7. Keep request validation and mission service behavior unchanged after the
   authentication dependency has authorized the request.

## CORS, transport, and rate limiting

- Same-origin integrated dashboard requests do not require CORS.
- Add CORS middleware only for explicitly configured frontend origins. Permit
  only required methods and `Authorization`/`Content-Type` headers; do not use
  wildcard origins or credentialed cookies.
- Use bearer headers rather than application cookies, avoiding cookie-based
  CSRF for mission requests.
- Render-managed HTTPS must be enabled and verified before a public staging
  preview is used. Do not claim HTTPS or access controls are operational before
  provider verification.
- Add per-user, process-local, fixed-window limits for one-instance staging:
  5 mission runs/minute, 30 validations/minute, and 60 destination reads/minute.
  Return 429 and `Retry-After` when exceeded. This is intentionally not a
  multi-instance or production-grade limiter; scale-out or production requires
  a separately reviewed shared limiter and operational policy.

## Configuration

Use these server environment variables:

- `CLERK_PUBLISHABLE_KEY` — public Clerk browser key.
- `CLERK_FRONTEND_API_URL` — configured Clerk Frontend API origin; derive the
  expected token issuer and JWKS URL from this trusted configuration.
- `CLERK_AUDIENCE` — optional expected audience, only when configured in the
  Clerk session-token setup.
- `CLERK_ALLOWED_ORIGINS` — comma-separated exact browser origins used for
  CORS and `azp` validation; no wildcard.
- `PORT` — supplied by Render for the Uvicorn listener.

Use only safe placeholders in `.env.example`. The Clerk secret key is not
required for local JWT verification and must not be added to browser code, the
repository, or chat. Missing Clerk configuration must leave the public shell
available but mission requests unavailable.

## Error behavior

- Missing, malformed, expired, wrong-signature, wrong-issuer, wrong-audience,
  or otherwise invalid session token: 401.
- Valid identity with a disallowed `azp`: 403.
- A future role-based denial would also use 403, but no role policy is included.
- Verification infrastructure unavailable or required server configuration
  absent: fail closed with an explicit service-unavailable error; do not return
  a success-shaped response.
- Rate limit exceeded: 429 with `Retry-After`.
- Preserve existing validation and generic error responses; never include
  implementation details or credentials in client errors.

## Verification plan

Use generated controlled signing keys and an injected JWKS response in tests;
never use real Clerk credentials. Cover:

- Missing and malformed Bearer tokens.
- Invalid signature, expiration, issuer, configured audience, and authorized
  party.
- Missing required identity claims and JWKS retrieval/key-rotation failures.
- Public health, dashboard, assets, and runtime-config behavior.
- Authentication required on each mission route and valid authenticated
  destinations, validation, and synthetic execution.
- 401/403/429 behavior, CORS allowlist behavior, and token non-disclosure.
- Existing mission validation, error, ARC-05/ARC-08, and dashboard regression
  tests.

Run `python -m pytest tests/mission_demo -q`, applicable Ruff/mypy checks, and
`git diff --check`. Browser testing with real Clerk sign-in/logout and real
provider JWTs remains pending until configuration is supplied securely.

## Staging boundary and manual setup

Do not create a Clerk account, configure Clerk or Render, or deploy as part of
the code change. Update the existing backend staging plan with:

1. Create a Clerk staging application and choose sign-in/sign-up methods.
2. Set allowed development and staging origins in Clerk.
3. Obtain the Frontend API URL and publishable key from Clerk's dashboard.
4. Configure the environment variables above in Render's secure environment
   settings, using the actual staging origin and never committing secrets.
5. Use source-checkout deployment, the existing editable-install build command,
   the Uvicorn command using Render's `PORT`, and `/health` as health check.
6. Verify public landing/dashboard behavior, unauthenticated 401s, authenticated
   route access, CORS, HTTPS, and one-instance rate limits before sharing the
   staging URL.

No staging URL can be recorded until a provider confirms deployment. Production
remains **NOT APPROVED**.

## Sources

- [Clerk JavaScript quickstart](https://clerk.com/docs/js-frontend/getting-started/quickstart)
- [Clerk session tokens](https://clerk.com/docs/guides/sessions/session-tokens)
- [Clerk manual JWT verification](https://clerk.com/docs/guides/sessions/manual-jwt-verification)
- [PyJWT API reference](https://pyjwt.readthedocs.io/en/stable/api.html#jwt.PyJWKClient)
