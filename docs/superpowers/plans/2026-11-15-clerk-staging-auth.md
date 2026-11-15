# Clerk Staging Authentication Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add real Clerk sign-in to the existing dashboard and require server-verified Clerk session tokens for all mission API operations, ready for separately authorized staging setup.

**Architecture:** Keep the existing same-origin FastAPI/static-dashboard architecture. Load documented ClerkJS/UI from the configured Clerk Frontend API URL, attach a short-lived session token to mission requests, and verify it in FastAPI with PyJWT/JWKS before applying a bounded single-instance per-user rate limit.

**Tech Stack:** Python 3.11+, FastAPI, PyJWT with cryptographic support, PyJWKClient, pytest/httpx, plain HTML/CSS/JavaScript, ClerkJS v6 and Clerk UI v1 hosted by the configured Frontend API.

**Spec:** `docs/superpowers/specs/2026-11-15-clerk-staging-auth-design.md`

## Global Constraints

- Keep the dashboard shell, health route, static assets, and auth runtime configuration public.
- Require verified Clerk session tokens for `GET /api/v1/missions/destinations`, `POST /api/v1/missions/validate`, and `POST /api/v1/missions/run`.
- Never trust decoded-but-unverified claims; verify issuer, expiration, not-before when present, required subject/session claims, optional configured audience, and `azp` when present.
- Missing/invalid credentials return 401; a valid identity with disallowed `azp` returns 403; required verification infrastructure unavailable fails closed.
- Do not log or persist bearer tokens; do not expose Clerk secret keys in browser code or repository files.
- CORS allows only configured exact origins, required methods, and `Authorization`/`Content-Type`; credentialed cookies and wildcard origins are not used.
- Enforce per-user, process-local limits for one-instance staging: 5 mission runs/minute, 30 validations/minute, and 60 destination reads/minute; return 429 with `Retry-After`.
- Add `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`, and `X-Frame-Options: DENY`; defer restrictive CSP until Clerk directives are verified.
- Keep synthetic execution labels, ARC-05/ARC-08 boundaries, the separate Dataset Validation API, and decisions D-01 through D-06 unchanged. Production remains **NOT APPROVED**.
- Do not create a Clerk account, configure Render, deploy, or record an unverified staging URL.
- Preserve all existing dirty and untracked work; inspect each dirty file before editing it and stage only task-owned files.

## Review Focus

- **JWKS unavailable or rotated signing key:** a cached key may continue to verify, but an unknown key that cannot be fetched must fail closed; Task 1 and Task 2 tests cover fetch errors and unknown `kid`.
- **Malformed, expired, wrong-issuer, wrong-audience, or wrong-signature token:** return 401 without leaking token material; Task 1 tests cover each invalid case.
- **Correctly signed token with a disallowed `azp`:** return 403; Task 1 and Task 2 tests cover the authorization distinction.
- **Missing Clerk environment configuration:** keep public landing routes available, report auth as unconfigured, and never permit mission access; Task 2 tests cover this state.
- **Rate-limit boundary and window rollover:** requests at the cap succeed, the next request gets 429 with a positive `Retry-After`, and a later window recovers; Task 3 tests cover this behavior.

---

### Task 1: Clerk Settings and Session-Token Verification

**Files:**
- Modify: `pyproject.toml`
- Create: `src/quantum_space_agi/mission_demo/auth.py`
- Create: `tests/mission_demo/test_auth.py`

**Interfaces:**
- `ClerkAuthSettings.from_environment() -> ClerkAuthSettings`
- `ClerkAuthSettings` fields: `publishable_key: str | None`, `frontend_api_url: str | None`, `audience: str | None`, and `allowed_origins: tuple[str, ...]`.
- `AuthenticatedUser(user_id: str, session_id: str, authorized_party: str | None)`
- `ClerkTokenVerifier.verify(token: str) -> AuthenticatedUser`
- Exceptions: `InvalidSessionToken`, `ForbiddenAuthorizedParty`, and `ClerkVerificationUnavailable`.
- `ClerkTokenVerifier` accepts an injectable key resolver for deterministic tests; production uses `jwt.PyJWKClient` with a finite timeout and JWKS cache.

