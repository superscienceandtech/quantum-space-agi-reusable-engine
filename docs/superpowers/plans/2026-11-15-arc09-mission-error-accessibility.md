# ARC-09 Mission Builder Error Accessibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace blank local Mission Builder load failures with an actionable accessible error while preserving disabled controls and successful destination loading.

**Architecture:** Keep the fix in the existing local browser adapter. Normalize unsuccessful HTTP, malformed/empty error bodies, and network failures to non-empty user-facing messages; expose failures as alerts and loading/ready states as polite statuses. Exercise the real page in headless Chrome with deterministic fetch responses, without adding an API or changing backend behavior.

**Tech Stack:** Existing vanilla JavaScript prototype, Python 3/pytest, headless Google Chrome, standard-library temporary files and subprocess.

**Spec:** `docs/superpowers/specs/2026-11-15-nasaq26-multi-arc-audit-design.md`, plus the Project Owner's attached requirements under “ARC-09 — Accessibility and Finalization” and “Mission Builder — Error Fix Authorization”.

## Global Constraints

- Preserve all existing modified and untracked files.
- Do not delete, reset, clean, or overwrite user work.
- Do not commit, push, merge, rewrite history, or deploy.
- Keep Dataset Validation and Mission Planning APIs separate.
- Treat ARC-10 v0.2 as draft/non-canonical; preserve the unresolved D-04/D-05 discrepancy and all other governance blockers.
- The local Mission Builder non-JSON error fallback is authorized for investigation and implementation; that authorization does not create or approve a backend endpoint.
- If two snapshots contain conflicting versions of the affected implementation, stop and request Project Owner direction before editing either version.
- No endpoint, backend, contract, or production behavior will be added.
- Run focused ARC-09 and mission-demo tests and the full project suite where practical.
- Record exact commands, checkout/commit, environment, counts, and failures/skips.

## Review Focus

1. A JSON error with `error.message` and/or details must not be replaced by a generic blank status; preserve meaningful service detail in safe text.
2. A non-JSON 404 must not expose the HTML response or leave the status blank; show a useful fallback and keep mission controls disabled.
3. A network rejection, including one with an empty message, must produce a non-empty actionable error.
4. An empty/malformed JSON error object must produce a non-empty fallback and an alert announcement.
5. A successful destination response must render its option, enable controls, and return the status region to polite status semantics.

---

### Task 1: Isolate the implementation worktree

**Files:**
- Create worktree: `/mnt/e/nasa26/nasaq26-arc09-error-worktree`
- Branch: `fix/arc09-mission-error-message`

**Interfaces:**
- Consumes: `develop` at `6a44af34a649a1138cf577b3b16dbaf436c8a203`.
- Produces: an isolated worktree containing the tracked local mission adapter and tests; existing dirty worktrees remain unchanged.

- [ ] **Step 1: Confirm the branch and target path are still unused**

Run:

```bash
git -C /mnt/e/nasa26/nasaq26-develop-worktree branch --list fix/arc09-mission-error-message
test ! -e /mnt/e/nasa26/nasaq26-arc09-error-worktree
```

Expected: no branch match and exit code 0 from `test`.

- [ ] **Step 2: Create the feature worktree without switching or modifying existing trees**

Run:

```bash
git -C /mnt/e/nasa26/nasaq26-develop-worktree worktree add \
  -b fix/arc09-mission-error-message \
  /mnt/e/nasa26/nasaq26-arc09-error-worktree \
  6a44af34a649a1138cf577b3b16dbaf436c8a203
```

Expected: a new worktree based on `develop`; no changes to the five existing worktrees.

- [ ] **Step 3: Verify the new worktree baseline**

Run:

```bash
git -C /mnt/e/nasa26/nasaq26-arc09-error-worktree status --short --branch
git -C /mnt/e/nasa26/nasaq26-arc09-error-worktree rev-parse HEAD
```

Expected: clean branch `fix/arc09-mission-error-message` at the recorded `develop` commit.

### Task 2: Add deterministic browser regressions first

**Files:**
- Create: `tests/mission_demo/test_frontend_error_handling.py`
- Read: `arc09-ui-prototype/index.html`
- Read: `arc09-ui-prototype/mission-demo.js`

