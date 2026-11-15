# ARC-10 Synthetic Execution Evidence

**Execution date:** 2026-11-15, 13:36–13:44 local (+06:00); 07:36–07:44 UTC
**Source:** `/mnt/e/nasa26/nasaq26-develop-worktree`, branch `develop`, HEAD `6a44af34a649a1138cf577b3b16dbaf436c8a203`
**Endpoint:** `http://127.0.0.1:8765`
**Evidence directory:** `/tmp/opencode/arc10_evidence/`
**Nature:** local synthetic educational execution. **No NASA data, production deployment, authentication, or mission feasibility was tested or claimed.**

## 1. Purpose and non-claims

This report records actual HTTP requests and responses executed against the documented local Mission API. It is evidence that the local backend starts, validates, executes ARC-05 + ARC-08, and returns the verified unified result.

It is **not** evidence of:

- production readiness,
- API contract approval,
- scientific or mission feasibility,
- NASA data use,
- authentication/authorization,
- CORS or network security,
- operational deployment,
- Dataset Validation API behavior,
- ARC-10 v0.3/v0.4 conformance.

## 2. Environment

| Item | Value |
|---|---|
| Python | 3.14.7 |
| Fresh venv | `$HOME/.venvs/nasaq26-arc10-verify` |
| Install | `pip install -e ".[api]"` (exit 0) |
| Import assertion | Resolved to `/mnt/e/nasa26/nasaq26-develop-worktree/src/quantum_space_agi/__init__.py` |
| Server command | `"$HOME/.venvs/nasaq26-arc10-verify/bin/python" -m quantum_space_agi.mission_demo.server` |
| Binding | `127.0.0.1:8765` (loopback only) |
| Server banner | `NASAQ26 local educational demo: http://127.0.0.1:8765/` |
| Warning banner | `Synthetic educational inputs only; no NASA data or production deployment.` |

### 2.1 Environment caveat

The ambient Miniconda editable install resolved `quantum_space_agi` to the ARC-03 checkout (`/mnt/e/nasa26/quantum-space-agi-reusable-engine/src/...`), not to this worktree. To avoid testing the wrong checkout:

- The first capture (`01`–`10`) used `PYTHONPATH=src` with the ambient interpreter.
- The documented-venv capture (`11`–`12`) used the fresh venv and the documented command, with the import assertion passing.

Both runs returned byte-identical success bodies (see §5). This is an environment-selection issue, not an application defect. The documented fresh-venv procedure is the correct way to avoid it.

## 3. Request sequence

All requests were sent to `http://127.0.0.1:8765`.

| # | Method | Path | Purpose | Evidence file |
|---:|---|---|---|---|
| 1 | `GET` | `/health` | Process health | `01_health.headers`, `01_health.body` |
| 2 | `GET` | `/api/v1/missions/destinations` | Synthetic profile catalog | `02_destinations.headers`, `02_destinations.body` |
| 3 | `POST` | `/api/v1/missions/validate` | Validate mission request | `03_validate.headers`, `03_validate.body` |
| 4 | `POST` | `/api/v1/missions/run` | Execute mission workflow | `04_run.headers`, `04_run.body` |
| 5 | `POST` | `/api/v1/missions/run` | Invalid destination profile | `05_invalid.headers`, `05_invalid.body` |
| 6 | `POST` | `/api/v1/missions/run` | Malformed JSON | `06_malformed.headers`, `06_malformed.body` |
| 7 | `GET` | `/api/v1/missions/unknown` | Unknown route | `07_unknown.headers`, `07_unknown.body` |
| 8 | `GET` | `/api/v1/missions/run` | GET on POST-only route | `08_method.headers`, `08_method.body` |
| 9 | `POST` | `/api/v1/missions/run` | Unsupported media type | `09_media.headers`, `09_media.body` |
| 10 | `GET` | `/` | Dashboard HTML | `10_dashboard.headers`, `10_dashboard.html` |
| 11 | `GET` | `/health` | Documented-venv repeat | `11_documented_health.headers`, `11_documented_health.body` |
| 12 | `POST` | `/api/v1/missions/run` | Documented-venv repeat | `12_documented_run.headers`, `12_documented_run.body` |

Method checks performed against the same server:

- `POST /health` → `405 method_not_allowed`
- `PUT /api/v1/missions/run` → `405 method_not_allowed`
- `GET /api/v1/missions/validate` → `404 not_found`
- `GET /api/v1/missions/run` → `404 not_found`

Evidence: `server_methods.log`, `method_body.txt`.

## 4. Successful request and response

### 4.1 Request

```http
POST /api/v1/missions/run HTTP/1.1
Host: 127.0.0.1:8765
Content-Type: application/json

{"destination_profile_id":"synthetic-leo-400-km","selected_payload_ids":["relay","imager"]}
```