- [ ] **Step 1: Write failing cryptographic verifier tests**

Create generated RSA signing keys, a token encoder, and a fixed-key resolver so tests exercise real signature verification without Clerk credentials:

```python
from types import SimpleNamespace

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from quantum_space_agi.mission_demo.auth import (
    ClerkAuthSettings,
    ClerkTokenVerifier,
    InvalidSessionToken,
)

DEFAULT_CLAIMS = {
    "iss": "https://clerk.example",
    "exp": 4_000_000_000,
    "iat": 1_700_000_000,
    "sub": "user_test_123",
    "sid": "sess_test_123",
    "azp": "https://app.example",
}


class FixedKeyResolver:
    def __init__(self, public_key):
        self.public_key = public_key

    def get_signing_key_from_jwt(self, token):
        return SimpleNamespace(key=self.public_key)


def encode_test_token(signing_key, changes=None, algorithm="RS256"):
    payload = DEFAULT_CLAIMS.copy()
    for name, value in (changes or {}).items():
        if value is None:
            payload.pop(name, None)
        else:
            payload[name] = value
    return jwt.encode(
        payload,
        signing_key,
        algorithm=algorithm,
        headers={"kid": "test-key"},
    )


@pytest.fixture(scope="module")
def signing_key():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture
def verifier(signing_key):
    settings = ClerkAuthSettings(
        publishable_key="pk_test_example",
        frontend_api_url="https://clerk.example",
        audience=None,
        allowed_origins=("https://app.example",),
    )
    resolver = FixedKeyResolver(signing_key.public_key())
    return ClerkTokenVerifier(settings, jwks_client=resolver)


def test_verifies_a_valid_session_token(verifier, signing_key):
    user = verifier.verify(encode_test_token(signing_key))
    assert user.user_id == "user_test_123"
    assert user.session_id == "sess_test_123"


@pytest.mark.parametrize(
    "changes",
    [
        {"iss": "https://other.example"},
        {"exp": 1},
        {"sub": None},
    ],
)
def test_rejects_invalid_or_incomplete_session_claims(verifier, signing_key, changes):
    with pytest.raises(InvalidSessionToken):
        verifier.verify(encode_test_token(signing_key, changes))
```

- [ ] **Step 2: Run the focused tests and confirm they fail**

Run: `python -m pytest tests/mission_demo/test_auth.py -q`

Expected: FAIL because the verifier and settings types do not exist.

- [ ] **Step 3: Add the verification dependency and implement settings/verifier**

Add `PyJWT[crypto]>=2.10,<3` to the `api` optional dependencies. In `auth.py`, normalize and validate the configured Frontend API origin, derive issuer and `/.well-known/jwks.json`, parse exact comma-separated `CLERK_ALLOWED_ORIGINS`, and support optional `CLERK_AUDIENCE`. Configure `PyJWKClient` with a finite timeout and JWKS cache; use its unknown-`kid` refresh behavior. Fix the accepted algorithm to `RS256` (the current Clerk manual-verification example) rather than reading an allowlist from the untrusted token. Require `iss`, `exp`, `iat`, `sub`, and `sid`; validate `nbf` and `aud` when present/configured. Convert invalid token/claim failures to `InvalidSessionToken`, a verified but disallowed `azp` to `ForbiddenAuthorizedParty`, and JWKS transport/configuration failures to `ClerkVerificationUnavailable`. Do not log tokens or raw claims.

- [ ] **Step 4: Add verifier failure and rotation tests**

Use the controlled private key to test wrong signature, invalid algorithm, future `nbf`, invalid configured audience, and disallowed `azp`. Use a resolver that raises a network error to test `ClerkVerificationUnavailable`. For real cache/rotation behavior, run a loopback-only `http.server.ThreadingHTTPServer` serving a controlled JWKS: return key A first, then key B; verify an A-signed token, then a B-signed token with a new `kid`, and assert PyJWKClient refreshes the JWKS and verifies B. Assert required claims are rejected when absent and error messages do not contain encoded token data.

- [ ] **Step 5: Run focused tests and dependency validation**

Run: `python -m pip install -e ".[api]" && python -m pip check && python -m pytest tests/mission_demo/test_auth.py -q`