**Interfaces:**
- Consumes: the existing `google-chrome` executable and the page's `#mission-demo-status`, `#mission-destination`, and submit button.
- Produces: `render_mission_builder(fetch_scenario) -> dict[str, object]`, a test helper that opens a temporary copy of the real prototype with a deterministic `window.fetch`.

- [ ] **Step 1: Add a temporary-page browser helper**

Add these imports, then add a result parser and browser helper:

```python
import json
import shutil
import subprocess
import tempfile
from html.parser import HTMLParser
from pathlib import Path

import pytest


class ResultParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_result = False
        self.result_text = ""

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        self.in_result = tag == "pre" and dict(attrs).get("id") == "mission-result"

    def handle_endtag(self, tag: str) -> None:
        if tag == "pre":
            self.in_result = False

    def handle_data(self, data: str) -> None:
        if self.in_result:
            self.result_text += data


def render_mission_builder(fetch_scenario: dict[str, object]) -> dict[str, object]:
    chrome = shutil.which("google-chrome")
    if not chrome:
        pytest.skip("Google Chrome is required for mission-demo browser tests.")

    prototype = Path(__file__).resolve().parents[2] / "arc09-ui-prototype"
    with tempfile.TemporaryDirectory(prefix="mission-builder-browser-") as temp_dir:
        page_dir = Path(temp_dir)
        for name in (
            "app.js",
            "charts.js",
            "data.js",
            "index.html",
            "mission-demo.js",
            "mission-demo.css",
            "styles.css",
        ):
            shutil.copy2(prototype / name, page_dir / name)

        page = page_dir / "index.html"
        html = page.read_text(encoding="utf-8")
        fetch_stub = f"""
<script>
  window.arc09FetchScenario = {json.dumps(fetch_scenario)};
  window.fetch = async () => {{
    const scenario = window.arc09FetchScenario;
    if (scenario.kind === 'network') throw new TypeError('');
    return {{
      ok: scenario.status >= 200 && scenario.status < 300,
      status: scenario.status,
      json: async () => {{
        if (scenario.kind === 'non-json') throw new SyntaxError('invalid JSON');
        return scenario.payload;
      }}
    }};
  }};
</script>
<script src="mission-demo.js"></script>"""
        html = html.replace(
            '<script src="mission-demo.js"></script>', fetch_stub, 1
        )
        probe = """
<script>
document.addEventListener('DOMContentLoaded', () => {
  const capture = () => {
    const status = document.getElementById('mission-demo-status');
    if (!status || (status.dataset.tone !== 'error' &&
        !status.textContent.startsWith('Ready.'))) {
      setTimeout(capture, 10);
      return;
    }
    const output = document.createElement('pre');
    output.id = 'mission-result';
    output.textContent = JSON.stringify({
      status: {
        text: status.textContent,
        role: status.getAttribute('role'),
        live: status.getAttribute('aria-live')
      },
      destination_disabled: document.getElementById('mission-destination').disabled,
      run_disabled: document.querySelector(
        '#mission-demo-form button[type="submit"]'
      ).disabled,
      option_labels: Array.from(
        document.getElementById('mission-destination').options,
        option => option.textContent
      )
    });
    document.body.appendChild(output);
  };
  capture();
});
</script>
"""
        page.write_text(html.replace("  </body>", probe + "  </body>"), encoding="utf-8")
        completed = subprocess.run(
            [
                chrome,
                "--headless",
                "--no-sandbox",
                "--disable-gpu",
                "--disable-dev-shm-usage",
                "--window-size=390,844",
                "--virtual-time-budget=1500",
                f"--user-data-dir={page_dir / 'profile'}",
                "--dump-dom",
                page.as_uri(),
            ],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr[-2000:]
        parser = ResultParser()
        parser.feed(completed.stdout)
        assert parser.result_text, completed.stdout[-4000:]
        return json.loads(parser.result_text)
```

The fetch scenarios passed to the helper use this shape:

```python
{
    "kind": "json",
    "status": 503,
    "payload": {"error": {"message": "Destination service unavailable"}},
}
```

