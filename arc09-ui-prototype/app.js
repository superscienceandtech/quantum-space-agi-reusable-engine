/* Prototype UI patterns: data rendering, navigation, filtering, and state previews. */
(function () {
  const data = window.arc09PrototypeData;
  const viewNames = {
    dashboard: 'Mission dashboard',
    'mission-builder': 'Mission Builder',
    spacecraft: 'Spacecraft Configuration',
    resources: 'Resource Dashboard',
    simulation: 'Simulation & Results',
    comparison: 'Mission Comparison & Report'
  };

  function node(tag, className, content) {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (content !== undefined) element.textContent = content;
    return element;
  }

  function statusBadge(label, tone) {
    const badge = node('span', `status-badge status-${tone}`, label);
    return badge;
  }

  function metricCard(item) {
    const card = node('article', 'metric-card');
    const top = node('div', 'metric-top');
    top.append(node('span', 'metric-icon metric-icon-' + item.tone, item.icon), statusBadge('Sample', 'neutral'));
    const label = node('p', 'metric-label', item.label);
    const value = node('p', 'metric-value', item.value);
    const detail = node('p', 'metric-detail', item.detail);
    card.append(top, label, value, detail);
    return card;
  }

  function resourceCard(item, index) {
    const card = node('article', 'panel resource-card');
    const titleRow = node('div', 'resource-title-row');
    titleRow.append(node('h3', '', item.label), node('span', 'resource-index', `SAMPLE ${String(index + 1).padStart(2, '0')}`));
    const valueRow = node('div', 'resource-value-row');
    valueRow.append(node('strong', 'resource-value', `${item.value}${item.unit}`), node('span', 'resource-tag', 'Synthetic share'));
    const track = node('div', 'resource-track');
    track.setAttribute('role', 'img');
    track.setAttribute('aria-label', `${item.label}: synthetic sample share ${item.value}${item.unit}`);
    const fill = node('span', 'resource-fill');
    fill.style.width = `${item.value}%`;
    track.appendChild(fill);
    card.append(titleRow, valueRow, track, node('p', 'resource-detail', item.detail));
    return card;
  }

  const comparisonUnavailable = 'Cross-mission comparison unavailable: the local API has no comparison or mission-history endpoint.';
  const emptyMissionMessage = 'Run a mission in Mission Builder to see the latest local API result.';
  let latestMissionState = { status: 'empty', result: null, message: null };

  function runStatePanel(host, title, message, state) {
    const panel = node('section', `run-state-panel run-state-${state}`);
    panel.setAttribute('role', state === 'error' ? 'alert' : 'status');
    panel.append(node('h2', '', title), node('p', '', message));
    host.appendChild(panel);
  }

  function renderSpacecraftResult(state) {
    const host = document.getElementById('spacecraft-run-result');
    host.replaceChildren();
    if (state.status !== 'ready' || !state.result) {
      const title = state.status === 'error' ? 'Mission result unavailable' : state.status === 'loading' ? 'Mission run in progress' : 'No mission results yet';
      const message = state.status === 'error' ? state.message : state.status === 'loading' ? 'Previous mission results were cleared while this run is in progress.' : emptyMissionMessage;
      runStatePanel(host, title, message, state.status);
      return;
    }

    const mission = state.result.mission;
    const panel = node('article', 'mission-summary-card');
    panel.append(node('h2', '', 'Latest spacecraft configuration'));
    panel.append(node('p', '', `Spacecraft profile: ${mission.spacecraft_profile_id}`));
    panel.append(node('h3', '', 'Selected payloads'));
    const payloads = node('ul', 'mission-value-list');
    mission.selected_payload_ids.forEach((payloadId) => payloads.append(node('li', '', payloadId)));
    panel.append(payloads);
    panel.append(node('p', 'run-unavailable-note', 'physical spacecraft properties are unavailable: mass, dimensions, propulsion, fuel, capacity, and power are not represented by this API.'));
    host.appendChild(panel);
  }

  function renderResourceResult(state) {
    const host = document.getElementById('resource-run-result');
    host.replaceChildren();
    if (state.status !== 'ready' || !state.result) {
      const title = state.status === 'error' ? 'Resource result unavailable' : state.status === 'loading' ? 'Mission run in progress' : 'No resource evaluation yet';
      const message = state.status === 'error' ? state.message : state.status === 'loading' ? 'Previous mission results were cleared while this run is in progress.' : emptyMissionMessage;
      runStatePanel(host, title, message, state.status);
      return;
    }

    const evaluation = state.result.resource_evaluation;
    const result = evaluation.result;
    const panel = node('article', 'mission-summary-card');
    panel.append(node('h2', '', 'ARC-08 educational evaluator'));
    panel.append(node('p', '', `Evaluator version: ${result.evaluator_version}`));
    panel.append(node('p', '', `Scenario: ${result.scenario_id}`));
    panel.append(node('p', '', `Evaluation status: ${evaluation.status}`));
    panel.append(node('p', 'run-warning', `policy approval pending (${evaluation.policy_approval_status}); this output is educational only.`));
    panel.append(node('p', '', evaluation.warning));
    const totals = node('ul', 'mission-value-list');
    [
      ['Budget', result.resource_totals.budget_units],
      ['Mass', result.resource_totals.mass_units],
      ['Power', result.resource_totals.power_units],
      ['Payload slots', result.resource_totals.payload_slots]
    ].forEach(([label, value]) => totals.append(node('li', '', `${label}: ${value} abstract units`)));
    panel.append(node('h3', '', 'Resource totals · abstract units'));
    panel.append(totals);
    panel.append(node('p', '', `Educational scenario result: ${result.feasible ? 'within this scenario' : 'outside this scenario'}; this is not mission feasibility.`));
    panel.append(node('h3', '', 'Scenario violations'));
    if (result.violations.length) {
      const violations = node('ul', 'mission-value-list mission-violations');
      result.violations.forEach((violation) => violations.append(node(
        'li',
        '',
        `${violation.code}: ${violation.observed_total} of ${violation.limit} abstract units`
      )));
      panel.append(violations);
    } else {
      panel.append(node('p', '', 'No violations reported by this educational scenario.'));
    }
    host.appendChild(panel);
  }

  function renderReportResult(state) {
    const host = document.getElementById('report-run-result');
    host.replaceChildren();
    if (state.status !== 'ready' || !state.result) {
      const title = state.status === 'error' ? 'Mission report unavailable' : state.status === 'loading' ? 'Mission run in progress' : 'No mission report yet';
      const message = state.status === 'error' ? state.message : state.status === 'loading' ? 'Previous mission results were cleared while this run is in progress.' : emptyMissionMessage;
      runStatePanel(host, title, message, state.status);
      host.append(node('p', 'run-unavailable-note', comparisonUnavailable));
      return;
    }

    const { mission, resource_evaluation: evaluation, trajectory } = state.result;
    const panel = node('article', 'mission-summary-card');
    panel.append(node('h2', '', 'Latest mission report'));
    panel.append(node('p', '', `Destination: ${mission.destination_display_name} (${mission.destination_profile_id})`));
    panel.append(node('p', '', `Selected payloads: ${mission.selected_payload_ids.join(', ')}`));
    panel.append(node('p', '', `ARC-05: ${trajectory.model.integrator} integrator · ${trajectory.model.reference_frame} frame · ${trajectory.states.length} state samples`));
    panel.append(node('p', '', `ARC-08 evaluator status: ${evaluation.status}; policy approval ${evaluation.policy_approval_status}.`));
    panel.append(node('p', 'run-unavailable-note', comparisonUnavailable));
    host.appendChild(panel);
  }

  function renderMissionState(state) {
    latestMissionState = state;
    renderSpacecraftResult(state);
    renderResourceResult(state);
    renderReportResult(state);

    const status = document.getElementById('simulation-run-state');
    const results = document.getElementById('mission-demo-results');
    results.hidden = state.status !== 'ready';
    if (state.status === 'ready') {
      status.textContent = `Simulation complete: ${state.result.trajectory.states.length} state samples. Educational output only.`;
    } else if (state.status === 'error') {
      status.textContent = `Mission result unavailable: ${state.message}`;
    } else if (state.status === 'loading') {
      status.textContent = 'Mission run in progress. Previous mission results were cleared.';
    } else {
      status.textContent = emptyMissionMessage;
    }
  }

  window.addEventListener('mission-demo:state', (event) => renderMissionState(event.detail));

  function fillTable(bodyId, rows, fields) {
    const body = document.getElementById(bodyId);
    body.replaceChildren(...rows.map((row) => {
      const tr = document.createElement('tr');
      fields(row).forEach((value) => {
        const cell = document.createElement('td');
        cell.textContent = String(value);
        tr.appendChild(cell);
      });
      return tr;
    }));
  }

  function renderActivity(filter) {
    const list = document.getElementById('activity-list');
    const rows = data.activity.filter((item) => filter === 'all' || item.status === filter);
    if (!rows.length) {
      const empty = node('li', 'activity-empty');
      empty.append(node('strong', '', 'No matching sample entries'), node('span', '', 'Choose another filter to view the synthetic examples.'));
      list.replaceChildren(empty);
      return;
    }
    list.replaceChildren(...rows.map((item) => {
      const li = node('li', 'activity-item');
      const icon = node('span', 'activity-symbol', item.title.slice(-1).toUpperCase());
      icon.setAttribute('aria-hidden', 'true');
      const content = node('div', 'activity-content');
      content.append(node('strong', '', item.title), node('span', '', item.action));
      const meta = node('div', 'activity-meta');
      meta.append(statusBadge(item.status, item.status === 'Reviewed' ? 'success' : item.status === 'Planning' ? 'info' : 'warning'), node('time', '', item.time));
      li.append(icon, content, meta);
      return li;
    }));
  }

  function previewState(state) {
    const host = document.getElementById('state-preview');
    host.replaceChildren();
    const content = {
      loading: ['state-loading', 'Loading sample content', 'This is a visual state example; no request is running.'],
      empty: ['state-empty', 'No sample content', 'An empty-state pattern with a neutral next step.'],
      error: ['state-error', 'Sample content unavailable', 'An error-state pattern; no backend request was made.']
    }[state];
    const box = node('div', `state-box ${content[0]}`);
    box.setAttribute('role', state === 'error' ? 'alert' : 'status');
    if (state === 'loading') box.append(node('span', 'loading-indicator', '···'));
    box.append(node('strong', '', content[1]), node('span', '', content[2]));
    host.appendChild(box);
  }

  function setView(view) {
    const activeView = Object.prototype.hasOwnProperty.call(viewNames, view) ? view : 'dashboard';
    document.querySelectorAll('[data-page]').forEach((page) => {
      page.hidden = page.dataset.page !== activeView;
    });
    document.querySelectorAll('.nav-item').forEach((item) => {
      const active = item.dataset.view === activeView;
      item.classList.toggle('is-active', active);
      if (active) item.setAttribute('aria-current', 'page');
      else item.removeAttribute('aria-current');
    });
    closeMenu(false);
    document.getElementById('main-content').focus({ preventScroll: true });
  }

  function openMenu() {
    const sidebar = document.getElementById('app-sidebar');
    const backdrop = document.getElementById('sidebar-backdrop');
    const button = document.getElementById('menu-toggle');
    sidebar.classList.add('is-open');
    sidebar.inert = false;
    sidebar.setAttribute('aria-hidden', 'false');
    backdrop.hidden = false;
    button.setAttribute('aria-expanded', 'true');
    button.setAttribute('aria-label', 'Close navigation');
    sidebar.querySelector('.nav-item.is-active')?.focus();
  }

  function closeMenu(restoreFocus = false) {
    const sidebar = document.getElementById('app-sidebar');
    const backdrop = document.getElementById('sidebar-backdrop');
    const button = document.getElementById('menu-toggle');
    sidebar.classList.remove('is-open');
    backdrop.hidden = true;
    const mobile = window.matchMedia('(max-width: 760px)').matches;
    sidebar.inert = mobile;
    sidebar.setAttribute('aria-hidden', String(mobile));
    button.setAttribute('aria-expanded', 'false');
    button.setAttribute('aria-label', 'Open navigation');
    if (restoreFocus && mobile) button.focus();
  }

  function syncNavigationForViewport() {
    const sidebar = document.getElementById('app-sidebar');
    const button = document.getElementById('menu-toggle');
    const backdrop = document.getElementById('sidebar-backdrop');
    const mobile = window.matchMedia('(max-width: 760px)').matches;
    const isOpen = button.getAttribute('aria-expanded') === 'true';
    if (!mobile) {
      sidebar.classList.remove('is-open');
      sidebar.inert = false;
      sidebar.setAttribute('aria-hidden', 'false');
      backdrop.hidden = true;
      button.setAttribute('aria-expanded', 'false');
      button.setAttribute('aria-label', 'Open navigation');
    } else if (!isOpen) {
      if (sidebar.contains(document.activeElement)) button.focus();
      sidebar.classList.remove('is-open');
      sidebar.inert = true;
      sidebar.setAttribute('aria-hidden', 'true');
      backdrop.hidden = true;
      button.setAttribute('aria-expanded', 'false');
      button.setAttribute('aria-label', 'Open navigation');
    }
  }

  function setupNavigation() {
    const button = document.getElementById('menu-toggle');
    const sidebar = document.getElementById('app-sidebar');
    const brand = document.querySelector('.brand');
    syncNavigationForViewport();

    document.querySelectorAll('.nav-item').forEach((link) => {
      link.addEventListener('click', () => setView(link.dataset.view));
    });
    document.querySelectorAll('.back-dashboard').forEach((link) => {
      link.addEventListener('click', () => {
        location.hash = 'dashboard';
        setView('dashboard');
      });
    });
    button.addEventListener('click', () => {
      button.getAttribute('aria-expanded') === 'true' ? closeMenu(true) : openMenu();
    });
    document.getElementById('sidebar-backdrop').addEventListener('click', () => closeMenu(true));
    window.addEventListener('resize', syncNavigationForViewport);
    document.addEventListener('keydown', (event) => {
      const isOpen = button.getAttribute('aria-expanded') === 'true';
      if (event.key === 'Escape' && isOpen) {
        closeMenu(true);
        return;
      }
      if (event.key !== 'Tab' || !isOpen) return;

      // Keep the sequence aligned with document order while the drawer is open.
      const targets = [button, brand, ...sidebar.querySelectorAll('a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])')]
        .filter((target) => target && !target.disabled && target.tabIndex >= 0);
      const first = targets[0];
      const last = targets[targets.length - 1];
      const activeIndex = targets.indexOf(document.activeElement);
      if (activeIndex === -1) {
        event.preventDefault();
        (event.shiftKey ? last : first).focus();
      } else if (event.shiftKey && activeIndex === 0) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && activeIndex === targets.length - 1) {
        event.preventDefault();
        first.focus();
      }
    });
    window.addEventListener('hashchange', () => setView(location.hash.slice(1)));
    if (location.hash) setView(location.hash.slice(1));
  }

  function start() {
    setupNavigation();
    renderMissionState(latestMissionState);
    if (!data || !window.arc09Charts) {
      document.querySelectorAll('.chart-host').forEach((host) => {
        const message = !data ? 'Sample chart data is unavailable.' : 'Chart rendering is unavailable.';
        host.innerHTML = `<div class="state-box state-error" role="alert"><strong>Chart preview unavailable</strong><span>${message}</span></div>`;
        host.setAttribute('aria-busy', 'false');
      });
      return;
    }
    const overview = document.getElementById('overview-grid');
    overview.replaceChildren(...data.overview.map(metricCard));
    const resources = document.getElementById('resource-grid');
    resources.replaceChildren(...data.resources.map(resourceCard));
    const lineRendered = window.arc09Charts.renderLine(document.getElementById('line-chart'), data.trend);
    const barsRendered = window.arc09Charts.renderBars(document.getElementById('bar-chart'), data.comparison);
    const scatterRendered = window.arc09Charts.renderScatter(document.getElementById('scatter-chart'), data.scatter);
    const graphRendered = window.arc09Charts.renderRelationshipGraph(document.getElementById('relationship-graph'), data.relationshipGraph);
    fillTable('line-table', lineRendered ? data.trend : [], (row) => [`Step ${row.step}`, row.value]);
    fillTable('bar-table', barsRendered ? data.comparison : [], (row) => [row.category, row.seriesA, row.seriesB]);
    fillTable('scatter-table', scatterRendered ? data.scatter : [], (point) => [point.x, point.y]);
    const graphRows = graphRendered ? [
      ...data.relationshipGraph.nodes.map((item) => ['Node', item.label, 'Illustrative concept only']),
      ...data.relationshipGraph.edges.map((edge) => {
        const from = data.relationshipGraph.nodes.find((item) => item.id === edge.from);
        const to = data.relationshipGraph.nodes.find((item) => item.id === edge.to);
        return ['Connection', `${from.label} to ${to.label}`, edge.label];
      })
    ] : [];
    fillTable('graph-table', graphRows, (row) => row);
    renderActivity('all');
    previewState('loading');

    document.getElementById('activity-filter').addEventListener('change', (event) => renderActivity(event.target.value));
    document.querySelectorAll('[data-state]').forEach((button) => button.addEventListener('click', () => {
      document.querySelectorAll('[data-state]').forEach((tab) => {
        const selected = tab === button;
        tab.classList.toggle('is-selected', selected);
        tab.setAttribute('aria-pressed', String(selected));
      });
      previewState(button.dataset.state);
    }));
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();
}());