Expected: no broken requirements and all verifier tests pass.

- [ ] **Step 6: Commit only Task 1 files**

```bash
git add pyproject.toml src/quantum_space_agi/mission_demo/auth.py tests/mission_demo/test_auth.py
git commit -m "feat: verify Clerk session tokens" -m "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

### Task 2: FastAPI Route Protection, Runtime Configuration, and Headers

**Files:**
- Modify: `src/quantum_space_agi/mission_demo/api.py`
- Modify: `tests/mission_demo/test_api.py`
- Create or modify: `tests/mission_demo/conftest.py` only if a shared controlled-key fixture is needed

**Interfaces:**
- Extend `create_app(service=None, auth_settings=None, token_verifier=None)` without breaking current service injection.
- Add `GET /api/v1/auth/config`, returning only `{"enabled": false}` when Clerk frontend settings are absent, or the configured publishable key and Frontend API URL when enabled.
- Add a synchronous FastAPI dependency that extracts Bearer credentials, invokes `ClerkTokenVerifier.verify`, and exposes only `AuthenticatedUser`.

- [ ] **Step 1: Add failing route-boundary tests**

Extend the test client helper so it can issue requests with a controlled signed token. Assert that health, dashboard shell, dashboard assets, and auth config are public; each mission route returns 401 without credentials; and each accepts a valid token. Assert no response contains test token strings or Clerk secret-key-like values.

- [ ] **Step 2: Run focused API tests and confirm the authorization failures**

Run: `python -m pytest tests/mission_demo/test_api.py -q`

Expected: new uncredentialed route assertions fail because mission routes are currently public.

- [ ] **Step 3: Wire settings, the auth dependency, and public config**

Update `create_app` to accept settings/verifier injection while retaining `MissionDemoService` injection. Register `/api/v1/auth/config` before mounting `StaticFiles`. Add the auth dependency to all three mission route signatures. Return safe 401 and 403 errors using the existing error envelope; return an explicit 503 when verification configuration or required JWKS retrieval is unavailable. Leave health, static assets, and public dashboard information unauthenticated.

- [ ] **Step 4: Add CORS and baseline security response headers**

Configure `CORSMiddleware` from exact `CLERK_ALLOWED_ORIGINS`, allow only GET/POST/OPTIONS and Authorization/Content-Type headers, and set `allow_credentials=False`. Add middleware for `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`, and `X-Frame-Options: DENY` on API, health, and static responses. Do not add a restrictive CSP before verifying Clerk's script and connection directives.

- [ ] **Step 5: Complete API boundary and configuration tests**

Test missing/malformed credentials, invalid signature, invalid `azp` => 403, verifier/JWKS outage => fail-closed 503, all protected routes, valid execution through the existing `MissionDemoService`, public route access with unset Clerk variables, CORS allow/deny behavior, and each required response header. Capture authentication failure logs and confirm they do not contain the submitted token. Preserve DTO validation and error-envelope assertions.

- [ ] **Step 6: Run the API test module**

Run: `python -m pytest tests/mission_demo/test_api.py -q`

Expected: all public/protected route, error, and mission regression tests pass.

- [ ] **Step 7: Commit only Task 2 files**

```bash
git add src/quantum_space_agi/mission_demo/api.py tests/mission_demo/test_api.py tests/mission_demo/conftest.py
git commit -m "feat: protect mission API with Clerk auth" -m "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

### Task 3: Bounded Per-User Staging Rate Limits

**Files:**
- Create: `src/quantum_space_agi/mission_demo/rate_limit.py`
- Modify: `src/quantum_space_agi/mission_demo/api.py`
- Create: `tests/mission_demo/test_rate_limit.py`
- Modify: `tests/mission_demo/test_api.py`

**Interfaces:**
- `FixedWindowRateLimiter.check(user_id: str, route_key: str, limit: int, now: float | None = None) -> int | None` returns `None` when allowed or a positive retry delay when limited.
- Use a lock for thread safety and bounded/pruned in-memory state. Inject a monotonic clock in tests.
- Cap retained user/route entries at `MAX_RATE_LIMIT_ENTRIES = 10_000`.
- Apply policy by authenticated `user_id`: run 5/minute, validate 30/minute, destinations 60/minute.
- Extend `create_app` with an optional rate-limiter injection so HTTP tests can use a deterministic clock.

