# Runtime and Dashboard Completion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Install and run the local mission app from this `develop` worktree without `PYTHONPATH`, and populate its spacecraft, resource, simulation, and report views only from actual local mission API responses.

**Architecture:** Keep the existing setuptools `src` package and FastAPI API. Give each checkout its own editable-install environment and assert the imported module points into this checkout. Move the current mission form into Mission Builder, publish a small browser-memory mission state event, and render the latest API response in the other pages; do not extend backend APIs or infer absent data.

**Tech Stack:** Python 3.11+, setuptools, TOML, pytest, FastAPI, HTML/CSS/JavaScript, browser smoke testing.

**Spec:** [2026-11-15-runtime-dashboard-completion-design.md](../specs/2026-11-15-runtime-dashboard-completion-design.md)

## Global Constraints

- The application remains an educational prototype. Reuse the current ARC-05 simulator, ARC-08 evaluator, mission API, and ARC-09 visual shell. Do not invent physical spacecraft values, mission eligibility, NASA data, or capabilities the API does not provide.
- Document one virtual environment per checkout/worktree and install the editable project with that environment's Python (`python -m pip install -e ".[api]"`).
- Preserve all existing `quantum_space_agi` subpackages and optional dependency groups. Do not rename the distribution or add a runtime bootstrap that manipulates `sys.path`.
- Keep the latest successful `/api/v1/missions/run` response in browser memory and share it with the other views. Do not persist it across reloads. Starting another run or encountering an error clears the prior result so a stale run cannot be mistaken for the current one. Until a successful run exists, each data-dependent page shows a clear empty state.
- Spacecraft Configuration shows only the returned spacecraft profile ID and selected payload IDs. Label mass, dimensions, propulsion, fuel, capacity, power, and other physical vehicle properties unavailable.
- Resource Dashboard renders the actual ARC-08 evaluator version, scenario, abstract-unit totals, violations, and warning. Mark policy approval pending; describe feasibility only as the result of that educational scenario.
- Mission Comparison & Report renders a report for the latest actual run. The API has no history or comparison endpoint, so cross-mission comparison is explicitly labeled unavailable rather than simulated from sample data.
- Retain the existing visual system and accessible navigation. Do not change unrelated ARC-09 illustrative charts or archived materials.

## Review Focus

- If destination loading returns an error or an empty list, Mission Builder must remain disabled and show the API error instead of offering fabricated choices. (Task 4 browser check: verify disabled controls and visible error for both responses.)
- If the user submits with no payload selected, no run request may occur and an actionable validation message must appear. (Task 2 test: `test_mission_builder_owns_form_and_views_have_result_hosts`; Task 4 browser check: submit with no payload and verify no `/run` request.)
- If validation or mission execution fails after a prior successful run, all result views must clear that run and show the current error/empty state. (Task 4 browser check: intercept the next run after success and verify all response-backed panels clear.)
- If the run response is missing trajectory arrays or contains malformed/non-finite state data, the dashboard must not render a partial or stale result as current. (Task 4 browser check: return a malformed trajectory response and verify the error state and absence of partial results.)
- If a user navigates to data views before the first run, while a run is pending, or after a page reload, the views must distinguish empty/loading from actual API data. (Task 4 browser check: navigate each data view through each state.)

---

## File Structure

- `pyproject.toml`: explicitly discover only real `quantum_space_agi` packages beneath `src`; preserve the existing distribution and optional dependencies.
- `README.md`: document per-checkout virtual environments, same-interpreter editable install, import-path verification, and startup; remove the remaining `PYTHONPATH=src` startup example.
- `docs/NASAQ26_LOCAL_EDUCATIONAL_DEMO.md`: add platform-specific isolated environment and no-`PYTHONPATH` verification instructions.
- `tests/test_packaging.py`: verify setuptools package discovery settings and continued inclusion of core, simulation, ML, and mission-demo packages.
- `arc09-ui-prototype/index.html`: put the live form under Mission Builder and provide data hosts/empty states for Spacecraft, Resources, Simulation, and Report.
- `arc09-ui-prototype/mission-demo.js`: publish loading/error/success states for the actual API request and render the trajectory into Simulation & Results.
- `arc09-ui-prototype/app.js`: consume mission state and render actual payload/resource/report fields into their corresponding views.
- `arc09-ui-prototype/mission-demo.css`: style the actual result panels and empty/unavailable states using the existing visual system.
- `tests/mission_demo/test_dashboard.py`: verify form location, page hosts, scientific labels, comparison unavailability, and live API state wiring.

## Task 1: Make Editable Installation Worktree-Specific