For `kind="non-json"`, `json()` rejects with `SyntaxError`; for `kind="network"`, `fetch()` rejects with `TypeError("")`. Run Chrome with a unique temporary profile and parse the `<pre>` result into a dictionary.

- [ ] **Step 2: Write failing tests for HTTP error body variants**

Add this parametrized test:

```python
@pytest.mark.parametrize(
    ("scenario", "expected_text"),
    [
        (
            {
                "kind": "json",
                "status": 503,
                "payload": {"error": {"message": "Destination service unavailable"}},
            },
            "Destination service unavailable",
        ),
        (
            {"kind": "non-json", "status": 404, "payload": None},
            "Could not load synthetic destination profiles",
        ),
        (
            {"kind": "json", "status": 503, "payload": {}},
            "Could not load synthetic destination profiles",
        ),
        (
            {"kind": "json", "status": 503, "payload": {"error": {}}},
            "Could not load synthetic destination profiles",
        ),
        (
            {"kind": "network", "status": 0, "payload": None},
            "Could not load synthetic destination profiles",
        ),
    ],
)
def test_destination_load_failures_show_actionable_alert(
    scenario: dict[str, object],
    expected_text: str,
) -> None:
    result = render_mission_builder(scenario)
    assert expected_text in result["status"]["text"]
    assert result["status"]["role"] == "alert"
    assert result["status"]["live"] == "assertive"
    assert result["destination_disabled"] is True
    assert result["run_disabled"] is True
```

- [ ] **Step 3: Write a failing successful-load regression**

Add:

```python
def test_destination_load_success_restores_status_and_enables_controls() -> None:
    result = render_mission_builder(
        {
            "kind": "json",
            "status": 200,
            "payload": {
                "destinations": [
                    {
                        "profile_id": "synthetic-leo-test",
                        "display_name": "Synthetic test orbit",
                        "altitude_m": 400000,
                    }
                ]
            },
        }
    )
    assert result["status"]["text"].startswith("Ready.")
    assert result["status"]["role"] == "status"
    assert result["status"]["live"] == "polite"
    assert result["destination_disabled"] is False
    assert result["run_disabled"] is False
    assert "Synthetic test orbit" in result["option_labels"]
```

- [ ] **Step 4: Run the new tests and confirm the expected failure**

Run:

```bash
cd /mnt/e/nasa26/nasaq26-arc09-error-worktree
/home/yousuf/.copilot/session-state/f342f789-70aa-4c5d-8252-c96168f9f1ba/files/nasaq26-develop-worktree-venv/bin/python -m pytest -q tests/mission_demo/test_frontend_error_handling.py
```

Expected: failures show that error text/semantics are absent or non-actionable; the successful-loading test should pass if existing behavior already meets its assertions.

### Task 3: Implement non-empty accessible error reporting

**Files:**
- Modify: `arc09-ui-prototype/mission-demo.js`
- Test: `tests/mission_demo/test_frontend_error_handling.py`

**Interfaces:**
- Consumes: `responseJson(response)`, `loadDestinations()`, and the existing status element.
- Produces: the same local-only destination loading flow, with errors rendered as non-empty alerts and loading/ready states rendered as polite statuses.

- [ ] **Step 1: Add a focused fallback message**

Use the user-facing fallback:

```javascript
const destinationLoadFallback =
  'Could not load synthetic destination profiles. Check that the local mission service is running and try again.';
```

- [ ] **Step 2: Preserve meaningful JSON service errors and reject empty errors**

Keep existing JSON `error.message` and `error.details` handling. When a non-OK response has no non-empty message/details (including malformed JSON, `{}`, and `{error:{}}`), throw an `Error` with `HTTP ${response.status}` as its detail. Never include a non-JSON HTML response body in the user-facing text.

- [ ] **Step 3: Normalize network and empty-message failures**

In the `loadDestinations()` catch path, use the fallback if the caught value is not an `Error` or its trimmed message is empty. For a non-empty detail, use this exact contextual form:

```javascript
`Could not load synthetic destination profiles: ${detail}. Check that the local mission service is running and try again.`
```

- [ ] **Step 4: Set status semantics according to state**