Payload order in the request was deliberately non-canonical (`relay`, then `imager`) to verify canonicalization.

### 4.2 Response headers

```http
HTTP/1.1 200 OK
date: Sun, 15 Nov 2026 07:36:04 GMT
server: uvicorn
content-length: 8783
content-type: application/json
```

Documented-venv repeat:

```http
HTTP/1.1 200 OK
date: Sun, 15 Nov 2026 07:43:26 GMT
server: uvicorn
content-length: 8783
content-type: application/json
```

### 4.3 Response integrity

| Property | Value |
|---|---|
| Body size | 8,783 bytes |
| SHA-256 | `e2a9e5a59d3106d4d845a72e47b7e4a0b59c56b4c7a9069c16ec770d6874c3b7` |
| First-run vs documented-venv body | **Byte-identical** (`cmp` returned equal) |
| JSON parse | Valid |
| Non-finite numbers | None; all checked values finite |

Health response SHA-256: `a29ee2b15c494311c52521766e44af56a3ad2248e7a8ab465e5206463c13d288` (both runs identical).

### 4.4 Response summary

Top-level keys: `classification`, `limitations`, `mission`, `resource_evaluation`, `trajectory`.

| Section | Verified content |
|---|---|
| `classification` | `"synthetic educational demonstration"` |
| `limitations` | 7 synthetic-profile assumption strings |
| `mission.destination_profile_id` | `"synthetic-leo-400-km"` |
| `mission.destination_display_name` | `"Synthetic LEO profile A"` |
| `mission.spacecraft_profile_id` | `"educational-payload-carrier-v1"` |
| `mission.selected_payload_ids` | `["imager","relay"]` — canonical order despite reversed input |
| `resource_evaluation.status` | `"evaluated"` |
| `resource_evaluation.policy_approval_status` | `"pending"` |
| `resource_evaluation.policy_authority` | `"educational evaluator output only"` |
| `resource_evaluation.result.evaluator_version` | `"educational-mission-evaluator/0.1.0"` |
| `resource_evaluation.result.scenario_id` | `"resource-selection-demo-v1"` |
| `resource_evaluation.result.feasible` | `true` |
| `resource_evaluation.result.violations` | `[]` |
| `resource_evaluation.result.resource_totals` | budget 5, mass 3, power 3, payload slots 2 (abstract units) |
| `resource_evaluation.result.educational_score` | `8` |
| `trajectory.times_s` | 31 values, `0.0` to `3600.0`, 120 s step |
| `trajectory.states` | 31 rows, each 6 finite numbers |
| `trajectory.state_order` | `["x_m","y_m","z_m","vx_mps","vy_mps","vz_mps"]` |
| `trajectory.states[0]` | `[6778137.0, 0.0, 0.0, 0.0, 7668.558175407055, 0.0]` |
| `trajectory.collision_index` | `null` |
| `trajectory.collision_time_s` | `null` |
| `trajectory.collision_state` | `null` |
| `trajectory.model` | ECI, RK4, Earth point-mass Newtonian two-body; s, m, m/s |
| `trajectory.diagnostics` | 9 keys: 7 arrays of length 31, 2 scalar maxima |

The exact body is stored at `/tmp/opencode/arc10_evidence/04_run.body` and `/tmp/opencode/arc10_evidence/12_documented_run.body`.

## 5. Profile catalog response

`GET /api/v1/missions/destinations` → `200`, 1,839 bytes, three profiles:

| Profile ID | Display name | Altitude |
|---|---|---:|
| `synthetic-leo-400-km` | Synthetic LEO profile A | 400,000 m |
| `synthetic-leo-800-km` | Synthetic LEO profile B | 800,000 m |
| `synthetic-earth-orbit-2000-km` | Synthetic Earth-orbit profile C | 2,000,000 m |

All three carry:

- `classification: "synthetic educational profile"`,
- 3,600 s duration,
- 120 s time step,
- assumptions stating they are synthetic, not real NASA mission targets, with no atmosphere/thrust/spacecraft mass/mission-success modeling.

## 6. Validation response

`POST /api/v1/missions/validate` → `200`, 226 bytes:

```json
{"valid":true,"mission":{"destination_profile_id":"synthetic-leo-400-km","destination_display_name":"Synthetic LEO profile A","spacecraft_profile_id":"educational-payload-carrier-v1","selected_payload_ids":["imager","relay"]}}
```

This endpoint validated the request and returned the canonical mission summary. It did not execute a simulation; that was verified by source (`api.py:158-160`) and tests (`test_api.py:64-81`).

## 7. Error responses