- [ ] **Step 1: Write failing limiter tests**

Test an allowed request, the exact limit boundary, the first over-limit request, route-key isolation, user isolation, next-window recovery, and bounded cleanup. Use a fake monotonic clock instead of sleeping.

- [ ] **Step 2: Run the limiter tests and confirm they fail**

Run: `python -m pytest tests/mission_demo/test_rate_limit.py -q`

Expected: FAIL because `FixedWindowRateLimiter` does not exist.

- [ ] **Step 3: Implement the fixed-window limiter**

Implement per-user/route counters keyed by fixed 60-second windows, protect mutations with `threading.Lock`, remove expired windows, and cap retained entries so a stream of distinct users cannot grow process memory without bound. Return at least one second of `Retry-After` for blocked requests.

- [ ] **Step 4: Enforce each route's configured policy**

Call the limiter only after authentication has produced a verified user. Map an exceeded limit to 429 with `Retry-After`; do not count rejected unauthenticated requests against another user's bucket.

- [ ] **Step 5: Verify limiter/API behavior**

Run: `python -m pytest tests/mission_demo/test_rate_limit.py tests/mission_demo/test_api.py -q`

Expected: direct limiter and HTTP 429 boundary tests pass; mission behavior remains unchanged below the cap.

- [ ] **Step 6: Commit only Task 3 files**

```bash
git add src/quantum_space_agi/mission_demo/rate_limit.py src/quantum_space_agi/mission_demo/api.py tests/mission_demo/test_rate_limit.py tests/mission_demo/test_api.py
git commit -m "feat: limit staging mission request rates" -m "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

### Task 4: Clerk Dashboard UI and Authenticated Mission Requests

**Files:**
- Create: `arc09-ui-prototype/auth.js`
- Modify: `arc09-ui-prototype/index.html`
- Modify: `arc09-ui-prototype/mission-demo.js`
- Modify: `arc09-ui-prototype/mission-demo.css`
- Modify: `tests/mission_demo/test_dashboard.py`

**Interfaces:**
- `window.nasaqAuth.ready: Promise<void>` resolves after runtime configuration and Clerk initialization complete, including the unconfigured state.
- `window.nasaqAuth.getToken(): Promise<string | null>` returns the active Clerk session token or `null`; it never persists the token.
- `window.nasaqAuth.isSignedIn(): boolean` reports the SDK's current signed-in state.
- `auth.js` dispatches `nasaq-auth:state` with only `{ signedIn: boolean, configured: boolean }`; it does not dispatch user claims or tokens.

- [ ] **Step 1: Add failing dashboard contract tests**

Update dashboard tests to require the Clerk mount points and auth script before the mission adapter. Assert the adapter obtains a session token and sends an Authorization header for all three mission endpoints, handles 401 and 403 distinctly, does not use localStorage/sessionStorage, and keeps the mission submit control disabled while signed out or auth is unconfigured.

- [ ] **Step 2: Run focused dashboard tests and confirm they fail**

Run: `python -m pytest tests/mission_demo/test_dashboard.py -q`

Expected: FAIL because the dashboard has no Clerk integration or authenticated fetch helper.

- [ ] **Step 3: Add accessible Clerk mount points and a dedicated auth controller**

Replace the static prototype avatar with a Clerk auth area, add a sign-in mount point/status message in the mission workspace, and load `auth.js` before `mission-demo.js`. In `auth.js`, fetch `/api/v1/auth/config`, load Clerk UI v1 and ClerkJS v6 sequentially from the configured Frontend API URL, call `Clerk.load`, mount Clerk SignIn when signed out and UserButton when signed in, and expose only the interface defined above. If configuration or SDK loading fails, keep the dashboard shell visible and mission controls disabled with an explicit status.

- [ ] **Step 4: Attach a fresh session token to mission requests**

In `mission-demo.js`, centralize protected `fetch` calls so each obtains `await window.nasaqAuth.getToken()` immediately before sending, adds the Authorization header, and never stores the token. Do not load destinations until sign-in; keep all submit controls disabled until auth is ready and signed in. On 401 clear mission results and show reauthentication guidance; on 403 show an authorization message; preserve existing validation and simulation error states.

- [ ] **Step 5: Add frontend source and syntax regression checks**

Run: `python -m pytest tests/mission_demo/test_dashboard.py tests/mission_demo/test_frontend_error_handling.py -q`

Run: `node --check arc09-ui-prototype/auth.js && node --check arc09-ui-prototype/mission-demo.js`

Expected: dashboard contract/error tests and JavaScript syntax checks pass. Real Clerk sign-in/logout remains unverified until real provider configuration is securely supplied.

- [ ] **Step 6: Commit only Task 4 files**

```bash
git add arc09-ui-prototype/auth.js arc09-ui-prototype/index.html arc09-ui-prototype/mission-demo.js arc09-ui-prototype/mission-demo.css tests/mission_demo/test_dashboard.py
git commit -m "feat: add Clerk sign-in to mission dashboard" -m "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