**Files:**
- Modify: `pyproject.toml`
- Modify: `README.md`
- Modify: `docs/NASAQ26_LOCAL_EDUCATIONAL_DEMO.md`
- Test: `tests/test_packaging.py`

**Interfaces:**
- Consumes: the existing setuptools `src` layout and `quantum_space_agi` package tree.
- Produces: `[tool.setuptools.packages.find]` with `where = ["src"]`, `include = ["quantum_space_agi*"]`, and `namespaces = false`; docs install and verify with the same Python executable that launches the server.

- [ ] **Step 1: Write the failing discovery test**

Add `tests/test_packaging.py`:

```python
from __future__ import annotations

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_setuptools_discovers_only_real_quantum_space_agi_packages() -> None:
    config = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    discovery = config["tool"]["setuptools"]["packages"]["find"]

    assert discovery == {
        "where": ["src"],
        "include": ["quantum_space_agi*"],
        "namespaces": False,
    }

    for package in (
        "quantum_space_agi",
        "quantum_space_agi.simulation",
        "quantum_space_agi.ml",
        "quantum_space_agi.mission_demo",
    ):
        path = ROOT / "src" / Path(*package.split("."))
        assert (path / "__init__.py").is_file()
```

- [ ] **Step 2: Run the test and verify it fails on the missing explicit include**

Run: `python -m pytest tests/test_packaging.py::test_setuptools_discovers_only_real_quantum_space_agi_packages -q`

Expected: FAIL because the current discovery configuration does not set `include` and `namespaces`.

- [ ] **Step 3: Add explicit setuptools discovery**

Change the existing stanza in `pyproject.toml` to:

```toml
[tool.setuptools.packages.find]
where = ["src"]
include = ["quantum_space_agi*"]
namespaces = false
```

- [ ] **Step 4: Document isolated installation and import verification**

Update the README and local-demo instructions to create one virtual environment per checkout, install through that environment's Python, and verify the import before launching. Use `.[api]` in user-facing run instructions and `.[api,test]` only in the verification environment. Remove the obsolete README example that starts the server with `PYTHONPATH=src`. Linux/macOS:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[api,test]"
.venv/bin/python -c "from pathlib import Path; import quantum_space_agi; expected = (Path.cwd() / 'src/quantum_space_agi/__init__.py').resolve(); actual = Path(quantum_space_agi.__file__).resolve(); assert actual == expected, f'{actual} is not {expected}'; print(actual)"
.venv/bin/python -m quantum_space_agi.mission_demo.server
```

Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[api,test]"
.venv\Scripts\python.exe -c "from pathlib import Path; import quantum_space_agi; expected=(Path.cwd() / 'src/quantum_space_agi/__init__.py').resolve(); actual=Path(quantum_space_agi.__file__).resolve(); assert actual == expected, f'{actual} is not {expected}'; print(actual)"
.venv\Scripts\python.exe -m quantum_space_agi.mission_demo.server
```

Clarify that the verification and server commands use the same environment. Do not recommend `PYTHONPATH` or a bare `pip` command.

- [ ] **Step 5: Run discovery, build, and documentation checks**

Run:

```bash
python -m pytest tests/test_packaging.py -q
python -m build
python -c "from pathlib import Path; from zipfile import ZipFile; wheel = next(Path('dist').glob('*.whl')); names = set(ZipFile(wheel).namelist()); expected = {'quantum_space_agi/__init__.py', 'quantum_space_agi/simulation/__init__.py', 'quantum_space_agi/ml/__init__.py', 'quantum_space_agi/mission_demo/__init__.py'}; assert expected <= names, expected - names"
git diff --check
```

Expected: the test passes; the wheel and source distribution build; no whitespace errors.

- [ ] **Step 6: Commit the verified package/runtime documentation changes**

```bash
git add pyproject.toml README.md docs/NASAQ26_LOCAL_EDUCATIONAL_DEMO.md tests/test_packaging.py
git commit -m "fix: isolate mission demo editable installation"
```

## Task 2: Put Mission Configuration in Mission Builder

**Files:**
- Modify: `arc09-ui-prototype/index.html`
- Modify: `tests/mission_demo/test_dashboard.py`

**Interfaces:**
- Consumes: the existing `mission-demo-form`, destination selector, selected-payload inputs, status element, and API route names.
- Produces: the mission form under `data-page="mission-builder"`; `mission-demo-results` under `data-page="simulation"`; stable page-host IDs `spacecraft-run-result`, `resource-run-result`, `simulation-run-state`, and `report-run-result`.

- [ ] **Step 1: Add a failing DOM contract test**

Add a test in `tests/mission_demo/test_dashboard.py`:

```python
def test_mission_builder_owns_form_and_views_have_result_hosts() -> None:
    from html.parser import HTMLParser

    class PageOwnershipParser(HTMLParser):
        def __init__(self) -> None:
            super().__init__()
            self.element_stack: list[tuple[str, str | None]] = []
            self.form_page: str | None = None
            self.host_pages: dict[str, str] = {}

        @property
        def current_page(self) -> str | None:
            return next(
                (page for _, page in reversed(self.element_stack) if page),
                None,
            )

        def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            values = dict(attrs)
            if tag == "form" and values.get("id") == "mission-demo-form":
                self.form_page = self.current_page
            if values.get("id") in {
                "mission-demo-results",
                "spacecraft-run-result",
                "resource-run-result",
                "simulation-run-state",
                "report-run-result",
            }:
                self.host_pages[values["id"] or ""] = self.current_page
            if tag not in {
                "area", "base", "br", "col", "embed", "hr", "img",
                "input", "link", "meta", "param", "source", "track", "wbr",
            }:
                self.element_stack.append((tag, values.get("data-page")))

        def handle_endtag(self, tag: str) -> None:
            for index in range(len(self.element_stack) - 1, -1, -1):
                if self.element_stack[index][0] == tag:
                    del self.element_stack[index:]
                    return

    parser = PageOwnershipParser()
    parser.feed((PROTOTYPE / "index.html").read_text(encoding="utf-8"))

    assert parser.form_page == "mission-builder"
    assert parser.host_pages == {
        "mission-demo-results": "simulation",
        "spacecraft-run-result": "spacecraft",
        "resource-run-result": "resources",
        "simulation-run-state": "simulation",
        "report-run-result": "comparison",
    }
    form = (PROTOTYPE / "index.html").read_text(encoding="utf-8").split(
        '<form id="mission-demo-form"', maxsplit=1
    )[1].split("</form>", maxsplit=1)[0]
    assert 'name="destination_profile_id"' in form
    assert 'name="selected_payload_ids"' in form
```

- [ ] **Step 2: Run the test and verify it fails because the form is currently on Dashboard**

Run: `python -m pytest tests/mission_demo/test_dashboard.py::test_mission_builder_owns_form_and_views_have_result_hosts -q`

Expected: FAIL with `parser.form_page == "mission-builder"` because the current form is inside the dashboard page.

- [ ] **Step 3: Move the existing form without changing its request contract**

Move the complete `<section class="mission-demo">` from `#dashboard` into `#mission-builder`. Keep its IDs, checkbox names, selector name, submit behavior, and educational warning unchanged. Replace the Mission Builder placeholder with the form and add its page title and a short workflow description.

- [ ] **Step 4: Move the result container and add typed page hosts**

Replace only the four requested placeholder panels:

```html
<section id="spacecraft-run-result" aria-live="polite"></section>
<section id="resource-run-result" aria-live="polite"></section>
<p id="simulation-run-state" role="status" aria-live="polite"></p>
<section id="mission-demo-results" aria-live="polite" aria-label="Educational mission results" hidden></section>
<section id="report-run-result" aria-live="polite"></section>
```

Place these respectively in the Spacecraft, Resources, Simulation, and Comparison pages. Keep the existing nav IDs and `data-page` values. Leave unrelated Dashboard charts and samples unchanged and labeled.

- [ ] **Step 5: Run dashboard/API regression tests**

Run: `python -m pytest tests/mission_demo/test_dashboard.py tests/mission_demo/test_api.py -q`

Expected: PASS; the existing API test still confirms the dashboard is served and the mission form exists.

- [ ] **Step 6: Commit the verified page structure**

```bash
git add arc09-ui-prototype/index.html tests/mission_demo/test_dashboard.py
git commit -m "feat: place mission workflow in its own dashboard view"
```

## Task 3: Share Actual Run State Across the Dashboard Views

**Files:**
- Modify: `arc09-ui-prototype/mission-demo.js`
- Modify: `arc09-ui-prototype/app.js`
- Modify: `arc09-ui-prototype/mission-demo.css`
- Modify: `README.md`
- Modify: `docs/NASAQ26_LOCAL_EDUCATIONAL_DEMO.md`
- Modify: `tests/mission_demo/test_dashboard.py`

**Interfaces:**
- Consumes: the Task 2 result-host IDs and the existing run-response fields from `MissionRunResponseDTO`.
- Produces: a `mission-demo:state` window event with detail `{status, result, message}`, where `status` is `empty`, `loading`, `ready`, or `error`; `result` is the latest actual response or `null`; `message` is an error string or `null`.

- [ ] **Step 1: Add failing state-contract tests**