| Case | Request | Status | Body |
|---|---|---|---|
| Unsupported profile | `{"destination_profile_id":"mars","selected_payload_ids":["relay"]}` | `422 Unprocessable Content` | `{"error":{"code":"validation_error","message":"The mission request did not pass validation.","details":[{"field":"destination_profile_id","message":"Value error, destination_profile_id is not a supported profile"}]}}` |
| Malformed JSON | `{` | `400 Bad Request` | `{"error":{"code":"malformed_json","message":"The request body is not valid JSON.","details":[]}}` |
| Unknown route | `GET /api/v1/missions/unknown` | `404 Not Found` | `{"error":{"code":"not_found","message":"Not Found","details":[]}}` |
| Unsupported media type | `POST` with `Content-Type: text/plain` | `415 Unsupported Media Type` | `{"error":{"code":"unsupported_media_type","message":"Send mission requests as application/json.","details":[]}}` |
| Unsupported method | `POST /health` | `405 Method Not Allowed` | `{"error":{"code":"method_not_allowed","message":"Method Not Allowed","details":[]}}` |
| Unsupported method | `PUT /api/v1/missions/run` | `405 Method Not Allowed` | Same `method_not_allowed` envelope |
| GET on POST-only route | `GET /api/v1/missions/run` | **`404 Not Found`** | `{"error":{"code":"not_found","message":"Not Found","details":[]}}` |

The GET result is a confirmed nuance: the catch-all static mount handles unmatched GET requests before Starlette can raise a 405 for the POST-only mission path. The local demo doc's broad statement that unsupported methods return 405 is therefore not exact for GET on those routes.

No `500` was observed in the successful or validation-error paths. The `500 mission_run_failed` path is covered by tests (`test_api.py:176-202`), not by this execution.

## 8. Dashboard response

`GET /` → `200`, `text/html; charset=utf-8`, 16,156 bytes, ETag `"caf6baf2696e5130cff2a8bf6bd1388f"`. The dashboard HTML was served from `arc09-ui-prototype/`. This verifies static serving, not interactive browser behavior. Interactive behavior is covered separately by the browser-backed tests (18 passed with Chrome).

## 9. Server logs

Successful documented run (`server_documented_run.log`):

```text
INFO:     Started server process [551740]
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8765 (Press CTRL+C to quit)
NASAQ26 local educational demo: http://127.0.0.1:8765/
Synthetic educational inputs only; no NASA data or production deployment.
INFO:     127.0.0.1:40060 - "POST /api/v1/missions/run HTTP/1.1" 200 OK
INFO:     Shutting down
INFO:     Application shutdown complete.
```

Method checks (`server_methods.log`):

```text
INFO:     127.0.0.1:36510 - "GET /api/v1/missions/validate HTTP/1.1" 404 Not Found
INFO:     127.0.0.1:36514 - "GET /api/v1/missions/run HTTP/1.1" 404 Not Found
INFO:     127.0.0.1:36526 - "POST /health HTTP/1.1" 405 Method Not Allowed
INFO:     127.0.0.1:36540 - "PUT /api/v1/missions/run HTTP/1.1" 405 Method Not Allowed
```

`server2.log` contains an `address already in use` error from an extra start attempt while the first server was still bound. That is a harness sequencing artifact, not an application failure. The successful startup and requests are recorded in the other logs.

## 10. What this evidence establishes

1. The documented local backend can be installed in a fresh venv and started on loopback.
2. The documented destination, validate, and run requests execute against the actual implementation.
3. The run response is the actual ARC-05 + ARC-08 composition, not a fixture.
4. Request canonicalization, strict validation, finite numeric output, and the documented error envelope behave as the source/tests describe.
5. The response is reproducible: two independent runs produced byte-identical bodies.
6. The local demo is explicitly synthetic and does not claim mission feasibility or scientific eligibility.

## 11. What remains unverified

| Item | Reason |
|---|---|
| Formal contract conformance | No approved contract; v0.3/v0.4 documents not found. |
| Production deployment | No production environment or authorization. |
| Authentication/authorization/CORS | Not implemented/tested in the local demo. |
| Dataset Validation API | Separate API; no route in this demo. |
| `scientific_eligibility` | Not part of the Mission API; must not be inferred from structural validation. |
| Collision threshold/method in response | Omitted from the unified result; confirmed data loss. |
| Human usability and cross-browser support | Browser tests exist, but no human acceptance or multi-browser certification. |
| Production acceptance | No authorized acceptance authority. |

## 12. Verdict

**Synthetic execution: VERIFIED AGAINST IMPLEMENTATION (local educational demo).**
**Production acceptance: BLOCKED / NOT APPROVED.**
**Overall: B — PARTIALLY VERIFIED.**