### Task 5: Safe Environment Example, Render Handover, and Final Verification

**Files:**
- Create: `.env.example`
- Modify: `docs/NASAQ26_BACKEND_STAGING_DEPLOYMENT_PLAN.md`

**Interfaces:**
- `.env.example` contains placeholders only for `CLERK_PUBLISHABLE_KEY`, `CLERK_FRONTEND_API_URL`, optional `CLERK_AUDIENCE`, `CLERK_ALLOWED_ORIGINS`, and the Render-provided `PORT`.
- The existing deployment plan documents exact provider setup actions and explicitly states that no Clerk/Render setup or deployment occurred.

- [ ] **Step 1: Add safe environment guidance**

Create `.env.example` with reserved/example placeholders only; do not add `.env`, real keys, actual domains, team CIDRs, or a Clerk secret key. Confirm `.gitignore` ignores `.env` and `.env.*` while allowing `.env.example`.

- [ ] **Step 2: Update the existing deployment plan in place**

Add the exact Clerk Dashboard actions, configured Frontend API URL and publishable key steps, exact Render environment variable names, allowed-origin requirements, source-checkout build/start commands, `/health` path, HTTPS verification, and the requirement to verify unauthenticated 401s and authenticated mission requests before sharing a preview. State that auth code can be tested with controlled keys while real Clerk operation and deployment are pending.

- [ ] **Step 3: Run all requested mission-demo regressions**

Run: `python -m pytest tests/mission_demo -q`

Expected: all tests pass, including existing synthetic mission, ARC-05/ARC-08, dashboard, accessibility/error, auth, CORS, security-header, and rate-limit tests.

- [ ] **Step 4: Run focused quality and configuration checks**

Run: `python -m pip check`

Run: `python -m ruff check src/quantum_space_agi/mission_demo tests/mission_demo`

Run: `python -m mypy src/quantum_space_agi/mission_demo`

Run: `node --check arc09-ui-prototype/auth.js && node --check arc09-ui-prototype/mission-demo.js`

Run: `git diff --check`

Expected: all commands exit zero. If any check fails, fix only issues caused by this implementation and rerun that exact check.

- [ ] **Step 5: Verify local public/protected behavior without Clerk secrets**

Start the app on loopback with Clerk variables unset. Confirm `/health`, `/`, static dashboard assets, and auth config are public; confirm all mission routes return 401 and the UI presents the unconfigured state. Use controlled-key ASGI tests for successful authenticated API requests; do not expose the app on `0.0.0.0` or use real credentials.

- [ ] **Step 6: Record real-provider blockers without deployment**

Record that a Clerk staging application, actual publishable key/Frontend API URL, allowed staging origin, Render repository/service access, and provider HTTPS/access verification are required. Do not ask for secrets in chat, create accounts, deploy, or claim a staging URL.

- [ ] **Step 7: Commit only Task 5 files**

```bash
git add .env.example docs/NASAQ26_BACKEND_STAGING_DEPLOYMENT_PLAN.md
git commit -m "docs: prepare Clerk staging configuration handover" -m "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```