Add a dashboard test:

```python
def test_dashboard_declares_live_result_pages_and_unavailable_capabilities() -> None:
    html = (PROTOTYPE / "index.html").read_text(encoding="utf-8")
    for text in ("Spacecraft configuration", "Educational resource evaluation"):
        assert text in html

    app = (PROTOTYPE / "app.js").read_text(encoding="utf-8")
    adapter = (PROTOTYPE / "mission-demo.js").read_text(encoding="utf-8")
    assert "mission-demo:state" in app
    assert "mission-demo:state" in adapter
    for text in (
        "Selected payloads",
        "physical spacecraft properties are unavailable",
        "ARC-08 educational evaluator",
        "abstract units",
        "policy approval pending",
    ):
        assert text in app
    assert "Cross-mission comparison unavailable" in app
    assert "policy_approval_status" in app
    assert "resource_totals" in app
    assert "trajectory" in adapter
```

Add focused source-contract checks for request-state publication and clearing the result before a new request:

```python
def test_dashboard_mission_adapter_publishes_all_request_states() -> None:
    adapter = (PROTOTYPE / "mission-demo.js").read_text(encoding="utf-8")
    for status in ("empty", "loading", "ready", "error"):
        assert f"'{status}'" in adapter
    assert "result = null" in adapter
    assert "new CustomEvent('mission-demo:state'" in adapter
    assert "render(result)" in adapter
    assert "publishMissionState('ready', result)" in adapter
    assert "publishMissionState('error', null" in adapter
```

- [ ] **Step 2: Run the new tests and verify they fail for missing shared rendering**

Run: `python -m pytest tests/mission_demo/test_dashboard.py -q`

Expected: FAIL because the requested page labels and shared mission-state event are not yet present.

- [ ] **Step 3: Publish request lifecycle state from `mission-demo.js`**

Add one helper that emits:

```javascript
function publishMissionState(status, result = null, message = null) {
  window.dispatchEvent(new CustomEvent('mission-demo:state', {
    detail: { status, result, message }
  }));
}
```

Publish `loading` before destination loading and before each validation/run sequence; publish `empty` after destinations load successfully but before a mission run; publish `ready` only after response JSON has passed the existing renderer's trajectory validation and rendered successfully; publish `error` from `showError`. Clear `results` and publish `result: null` on a new run or any error. Do not publish a success state for a malformed payload.

- [ ] **Step 4: Render spacecraft, resources, and report from the actual response**

In `app.js`, initialize all three result hosts with an empty state and listen for `mission-demo:state`. Use DOM construction and `textContent`, not response-derived `innerHTML`.

For `ready`:
- Spacecraft page: show `mission.spacecraft_profile_id`, the actual selected payload IDs, and a visible unavailable list for physical vehicle properties.
- Resource page: show evaluator version/scenario, `policy_approval_status`, warning, `resource_totals` with labels explicitly marked abstract units, actual violations, and feasibility described only as the evaluator's demo-scenario result.
- Report page: show the latest run's destination, payload IDs, ARC-05 integrator/reference frame/state count, and ARC-08 evaluator status.

For every report state, include the exact text `Cross-mission comparison unavailable: the local API has no comparison or mission-history endpoint.` For `loading` or `error`, clear all prior result panels and render a status/error message, including in `simulation-run-state`. For `empty`, render a neutral instruction to run a mission and retain the comparison-unavailable label. Do not read sample dashboard data from `data.js`.

- [ ] **Step 5: Keep ARC-05 trajectory output in Simulation & Results**

Retain the existing SVG trajectory and accessible state table, but ensure `mission-demo-results` is now under `#simulation`. Render response-derived model metadata and diagnostics only from `trajectory.model` and `trajectory.diagnostics`; include maximum energy and angular-momentum drift with the response's declared units. Keep the synthetic educational model warning next to the plot/table.

- [ ] **Step 6: Add focused panel styles**

Add styles to `mission-demo.css` for the actual result summary cards, unit/warning labels, violations, and empty/error/loading states. Reuse existing colors, borders, spacing, and typography; do not alter the unrelated prototype chart styles.

- [ ] **Step 7: Run dashboard and mission regression tests**

Run: `python -m pytest tests/mission_demo -q`

Expected: PASS across API response, page structure, mission form validation, and response labels.

- [ ] **Step 8: Commit the verified cross-view rendering**

```bash
git add arc09-ui-prototype/index.html arc09-ui-prototype/app.js arc09-ui-prototype/mission-demo.js arc09-ui-prototype/mission-demo.css README.md docs/NASAQ26_LOCAL_EDUCATIONAL_DEMO.md tests/mission_demo/test_dashboard.py
git commit -m "feat: render mission results across dashboard views"
```

