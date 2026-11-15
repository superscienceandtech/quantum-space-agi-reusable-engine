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

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.in_result = tag == "pre" and dict(attrs).get("id") == "mission-result"

    def handle_endtag(self, tag: str) -> None:
        if tag == "pre":
            self.in_result = False

    def handle_data(self, data: str) -> None:
        if self.in_result:
            self.result_text += data


def render_mission_builder(
    fetch_scenario: dict[str, object],
    *,
    auth_state: dict[str, bool] | None = None,
    submit_mission: bool = False,
    selected_payloads: tuple[str, ...] = (),
    invalid_profile_selection: bool = False,
    duplicate_submission: bool = False,
) -> dict[str, object]:
    chrome = shutil.which("google-chrome")
    if not chrome:
        pytest.skip("Google Chrome is required for mission-demo browser tests.")

    prototype = Path(__file__).resolve().parents[2] / "arc09-ui-prototype"
    auth_state = (
        {"signedIn": True, "configured": True} if auth_state is None else auth_state
    )
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
  window.arc09CapturedRequests = [];
  window.arc09TokenRequestCount = 0;
  window.arc09SubmitMission = {str(submit_mission).lower()};
  window.arc09SelectedPayloads = {json.dumps(list(selected_payloads))};
  window.arc09InvalidProfileSelection = {str(invalid_profile_selection).lower()};
  window.arc09DuplicateSubmission = {str(duplicate_submission).lower()};
  window.fetch = async (url, options = {{}}) => {{
    window.arc09CapturedRequests.push({{
      url,
      authorization: options.headers && options.headers.Authorization
    }});
    const responseIndex = window.arc09CapturedRequests.length - 1;
    const scenario = Array.isArray(window.arc09FetchScenario.responses)
      ? window.arc09FetchScenario.responses[responseIndex]
      : window.arc09FetchScenario;
    if (!scenario) throw new Error('No response scenario configured.');
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
        auth_stub = f"""
<script>
  window.nasaqAuth = {{
    ready: Promise.resolve(),
    getToken: async () => {{
      window.arc09TokenRequestCount += 1;
      return 'test-only-session-token';
    }},
    isSignedIn: () => {str(auth_state["signedIn"]).lower()}
  }};
</script>"""
        html = html.replace('<script src="auth.js"></script>', auth_stub, 1)
        fetch_stub = fetch_stub.replace(
            '<script src="mission-demo.js"></script>',
            '<script src="mission-demo.js"></script>'
            f'<script>window.dispatchEvent(new CustomEvent("nasaq-auth:state", '
            f"{{detail: {json.dumps(auth_state)}}}));</script>",
        )
        html = html.replace('<script src="mission-demo.js"></script>', fetch_stub, 1)
        probe = """
<script>
document.addEventListener('DOMContentLoaded', () => {
  const missionPage = document.getElementById('mission-builder');
  document.querySelectorAll('section[data-page]').forEach(page => {
    page.hidden = page !== missionPage;
  });
  let initialized = false;
  let submitted = false;
  const capture = () => {
    const status = document.getElementById('mission-demo-status');
    if (status && status.textContent.startsWith('Ready.') && !initialized) {
      initialized = true;
      const form = document.getElementById('mission-demo-form');
      if (window.arc09InvalidProfileSelection) {
        const destination = document.getElementById('mission-destination');
        destination.value = 'unlisted-profile';
        destination.dispatchEvent(new Event('change', { bubbles: true }));
      }
      Array.from(form.querySelectorAll(
        'input[name="selected_payload_ids"]'
      )).forEach(input => {
        input.checked = window.arc09SelectedPayloads.includes(input.value);
        input.dispatchEvent(new Event('change', { bubbles: true }));
      });
      if (window.arc09SubmitMission) {
        submitted = true;
        form.dispatchEvent(
          new Event('submit', { bubbles: true, cancelable: true })
        );
        if (window.arc09DuplicateSubmission) {
          form.dispatchEvent(
            new Event('submit', { bubbles: true, cancelable: true })
          );
        }
      }
      setTimeout(capture, 10);
      return;
    }
    if (!status || (status.dataset.tone !== 'error' &&
        ![
          'Ready.',
          'No synthetic educational profiles',
          'Sign in above',
          'Clerk sign-in is not configured.',
          'Simulation complete'
        ]
          .some(prefix => status.textContent.startsWith(prefix)))) {
      setTimeout(capture, 10);
      return;
    }
    const readiness = document.getElementById('mission-demo-readiness');
    const output = document.createElement('pre');
    output.id = 'mission-result';
    output.textContent = JSON.stringify({
      status: {
        text: status.textContent,
        role: status.getAttribute('role'),
        live: status.getAttribute('aria-live')
      },
      destination_disabled: document.getElementById('mission-destination').disabled,
      readiness: readiness && readiness.textContent,
      run_disabled: document.querySelector(
        '#mission-demo-form button[type="submit"]'
      ).disabled,
      controls_disabled: Array.from(document.querySelectorAll(
        '#mission-demo-form input, #mission-demo-form select, ' +
        '#mission-demo-form button'
      )).every(control => control.disabled),
      requests: window.arc09CapturedRequests,
      token_request_count: window.arc09TokenRequestCount,
      results_hidden: document.getElementById('mission-demo-results').hidden,
      results_text: document.getElementById('mission-demo-results').textContent,
      responsive: {
        viewport_width: document.documentElement.clientWidth,
        document_width: document.documentElement.scrollWidth,
        mission_builder_width: missionPage.getBoundingClientRect().width,
        readiness_visible: Boolean(
          readiness && readiness.getBoundingClientRect().height > 0
        )
      },
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
        page.write_text(
            html.replace("  </body>", probe + "  </body>"), encoding="utf-8"
        )
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


def render_auth_controller(enabled: bool) -> dict[str, object]:
    chrome = shutil.which("google-chrome")
    if not chrome:
        pytest.skip("Google Chrome is required for mission-demo browser tests.")

    prototype = Path(__file__).resolve().parents[2] / "arc09-ui-prototype"
    configuration = {
        "enabled": enabled,
        "publishable_key": "pk_test_example",
        "frontend_api_url": "https://clerk.example",
    }
    with tempfile.TemporaryDirectory(prefix="mission-auth-browser-") as temp_dir:
        page_dir = Path(temp_dir)
        shutil.copy2(prototype / "auth.js", page_dir / "auth.js")
        page = page_dir / "index.html"
        page.write_text(
            f"""<!doctype html>
<html><body>
  <div id="clerk-sign-in" hidden></div>
  <div id="clerk-user-button" hidden></div>
  <div id="clerk-auth-status"></div>
  <div id="mission-demo-auth-status"></div>
  <script>
    const configuration = {json.dumps(configuration)};
    window.fetch = async () => ({{
      ok: true,
      json: async () => configuration
    }});
    window.arc09AuthStates = [];
    window.arc09ScriptURLs = [];
    window.__internal_ClerkUICtor = function () {{}};
    window.Clerk = {{
      isSignedIn: false,
      session: null,
      load: async (options) => {{
        window.arc09LoadedClerkUI = Boolean(options.ui.ClerkUI);
      }},
      addListener: (listener) => {{
        window.arc09ClerkListener = listener;
      }},
      mountSignIn: (host) => {{
        host.dataset.mounted = 'sign-in';
      }},
      mountUserButton: (host) => {{
        host.dataset.mounted = 'user-button';
      }}
    }};
    const appendScript = document.head.appendChild.bind(document.head);
    document.head.appendChild = (script) => {{
      if (script.tagName !== 'SCRIPT') return appendScript(script);
      window.arc09ScriptURLs.push(script.src);
      queueMicrotask(() => script.onload());
      return script;
    }};
    window.addEventListener('nasaq-auth:state', (event) => {{
      window.arc09AuthStates.push(event.detail);
    }});
  </script>
  <script src="auth.js"></script>
  <script>
    window.nasaqAuth.ready.then(async () => {{
      const initialState = window.arc09AuthStates[0] || null;
      const signIn = document.getElementById('clerk-sign-in');
      const userButton = document.getElementById('clerk-user-button');
      if (configuration.enabled) {{
        window.Clerk.isSignedIn = true;
        window.Clerk.session = {{
          getToken: async () => 'test-only-session-token'
        }};
        window.arc09ClerkListener();
      }}
      const output = document.createElement('pre');
      output.id = 'mission-result';
      output.textContent = JSON.stringify({{
        initial_state: initialState,
        states: window.arc09AuthStates,
        script_urls: window.arc09ScriptURLs,
        clerk_ui_loaded: Boolean(window.arc09LoadedClerkUI),
        sign_in_mounted: signIn.dataset.mounted || null,
        user_button_mounted: userButton.dataset.mounted || null,
        signed_in: window.nasaqAuth.isSignedIn(),
        token: await window.nasaqAuth.getToken(),
        status: document.getElementById('clerk-auth-status').textContent
      }});
      document.body.appendChild(output);
    }});
  </script>
</body></html>""",
            encoding="utf-8",
        )
        completed = subprocess.run(
            [
                chrome,
                "--headless",
                "--no-sandbox",
                "--disable-gpu",
                "--disable-dev-shm-usage",
                "--virtual-time-budget=1000",
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
            {
                "kind": "json",
                "status": 503,
                "payload": {"error": {"details": [{"field": "", "message": ""}]}},
            },
            "HTTP 503",
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


def test_destination_load_success_keeps_run_disabled_without_payload() -> None:
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
                        "simulation_duration_s": 3600,
                        "time_step_s": 120,
                        "assumptions": ["Synthetic educational test profile."],
                        "classification": "synthetic educational profile",
                    }
                ]
            },
        }
    )
    assert result["status"]["text"].startswith("Ready.")
    assert result["status"]["role"] == "status"
    assert result["status"]["live"] == "polite"
    assert result["destination_disabled"] is False
    assert result["run_disabled"] is True
    assert "Select at least one supported payload" in result["readiness"]
    assert result["requests"] == [
        {
            "url": "/api/v1/missions/destinations",
            "authorization": "Bearer test-only-session-token",
        }
    ]
    assert any("Synthetic test orbit" in label for label in result["option_labels"])


def test_selecting_a_payload_enables_a_valid_mission_run() -> None:
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
                        "simulation_duration_s": 3600,
                        "time_step_s": 120,
                        "assumptions": ["Synthetic educational test profile."],
                        "classification": "synthetic educational profile",
                    }
                ]
            },
        },
        selected_payloads=("imager",),
    )

    assert result["run_disabled"] is False
    assert "Ready to validate" in result["readiness"]


def test_mission_readiness_fits_the_mobile_viewport() -> None:
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
                        "simulation_duration_s": 3600,
                        "time_step_s": 120,
                        "assumptions": ["Synthetic educational test profile."],
                        "classification": "synthetic educational profile",
                    }
                ]
            },
        },
        selected_payloads=("imager",),
    )

    responsive = result["responsive"]
    assert responsive["mission_builder_width"] > 0
    assert responsive["readiness_visible"] is True
    assert responsive["document_width"] <= responsive["viewport_width"]


def test_empty_destination_list_has_a_distinct_empty_state() -> None:
    result = render_mission_builder(
        {"kind": "json", "status": 200, "payload": {"destinations": []}}
    )

    assert result["status"]["text"].startswith(
        "No synthetic educational profiles are available"
    )
    assert result["status"]["role"] == "status"
    assert result["destination_disabled"] is True
    assert result["run_disabled"] is True


def test_invalid_destination_records_are_rejected() -> None:
    result = render_mission_builder(
        {
            "kind": "json",
            "status": 200,
            "payload": {
                "destinations": [
                    {
                        "profile_id": "synthetic-leo-test",
                        "display_name": "Unclassified test profile",
                        "altitude_m": 400000,
                        "simulation_duration_s": 3600,
                        "time_step_s": 120,
                        "assumptions": ["Test profile."],
                        "classification": "real mission",
                    }
                ]
            },
        }
    )

    assert "invalid synthetic destination profile" in result["status"]["text"]
    assert result["status"]["role"] == "alert"
    assert result["destination_disabled"] is True
    assert result["run_disabled"] is True


def test_unlisted_selected_profile_keeps_run_disabled() -> None:
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
                        "simulation_duration_s": 3600,
                        "time_step_s": 120,
                        "assumptions": ["Synthetic educational test profile."],
                        "classification": "synthetic educational profile",
                    }
                ]
            },
        },
        selected_payloads=("imager",),
        invalid_profile_selection=True,
    )

    assert result["run_disabled"] is True
    assert "Select a valid synthetic profile" in result["readiness"]


def test_duplicate_submission_runs_a_mission_once() -> None:
    result = render_mission_builder(
        {
            "responses": [
                {
                    "kind": "json",
                    "status": 200,
                    "payload": {
                        "destinations": [
                            {
                                "profile_id": "synthetic-leo-test",
                                "display_name": "Synthetic test orbit",
                                "altitude_m": 400000,
                                "simulation_duration_s": 3600,
                                "time_step_s": 120,
                                "assumptions": ["Synthetic educational test profile."],
                                "classification": "synthetic educational profile",
                            }
                        ]
                    },
                },
                {"kind": "json", "status": 200, "payload": {"valid": True}},
                {
                    "kind": "json",
                    "status": 503,
                    "payload": {"error": {"message": "Synthetic service unavailable"}},
                },
            ]
        },
        submit_mission=True,
        selected_payloads=("imager",),
        duplicate_submission=True,
    )

    assert sum(
        request["url"] == "/api/v1/missions/validate"
        for request in result["requests"]
    ) == 1
    assert sum(
        request["url"] == "/api/v1/missions/run" for request in result["requests"]
    ) == 1


def test_successful_synthetic_run_displays_returned_result() -> None:
    from quantum_space_agi.mission_demo.service import MissionDemoService

    mission_request = {
        "destination_profile_id": "synthetic-leo-400-km",
        "selected_payload_ids": ["imager"],
    }
    result = MissionDemoService().run(mission_request)
    browser_result = render_mission_builder(
        {
            "responses": [
                {
                    "kind": "json",
                    "status": 200,
                    "payload": {
                        "destinations": [
                            {
                                "profile_id": "synthetic-leo-400-km",
                                "display_name": "Synthetic test orbit",
                                "altitude_m": 400000,
                                "simulation_duration_s": 3600,
                                "time_step_s": 120,
                                "assumptions": ["Synthetic educational test profile."],
                                "classification": "synthetic educational profile",
                            }
                        ]
                    },
                },
                {
                    "kind": "json",
                    "status": 200,
                    "payload": {"valid": True},
                },
                {"kind": "json", "status": 200, "payload": result},
            ]
        },
        submit_mission=True,
        selected_payloads=("imager",),
    )

    assert browser_result["status"]["text"].startswith("Simulation complete")
    assert browser_result["results_hidden"] is False
    assert "Mission run results · synthetic educational output" in browser_result[
        "results_text"
    ]


@pytest.mark.parametrize(
    ("auth_state", "expected_status"),
    [
        ({"signedIn": False, "configured": True}, "Sign in above"),
        (
            {"signedIn": False, "configured": False},
            "Clerk sign-in is not configured",
        ),
    ],
)
def test_mission_controls_remain_disabled_without_a_signed_in_session(
    auth_state: dict[str, bool],
    expected_status: str,
) -> None:
    result = render_mission_builder(
        {"kind": "json", "status": 200, "payload": {"destinations": []}},
        auth_state=auth_state,
    )

    assert result["status"]["text"].startswith(expected_status)
    assert result["destination_disabled"] is True
    assert result["run_disabled"] is True
    assert result["controls_disabled"] is True
    assert result["requests"] == []


@pytest.mark.parametrize(
    ("status_code", "expected_message"),
    [
        (401, "Your sign-in has expired"),
        (403, "Your account is not authorized"),
    ],
)
def test_authenticated_mission_requests_send_tokens_and_handle_auth_errors(
    status_code: int,
    expected_message: str,
) -> None:
    result = render_mission_builder(
        {
            "responses": [
                {
                    "kind": "json",
                    "status": 200,
                    "payload": {
                        "destinations": [
                            {
                                "profile_id": "synthetic-leo-test",
                                "display_name": "Synthetic test orbit",
                                "altitude_m": 400000,
                                "simulation_duration_s": 3600,
                                "time_step_s": 120,
                                "assumptions": ["Synthetic educational test profile."],
                                "classification": "synthetic educational profile",
                            }
                        ]
                    },
                },
                {"kind": "json", "status": 200, "payload": {"valid": True}},
                {
                    "kind": "json",
                    "status": status_code,
                    "payload": {"error": {"message": "Authentication failed"}},
                },
            ]
        },
        submit_mission=True,
        selected_payloads=("imager",),
    )

    assert expected_message in result["status"]["text"]
    assert result["status"]["role"] == "alert"
    assert result["results_hidden"] is True
    assert result["token_request_count"] == 3
    assert [request["url"] for request in result["requests"]] == [
        "/api/v1/missions/destinations",
        "/api/v1/missions/validate",
        "/api/v1/missions/run",
    ]
    assert all(
        request["authorization"] == "Bearer test-only-session-token"
        for request in result["requests"]
    )


def test_auth_controller_fails_closed_when_clerk_is_unconfigured() -> None:
    result = render_auth_controller(enabled=False)

    assert result["initial_state"] == {"signedIn": False, "configured": False}
    assert result["signed_in"] is False
    assert result["token"] is None
    assert result["script_urls"] == []
    assert "not configured" in result["status"]


def test_auth_controller_loads_clerk_sequentially_and_keeps_tokens_in_memory() -> None:
    result = render_auth_controller(enabled=True)

    assert result["initial_state"] == {"signedIn": False, "configured": True}
    assert result["states"] == [
        {"signedIn": False, "configured": True},
        {"signedIn": True, "configured": True},
    ]
    assert result["script_urls"] == [
        "https://clerk.example/npm/@clerk/ui@1/dist/ui.browser.js",
        "https://clerk.example/npm/@clerk/clerk-js@6/dist/clerk.browser.js",
    ]
    assert result["clerk_ui_loaded"] is True
    assert result["sign_in_mounted"] == "sign-in"
    assert result["user_button_mounted"] == "user-button"
    assert result["signed_in"] is True
    assert result["token"] == "test-only-session-token"
