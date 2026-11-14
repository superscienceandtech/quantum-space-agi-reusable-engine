/* Prototype UI patterns: data rendering, navigation, filtering, and state previews. */
(function () {
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

  function renderActivity(filter, data) {
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

  function showStartupFailure() {
    const notice = document.getElementById('startup-error');
    notice.textContent = 'Dashboard preview unavailable. The prototype data provider or required synthetic fixture data is missing or invalid. Restore the prototype files and reload; no live data is available.';
    notice.hidden = false;
  }

  function clearDashboardContent(isLoading) {
    ['overview-grid', 'resource-grid', 'activity-list', 'line-table', 'bar-table', 'scatter-table', 'graph-table']
      .forEach((id) => document.getElementById(id).replaceChildren());
    document.querySelectorAll('.chart-host').forEach((host) => {
      host.replaceChildren();
      host.setAttribute('aria-busy', String(isLoading));
    });
  }

  function reportStartupFailure(error) {
    const cleanupErrors = [];
    const attemptCleanup = (action) => {
      try {
        action();
      } catch (cleanupError) {
        cleanupErrors.push(cleanupError);
      }
    };

    attemptCleanup(() => {
      const loading = document.getElementById('dashboard-loading');
      if (loading) loading.hidden = true;
    });
    attemptCleanup(() => {
      const dashboard = document.getElementById('dashboard');
      if (dashboard) dashboard.setAttribute('aria-busy', 'false');
    });
    attemptCleanup(() => clearDashboardContent(false));
    attemptCleanup(() => showStartupFailure());

    try {
      if (typeof console !== 'undefined' && typeof console.error === 'function') {
        const diagnostic = cleanupErrors.length ? { startupError: error, cleanupErrors } : error;
        console.error('ARC-09 dashboard startup failed.', diagnostic);
      }
    } catch (_) {
      // Diagnostics are best-effort; the UI cleanup above must not depend on logging.
    }
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

  let startupStarted = false;

  async function start() {
    if (startupStarted) return;
    startupStarted = true;

    setupNavigation();
    const dashboard = document.getElementById('dashboard');
    const loading = document.getElementById('dashboard-loading');
    document.getElementById('startup-error').hidden = true;
    clearDashboardContent(true);
    dashboard.setAttribute('aria-busy', 'true');
    loading.hidden = false;

    const provider = window.arc09PrototypeProvider;
    if (!provider || typeof provider.getData !== 'function') {
      throw new Error('Prototype data provider is unavailable.');
    }

    const data = await provider.getData();
    const validation = window.arc09PrototypeValidation;
    if (!validation || typeof validation.hasValidPrototypeData !== 'function' || !validation.hasValidPrototypeData(data)) {
      throw new Error('Prototype data failed validation.');
    }

    loading.hidden = true;
    if (!window.arc09Charts) {
      document.querySelectorAll('.chart-host').forEach((host) => {
        host.innerHTML = '<div class="state-box state-error" role="alert"><strong>Chart preview unavailable</strong><span>Chart rendering is unavailable.</span></div>';
        host.setAttribute('aria-busy', 'false');
      });
      dashboard.setAttribute('aria-busy', 'false');
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
    renderActivity('all', data);
    previewState('loading');
    dashboard.setAttribute('aria-busy', 'false');

    document.getElementById('activity-filter').addEventListener('change', (event) => renderActivity(event.target.value, data));
    document.querySelectorAll('[data-state]').forEach((button) => button.addEventListener('click', () => {
      document.querySelectorAll('[data-state]').forEach((tab) => {
        const selected = tab === button;
        tab.classList.toggle('is-selected', selected);
        tab.setAttribute('aria-pressed', String(selected));
      });
      previewState(button.dataset.state);
    }));
  }

  function launchStartup() {
    start().catch(reportStartupFailure);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', launchStartup);
  else launchStartup();
}());