## Task 4: Verify Installed Runtime and Browser Workflow

**Files:**
- Modify only if verification exposes a defect in the files from Tasks 1-3.

**Interfaces:**
- Consumes: the editable package configuration and `mission-demo:state` event.
- Produces: evidence that the current worktree imports and starts normally, and that actual API values propagate to all requested views.

- [ ] **Step 1: Install the current checkout into a clean, checkout-specific environment**

From the develop worktree, Create a fresh virtual environment at `.venv` only if it does not already exist. Install all project extras needed for the non-notebook suite and quality/build checks using its own Python:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[api,dev,quality,notebooks,test]"
.venv/bin/python -c "from pathlib import Path; import quantum_space_agi; expected = (Path.cwd() / 'src/quantum_space_agi/__init__.py').resolve(); actual = Path(quantum_space_agi.__file__).resolve(); assert actual == expected, f'{actual} is not {expected}'; print(actual)"
```

Expected: the printed path is under `/mnt/e/nasa26/nasaq26-develop-worktree/src/quantum_space_agi`, not the original or integration checkout.

- [ ] **Step 2: Start the documented server without `PYTHONPATH`**

Check whether `127.0.0.1:8765` is already occupied. Do not stop a process that predates this task; if it is occupied, ask the owner before stopping it. Once the port is available, run `.venv/bin/python -m quantum_space_agi.mission_demo.server` from the develop worktree, with no `PYTHONPATH` override. Verify `GET http://127.0.0.1:8765/health` returns `{"status":"ok"}` and `/` returns the dashboard. Stop only the server process started for this test after browser verification.

- [ ] **Step 3: Verify empty, loading, and API-error states in the browser**

Open the dashboard. Before a run, visit Spacecraft Configuration, Resource Dashboard, Simulation & Results, and Mission Comparison & Report; each must show an empty state and the comparison page must label comparison unavailable. Return to Mission Builder, submit with no payload selected, and verify an actionable error appears without an `/api/v1/missions/run` request. Start a valid run and verify the loading state and disabled submit button.

- [ ] **Step 4: Run an actual mission and verify all response-backed views**

In Mission Builder, choose a synthetic destination, select at least one payload, and submit. Verify:
- ARC-05 trajectory samples, ECI/RK4 metadata, SVG projection, and state table appear under Simulation & Results.
- ARC-08 evaluator version/scenario, actual abstract totals/violations, and pending policy warning appear under Resource Dashboard.
- The selected payload IDs appear under Spacecraft Configuration, with physical properties marked unavailable.
- The report shows the actual mission summary and comparison unavailable notice.

- [ ] **Step 5: Verify failure and reload behavior after a successful run**

Use browser request interception on a subsequent `/api/v1/missions/run` call to return an API error. Confirm Mission Builder reports it and all result views clear the previous response. Intercept a second run with a successful HTTP status but a malformed trajectory response; confirm no result view publishes partial data. Reload the page and verify all result pages return to their empty state. Intercept the destination request with an empty list and an HTTP error in separate reloads; in both cases confirm the form remains disabled and shows the returned error/state.

- [ ] **Step 6: Run final regression, build, and static checks**

Run:

```bash
.venv/bin/python -m pytest --ignore=tests/simulation/test_arc05_notebooks.py -q
.venv/bin/ruff check src/quantum_space_agi/mission_demo tests/mission_demo tests/test_packaging.py
.venv/bin/ruff format --check src/quantum_space_agi/mission_demo tests/mission_demo tests/test_packaging.py
.venv/bin/python -m build
git diff --check origin/develop..HEAD -- README.md pyproject.toml docs/NASAQ26_LOCAL_EDUCATIONAL_DEMO.md arc09-ui-prototype/index.html arc09-ui-prototype/app.js arc09-ui-prototype/mission-demo.js arc09-ui-prototype/mission-demo.css tests/test_packaging.py tests/mission_demo/test_dashboard.py
```

Expected: tests, scoped quality checks, build, and whitespace check all succeed. Report the notebook suite as excluded, not passed.

- [ ] **Step 7: Commit any verification-driven fix and report evidence**

If a test or browser step exposes a defect, write a regression test first, verify it fails, fix the defect, rerun the task's tests, and commit only after green results. Do not push or force-push.

## Completion

The task is complete when the package import assertion prints the current develop-worktree path; the server starts without `PYTHONPATH`; all four requested views display actual API-backed data or explicit empty/unavailable/error states; the browser smoke workflow succeeds; and the final non-notebook suite/build/scoped checks pass.
