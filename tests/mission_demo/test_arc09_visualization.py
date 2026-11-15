import json
import shutil
import subprocess
import tempfile
from html.parser import HTMLParser
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
PROTOTYPE = ROOT / "arc09-ui-prototype"


class ResultParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_results = False
        self.result_text = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.in_results = tag == "pre" and dict(attrs).get("id") == "arc09-test-results"

    def handle_endtag(self, tag: str) -> None:
        if tag == "pre":
            self.in_results = False

    def handle_data(self, data: str) -> None:
        if self.in_results:
            self.result_text += data


def render_dashboard(
    overrides: dict[str, object] | None = None,
    missing: tuple[str, ...] = (),
) -> dict[str, object]:
    chrome = shutil.which("google-chrome")
    if not chrome:
        pytest.skip("Google Chrome is required for ARC-09 browser tests.")

    with tempfile.TemporaryDirectory(prefix="arc09-browser-test-") as temp_dir:
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
            shutil.copy2(PROTOTYPE / name, page_dir / name)

        page = page_dir / "index.html"
        html = page.read_text(encoding="utf-8")
        if overrides is not None or missing:
            override_script = (
                "<script>window.arc09PrototypeData = Object.assign({}, "
                "window.arc09PrototypeData, "
                f"{json.dumps(overrides or {})});"
                f"for (const key of {json.dumps(missing)}) delete window.arc09PrototypeData[key];"
                "</script>\n"
            )
            html = html.replace(
                '    <script src="charts.js"></script>',
                f"    {override_script}    <script src=\"charts.js\"></script>",
                1,
            )
        probe = """
<script>
document.addEventListener('DOMContentLoaded', () => {
  const result = {};
  const overview = document.getElementById('overview-grid');
  const resources = document.getElementById('resource-grid');
  function stateBoxBounds(host) {
    const box = host.querySelector('.state-box');
    if (!box) return null;
    const rect = box.getBoundingClientRect();
    return { width: rect.width, height: rect.height, visible: rect.width > 0 && rect.height > 0 };
  }
  result.overview = {
    cards: overview.querySelectorAll('.metric-card').length,
    empty: overview.querySelector('.state-empty')?.textContent || '',
    error: overview.querySelector('.state-error')?.textContent || '',
    role: overview.querySelector('.state-box')?.getAttribute('role') || '',
    bounds: stateBoxBounds(overview)
  };
  result.resources = {
    cards: resources.querySelectorAll('.resource-card').length,
    empty: resources.querySelector('.state-empty')?.textContent || '',
    error: resources.querySelector('.state-error')?.textContent || '',
    role: resources.querySelector('.state-box')?.getAttribute('role') || '',
    bounds: stateBoxBounds(resources)
  };

  const sampleEdges = Array.from(document.querySelectorAll('#relationship-graph .graph-edge-mark'));
  result.sampleEdgeLabels = sampleEdges.map((group) => ({
    text: group.querySelector('.graph-edge-label')?.textContent || '',
    accessibleName: group.getAttribute('aria-label') || ''
  }));
  result.previewLoadingPreserved = false;
  document.querySelector('[data-state="loading"]').click();
  result.previewLoadingPreserved =
    document.querySelector('#state-preview .state-loading')?.textContent.includes('Loading sample content') === true;
  document.querySelector('[data-state="error"]').click();
  result.previewErrorPreserved =
    document.querySelector('#state-preview .state-error')?.getAttribute('role') === 'alert';

  function makeHost(id) {
    const panel = document.createElement('article');
    panel.className = 'panel chart-panel';
    const host = document.createElement('div');
    host.id = id;
    const tooltip = document.createElement('div');
    tooltip.className = 'chart-tooltip';
    panel.append(host, tooltip);
    document.body.appendChild(panel);
    return host;
  }
  const lineHost = makeHost('arc09-test-line');
  window.arc09Charts.renderLine(lineHost, [
    { step: 1, value: 2 }, { step: 4, value: 5 }, { step: 10, value: 8 }
  ]);
  result.ordinalLine = {
    xs: Array.from(lineHost.querySelectorAll('circle.line-dot'), (dot) => Number(dot.getAttribute('cx'))),
    labels: Array.from(lineHost.querySelectorAll('text.chart-tick'))
      .map((label) => label.textContent)
      .filter((label) => label.startsWith('Step '))
  };

  const scatterHost = makeHost('arc09-test-scatter');
  window.arc09Charts.renderScatter(scatterHost, [
    { x: 1, y: 2 }, { x: 4, y: 5 }, { x: 9, y: 8 }
  ]);
  result.quantitativeScatter = Array.from(
    scatterHost.querySelectorAll('circle.scatter-dot'),
    (dot) => Number(dot.getAttribute('cx'))
  );

  const graphHost = makeHost('arc09-test-graph');
  const graph = {
    nodes: [
      { id: 'a', label: 'Node A' },
      { id: 'b', label: 'Node B' },
      { id: 'c', label: 'Node C' },
      { id: 'd', label: 'Node D' },
      { id: 'e', label: 'Node E' }
    ],
    edges: [
      { from: 'a', to: 'b', label: 'An extremely long illustrative association label intended to remain fully visible in a narrow graph without being clipped or replaced' },
      { from: 'a', to: 'b', label: 'A second lengthy illustrative association label that must remain readable and within the SVG viewBox' },
      { from: 'a', to: 'b', label: 'Relationship gamma' },
      { from: 'a', to: 'c', label: 'Relationship delta' },
      { from: 'a', to: 'd', label: 'Relationship epsilon' },
      { from: 'a', to: 'e', label: 'Relationship zeta' },
      { from: 'b', to: 'c', label: 'Relationship eta' },
      { from: 'b', to: 'd', label: 'Relationship theta' },
      { from: 'c', to: 'd', label: 'Relationship iota' },
      { from: 'd', to: 'e', label: 'Relationship kappa' }
    ]
  };
  window.arc09Charts.renderRelationshipGraph(graphHost, graph);
  const labels = Array.from(graphHost.querySelectorAll('.graph-edge-label'));
  const labelBoxes = labels.map((label) => {
    const box = label.getBBox();
    return { x: box.x, y: box.y, width: box.width, height: box.height };
  });
  const nodeBoxes = Array.from(graphHost.querySelectorAll('rect.graph-node'), (node) => {
    const box = node.getBBox();
    return { x: box.x, y: box.y, width: box.width, height: box.height };
  });
  function overlaps(a, b) {
    return a.x < b.x + b.width && a.x + a.width > b.x &&
      a.y < b.y + b.height && a.y + a.height > b.y;
  }
  function luminance(color) {
    const channels = color.match(/[0-9.]+/g).slice(0, 3).map(Number).map((channel) => {
      const value = channel / 255;
      return value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4;
    });
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2];
  }
  function contrastRatio(first, second) {
    const values = [luminance(first), luminance(second)].sort((a, b) => b - a);
    return (values[0] + 0.05) / (values[1] + 0.05);
  }
  result.customGraph = {
    labels: Array.from(graphHost.querySelectorAll('.graph-edge-mark'), (group) => ({
      text: group.querySelector('.graph-edge-label')?.textContent || '',
      accessibleName: group.getAttribute('aria-label') || ''
    })),
    labelBoxes,
    labelOverlap: labelBoxes.some((box, index) =>
      labelBoxes.slice(index + 1).some((other) => overlaps(box, other))),
    nodeOverlap: labelBoxes.some((box) => nodeBoxes.some((node) => overlaps(box, node))),
    nodeOverlapIndices: labelBoxes.map((box, index) =>
      nodeBoxes.some((node) => overlaps(box, node)) ? index : -1
    ).filter((index) => index >= 0),
    edgeContrastRatio: contrastRatio(
      getComputedStyle(graphHost.querySelector('.graph-edge')).stroke,
      getComputedStyle(graphHost.closest('.chart-panel')).backgroundColor
    ),
    preserveAspectRatio: graphHost.querySelector('svg')?.getAttribute('preserveAspectRatio') || ''
  };
  const narrowGraphHost = makeHost('arc09-test-narrow-graph');
  narrowGraphHost.classList.add('graph-host');
  narrowGraphHost.style.width = '289px';
  window.arc09Charts.renderRelationshipGraph(narrowGraphHost, graph);
  const narrowHostBox = narrowGraphHost.getBoundingClientRect();
  const clippedEdge = Array.from(narrowGraphHost.querySelectorAll('.graph-edge-mark'))
    .find((group) => group.querySelector('.graph-edge-label').getBoundingClientRect().right > narrowHostBox.right);
  clippedEdge?.focus();
  const focusedLabelBox = clippedEdge?.querySelector('.graph-edge-label').getBoundingClientRect();
  const narrowTooltip = narrowGraphHost.closest('.chart-panel').querySelector('.chart-tooltip');
  const narrowTooltipBox = narrowTooltip.getBoundingClientRect();
  result.narrowGraphFocus = {
    foundClippedEdge: Boolean(clippedEdge),
    scrollLeft: narrowGraphHost.scrollLeft,
    labelVisible: Boolean(focusedLabelBox &&
      focusedLabelBox.left >= narrowGraphHost.getBoundingClientRect().left &&
      focusedLabelBox.right <= narrowGraphHost.getBoundingClientRect().right),
    tooltipVisible: !narrowTooltip.hidden &&
      narrowTooltipBox.left >= 0 && narrowTooltipBox.right <= window.innerWidth,
    tooltipContentFits: narrowTooltip.scrollWidth <= narrowTooltip.clientWidth
  };
  const invalidGraphHost = makeHost('arc09-test-invalid-graph');
  window.arc09Charts.renderRelationshipGraph(invalidGraphHost, {
    nodes: graph.nodes,
    edges: [{ from: 'a', to: 'b', label: '' }]
  });
  result.invalidGraphError = invalidGraphHost.querySelector('[role="alert"]')?.textContent || '';
  result.responsive = {
    viewportWidth: window.innerWidth,
    documentWidth: document.documentElement.scrollWidth,
    graphHostWidth: graphHost.clientWidth,
    graphSvgWidth: graphHost.querySelector('svg')?.getBoundingClientRect().width || 0
  };

  const output = document.createElement('pre');
  output.id = 'arc09-test-results';
  output.textContent = JSON.stringify(result);
  document.body.appendChild(output);
});
</script>
"""
        html = html.replace("  </body>", f"{probe}\n  </body>")
        page.write_text(html, encoding="utf-8")
        completed = subprocess.run(
            [
                chrome,
                "--headless",
                "--no-sandbox",
                "--disable-gpu",
                "--disable-dev-shm-usage",
                "--disable-background-networking",
                "--no-first-run",
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


@pytest.fixture(scope="module")
def dashboard_result() -> dict[str, object]:
    return render_dashboard()


def test_graph_displays_real_edge_labels_and_accessible_relationships(
    dashboard_result: dict[str, object],
) -> None:
    labels = dashboard_result["customGraph"]["labels"]
    assert [edge["text"] for edge in labels] == [
        "An extremely long illustrative association label intended to remain fully visible in a narrow graph without being clipped or replaced",
        "A second lengthy illustrative association label that must remain readable and within the SVG viewBox",
        "Relationship gamma",
        "Relationship delta",
        "Relationship epsilon",
        "Relationship zeta",
        "Relationship eta",
        "Relationship theta",
        "Relationship iota",
        "Relationship kappa",
    ]
    assert all(
        name.startswith(f"Node {source} to Node {target}: ")
        for name, (source, target) in zip(
            (edge["accessibleName"] for edge in labels),
            [("A", "B"), ("A", "B"), ("A", "B"), ("A", "C"), ("A", "D"),
             ("A", "E"), ("B", "C"), ("B", "D"), ("C", "D"), ("D", "E")],
        )
    )
    assert all(edge["text"] != "example link" for edge in dashboard_result["sampleEdgeLabels"])
    assert "include a label." in dashboard_result["invalidGraphError"]


def test_graph_edge_labels_do_not_overlap_each_other_or_nodes(
    dashboard_result: dict[str, object],
) -> None:
    graph = dashboard_result["customGraph"]
    assert graph["labelOverlap"] is False
    assert graph["nodeOverlap"] is False
    assert graph["preserveAspectRatio"] == "xMidYMid meet"
    assert all(
        box["x"] >= 0 and box["y"] >= 0 and
        box["x"] + box["width"] <= 560 and box["y"] + box["height"] <= 330
        for box in graph["labelBoxes"]
    )


def test_graph_relationships_have_readable_default_contrast(
    dashboard_result: dict[str, object],
) -> None:
    graph = dashboard_result["customGraph"]
    assert graph["edgeContrastRatio"] >= 3


def test_keyboard_focus_reveals_graph_labels_inside_narrow_scroll_container(
    dashboard_result: dict[str, object],
) -> None:
    focus = dashboard_result["narrowGraphFocus"]
    assert focus["foundClippedEdge"] is True
    assert focus["scrollLeft"] > 0
    assert focus["labelVisible"] is True
    assert focus["tooltipVisible"] is True
    assert focus["tooltipContentFits"] is True


def test_graph_and_dashboard_fit_a_narrow_viewport(
    dashboard_result: dict[str, object],
) -> None:
    responsive = dashboard_result["responsive"]
    assert responsive["viewportWidth"] <= 540
    assert responsive["documentWidth"] <= responsive["viewportWidth"]
    assert responsive["graphSvgWidth"] <= responsive["graphHostWidth"]


def test_ordinal_line_steps_are_equally_spaced_and_keep_step_labels(
    dashboard_result: dict[str, object],
) -> None:
    line = dashboard_result["ordinalLine"]
    x_positions = line["xs"]
    assert len(x_positions) == 3
    assert x_positions[1] - x_positions[0] == pytest.approx(x_positions[2] - x_positions[1])
    assert line["labels"] == ["Step 1", "Step 4", "Step 10"]


def test_quantitative_scatter_values_keep_proportional_spacing(
    dashboard_result: dict[str, object],
) -> None:
    x_positions = dashboard_result["quantitativeScatter"]
    assert len(x_positions) == 3
    assert (x_positions[1] - x_positions[0]) / (x_positions[2] - x_positions[0]) == pytest.approx(3 / 8)


def test_nonempty_dashboard_collections_remain_visible(
    dashboard_result: dict[str, object],
) -> None:
    assert dashboard_result["overview"]["cards"] == 3
    assert dashboard_result["resources"]["cards"] == 2
    assert dashboard_result["overview"]["empty"] == ""
    assert dashboard_result["resources"]["empty"] == ""
    assert dashboard_result["previewLoadingPreserved"] is True
    assert dashboard_result["previewErrorPreserved"] is True


def test_empty_dashboard_collections_show_approved_messages() -> None:
    result = render_dashboard({"overview": [], "resources": []})
    assert result["overview"]["empty"] == "No overview items are available."
    assert result["resources"]["empty"] == "No resource items are available."
    assert result["overview"]["role"] == "status"
    assert result["resources"]["role"] == "status"
    assert result["overview"]["bounds"]["visible"] is True
    assert result["resources"]["bounds"]["visible"] is True


def test_invalid_dashboard_collections_show_errors_not_empty_states() -> None:
    result = render_dashboard({"overview": None, "resources": {}})
    assert result["overview"]["error"]
    assert result["resources"]["error"]
    assert result["overview"]["role"] == "alert"
    assert result["resources"]["role"] == "alert"
    assert result["overview"]["empty"] == ""
    assert result["resources"]["empty"] == ""


def test_missing_dashboard_collections_show_errors_not_empty_states() -> None:
    result = render_dashboard(missing=("overview", "resources"))
    assert result["overview"]["error"]
    assert result["resources"]["error"]
    assert result["overview"]["role"] == "alert"
    assert result["resources"]["role"] == "alert"
    assert result["overview"]["empty"] == ""
    assert result["resources"]["empty"] == ""
