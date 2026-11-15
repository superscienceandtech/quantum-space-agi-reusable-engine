from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROTOTYPE = ROOT / "arc09-ui-prototype"


def test_dashboard_uses_local_mission_api_and_exposes_run_form() -> None:
    html = (PROTOTYPE / "index.html").read_text(encoding="utf-8")
    adapter = PROTOTYPE / "mission-demo.js"

    assert '<form id="mission-demo-form"' in html
    assert 'id="mission-demo-status"' in html
    assert 'id="mission-demo-results"' in html
    assert adapter.is_file()
    script = adapter.read_text(encoding="utf-8")
    assert "authenticatedFetch('/api/v1/missions/destinations')" in script
    assert "authenticatedFetch(" in script
    assert all(
        endpoint in script
        for endpoint in (
            "/api/v1/missions/validate",
            "/api/v1/missions/run",
        )
    )
    assert "/local/mission-run" not in script
    assert "disabled>Validate and run mission</button>" in html


def test_dashboard_requires_clerk_auth_before_mission_requests() -> None:
    html = (PROTOTYPE / "index.html").read_text(encoding="utf-8")
    auth_script = PROTOTYPE / "auth.js"
    adapter = (PROTOTYPE / "mission-demo.js").read_text(encoding="utf-8")

    assert 'id="clerk-sign-in"' in html
    assert 'id="clerk-user-button"' in html
    assert 'id="mission-demo-auth-status"' in html
    assert auth_script.is_file()
    assert html.index('src="auth.js"') < html.index('src="mission-demo.js"')
    assert "await window.nasaqAuth.getToken()" in adapter
    assert "Authorization" in adapter
    assert all(
        endpoint in adapter
        for endpoint in (
            "/api/v1/missions/destinations",
            "/api/v1/missions/validate",
            "/api/v1/missions/run",
        )
    )
    assert "response.status === 401" in adapter
    assert "response.status === 403" in adapter
    assert "localStorage" not in adapter
    assert "sessionStorage" not in adapter
    assert "nasaq-auth:state" in auth_script.read_text(encoding="utf-8")
    assert "disabled>Validate and run mission</button>" in html


def test_dashboard_labels_synthetic_assumptions_and_policy_boundary() -> None:
    html = (PROTOTYPE / "index.html").read_text(encoding="utf-8")

    assert "Synthetic educational profiles only" in html
    assert "resource-policy approval remains pending" in html
    assert "ARC-08 runs after ARC-05" in html
    assert "No fuel estimate" in html


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

        def handle_starttag(
            self,
            tag: str,
            attrs: list[tuple[str, str | None]],
        ) -> None:
            values = dict(attrs)
            if tag == "form" and values.get("id") == "mission-demo-form":
                self.form_page = self.current_page
            host_ids = {
                "mission-demo-results",
                "spacecraft-run-result",
                "resource-run-result",
                "simulation-run-state",
                "report-run-result",
            }
            if values.get("id") in host_ids:
                self.host_pages[values["id"] or ""] = self.current_page
            if tag not in {
                "area",
                "base",
                "br",
                "col",
                "embed",
                "hr",
                "img",
                "input",
                "link",
                "meta",
                "param",
                "source",
                "track",
                "wbr",
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
    form = (
        (PROTOTYPE / "index.html")
        .read_text(encoding="utf-8")
        .split('<form id="mission-demo-form"', maxsplit=1)[1]
        .split("</form>", maxsplit=1)[0]
    )
    assert 'name="destination_profile_id"' in form
    assert 'name="selected_payload_ids"' in form


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


def test_dashboard_mission_adapter_publishes_all_request_states() -> None:
    adapter = (PROTOTYPE / "mission-demo.js").read_text(encoding="utf-8")
    for status in ("empty", "loading", "ready", "error"):
        assert f"'{status}'" in adapter
    assert "result = null" in adapter
    assert "new CustomEvent('mission-demo:state'" in adapter
    assert "render(result)" in adapter
    assert "publishMissionState('ready', result)" in adapter
    assert "publishMissionState('error', null" in adapter