Update `setStatus(message, tone)` to set semantics before replacing status text:

```javascript
const isError = tone === 'error';
status.setAttribute('role', isError ? 'alert' : 'status');
status.setAttribute('aria-live', isError ? 'assertive' : 'polite');
```

Keep existing `data-tone` behavior and do not enable either mission control on load failure.

- [ ] **Step 5: Run the focused browser tests**

Run:

```bash
cd /mnt/e/nasa26/nasaq26-arc09-error-worktree
/home/yousuf/.copilot/session-state/f342f789-70aa-4c5d-8252-c96168f9f1ba/files/nasaq26-develop-worktree-venv/bin/python -m pytest -q tests/mission_demo/test_frontend_error_handling.py
```

Expected: all six error and successful-load scenarios pass.

### Task 4: Verify regressions and update evidence reports

**Files:**
- Test: `tests/mission_demo/test_frontend_error_handling.py`
- Verify: `arc09-ui-prototype/mission-demo.js`
- Modify in the active develop worktree only after the feature-worktree tests pass:
  - `docs/NASAQ26_ARC09_ACCESSIBILITY_AUDIT.md`
  - `docs/NASAQ26_ARC09_FINAL_QA_REPORT.md`
  - `docs/NASAQ26_ARC09_HANDOVER.md`

**Interfaces:**
- Consumes: verified test output and the exact implementation worktree/commit.
- Produces: updated reports distinguishing fixed local error behavior, still-untested assistive technology, handover acceptance, and production/API authorization.

- [ ] **Step 1: Run mission-demo tests**

Run:

```bash
cd /mnt/e/nasa26/nasaq26-arc09-error-worktree
/home/yousuf/.copilot/session-state/f342f789-70aa-4c5d-8252-c96168f9f1ba/files/nasaq26-develop-worktree-venv/bin/python -m pytest -q tests/mission_demo
```

Expected: all mission-demo tests pass.

- [ ] **Step 2: Run the full suite**

Run:

```bash
cd /mnt/e/nasa26/nasaq26-arc09-error-worktree
/home/yousuf/.copilot/session-state/f342f789-70aa-4c5d-8252-c96168f9f1ba/files/nasaq26-develop-worktree-venv/bin/python -m pytest -q --showlocals
```

Expected: command exits 0. Record actual passed/failed/skipped counts; do not infer them from earlier runs.

- [ ] **Step 3: Reproduce the static-server failure in Chrome**

Run the prototype from the feature worktree with a temporary static-only server and open Mission Builder. Verify the resulting status contains a non-empty actionable message, has `role="alert"` and `aria-live="assertive"`, and both the destination selector and submit control remain disabled. Confirm the HTML 404 body is not displayed. Stop only the specific temporary server process started for this test.

- [ ] **Step 4: Update the three QA reports**

Record:

- The exact file/behavior changed and feature branch/worktree path.
- JSON error, non-JSON 404, network failure, empty-error, and successful-load test results.
- Whether a supported screen reader or axe scan was available; retain `NOT TESTED` when not executed.
- The Mission Builder finding as `FIXED` for the local frontend fallback only.
- Handover acceptance as `PENDING`; do not infer contributor acceptance.
- ARC-10 and production API implementation as separate and still blocked as stated in the design.

- [ ] **Step 5: Verify report and repository hygiene**

Run:

```bash
git -C /mnt/e/nasa26/nasaq26-arc09-error-worktree diff --check
git -C /mnt/e/nasa26/nasaq26-develop-worktree diff --check
git -C /mnt/e/nasa26/nasaq26-develop-worktree status --short --branch
git -C /mnt/e/nasa26/nasaq26-arc09-error-worktree status --short --branch
```

Expected: whitespace checks pass; all pre-existing worktree files remain present; no commit, merge, push, or deployment occurs. Include both statuses in the handover.

## Completion gate

This subproject is complete only when all six browser scenarios pass, the mission-demo and full suites have recorded results, the static-server error is verified in Chrome, the three reports are updated, and the final two-worktree status is reported. Screen-reader testing and formal ARC-09/Project Owner handover acceptance remain separate closure gates if unavailable or pending.
