/* Local-only educational mission adapter; requests remain on the loopback host. */
(function () {
  const form = document.getElementById('mission-demo-form');
  if (!form) return;

  const status = document.getElementById('mission-demo-status');
  const results = document.getElementById('mission-demo-results');
  const destination = form.elements.destination_profile_id;
  const runButton = form.querySelector('button[type="submit"]');
  const SVG_NS = 'http://www.w3.org/2000/svg';
  const destinationLoadFallback =
    'Could not load synthetic destination profiles. Check that the local mission service is running and try again.';
  const formControls = [...form.querySelectorAll('input, select, button')];
  let authReady = false;
  let authConfigured = false;
  let authStateReceived = false;
  let signedIn = false;
  let destinationsLoaded = false;
  let result = null;

  class MissionAuthorizationError extends Error {
    constructor(status) {
      super(status === 401
        ? 'Your sign-in has expired. Sign out and sign in again to continue.'
        : 'Your account is not authorized to use this mission service.');
      this.status = status;
    }
  }

  function element(tag, text, parent) {
    const node = document.createElement(tag);
    if (text !== undefined) node.textContent = String(text);
    if (parent) parent.appendChild(node);
    return node;
  }

  function setStatus(message, tone) {
    const isError = tone === 'error';
    status.setAttribute('role', isError ? 'alert' : 'status');
    status.setAttribute('aria-live', isError ? 'assertive' : 'polite');
    if (tone) status.dataset.tone = tone;
    else status.removeAttribute('data-tone');
    status.textContent = message;
  }

  function publishMissionState(status, result = null, message = null) {
    window.dispatchEvent(new CustomEvent('mission-demo:state', {
      detail: { status, result, message }
    }));
  }

  function showError(message) {
    setStatus(message, 'error');
    results.hidden = true;
    results.replaceChildren();
    result = null;
    publishMissionState('error', null, message);
  }

  function setControlsDisabled(disabled) {
    formControls.forEach((control) => {
      control.disabled = disabled;
    });
  }

  function clearMissionResults() {
    results.hidden = true;
    results.replaceChildren();
    result = null;
    publishMissionState('empty', null);
  }

  function showRequestError(error, fallback) {
    if (error instanceof MissionAuthorizationError) {
      destinationsLoaded = false;
      setControlsDisabled(true);
      showError(error.message);
      return;
    }
    const detail = error instanceof Error ? error.message.trim() : '';
    showError(detail || fallback);
  }

  async function authenticatedFetch(path, options = {}) {
    const token = await window.nasaqAuth.getToken();
    if (!token) throw new MissionAuthorizationError(401);
    const headers = {
      ...options.headers,
      Authorization: `Bearer ${token}`
    };
    return fetch(path, { ...options, headers });
  }

  async function responseJson(response) {
    const payload = await response.json().catch(() => null);
    if (!response.ok) {
      if (response.status === 401 || response.status === 403) {
        throw new MissionAuthorizationError(response.status);
      }
      const error = payload && payload.error;
      const message = error && typeof error.message === 'string'
        ? error.message.trim()
        : '';
      const details = error && Array.isArray(error.details)
        ? error.details
          .filter((detail) => detail &&
            typeof detail.field === 'string' &&
            typeof detail.message === 'string')
          .map((detail) => {
            const field = detail.field.trim();
            const message = detail.message.trim();
            return message ? `${field ? `${field}: ` : ''}${message}` : '';
          })
          .filter(Boolean)
          .join(' ')
        : '';
      throw new Error([message, details].filter(Boolean).join(' ') || `HTTP ${response.status}`);
    }
    return payload;
  }

  function missionRequest() {
    return {
      destination_profile_id: destination.value,
      selected_payload_ids: [...form.querySelectorAll('input[name="selected_payload_ids"]:checked')]
        .map((input) => input.value)
    };
  }

  function drawTrajectory(host, trajectory) {
    const { times_s: times, states } = trajectory || {};
    if (!Array.isArray(times) || !Array.isArray(states) ||
      states.length < 2 || times.length !== states.length ||
      times.some((value) => !Number.isFinite(value)) ||
      states.some((row) => !Array.isArray(row) || row.length !== 6 ||
        row.some((value) => !Number.isFinite(value)))
    ) {
      throw new Error('The local service returned an invalid trajectory for display.');
    }
    const xs = states.map((row) => row[0]);
    const ys = states.map((row) => row[1]);
    const minX = Math.min(...xs), maxX = Math.max(...xs);
    const minY = Math.min(...ys), maxY = Math.max(...ys);
    const spanX = maxX - minX || 1, spanY = maxY - minY || 1;
    const points = states.map((row) => [
      30 + ((row[0] - minX) / spanX) * 540,
      290 - ((row[1] - minY) / spanY) * 260
    ]);
    const svg = document.createElementNS(SVG_NS, 'svg');
    svg.setAttribute('class', 'mission-trajectory');
    svg.setAttribute('viewBox', '0 0 600 320');
    svg.setAttribute('role', 'img');
    svg.setAttribute('aria-labelledby', 'mission-trajectory-title mission-trajectory-description');
    const title = document.createElementNS(SVG_NS, 'title');
    title.id = 'mission-trajectory-title';
    title.textContent = 'Synthetic ECI X/Y orbit projection';
    const desc = document.createElementNS(SVG_NS, 'desc');
    desc.id = 'mission-trajectory-description';
    desc.textContent = 'Projected position samples from the educational Earth two-body simulator, in metres. This is not a transfer trajectory.';
    const path = document.createElementNS(SVG_NS, 'path');
    path.setAttribute('d', points.map(([x, y], index) =>
      `${index ? 'L' : 'M'} ${x.toFixed(2)} ${y.toFixed(2)}`
    ).join(' '));
    path.setAttribute('fill', 'none');
    path.setAttribute('stroke', '#1d4ed8');
    path.setAttribute('stroke-width', '3');
    svg.append(title, desc, path);
    host.appendChild(svg);
  }

  function render(payload) {
    results.replaceChildren();
    results.hidden = false;
    element('h3', 'Mission run results · synthetic educational output', results);
    element('p', `Profile: ${payload.mission.destination_display_name}; payloads: ${payload.mission.selected_payload_ids.join(', ')}.`, results);
    const trajectory = payload.trajectory;
    const model = trajectory.model;
    const diagnostics = trajectory.diagnostics;
    element('p', `${model.dynamics} · ${model.integrator} · ${model.reference_frame}.`, results);
    element('p', `Time: ${model.time_unit}; position: ${model.position_unit}; velocity: ${model.velocity_unit}.`, results);
    element('p', `Maximum absolute energy drift: ${diagnostics.max_abs_energy_drift_m2_s2} m²/s²; maximum absolute angular-momentum drift: ${diagnostics.max_abs_angular_momentum_drift_m2_s} m²/s.`, results);
    element('p', 'Synthetic educational two-body projection; not a transfer trajectory or validated mission prediction.', results);
    const limitations = element('ul', undefined, results);
    payload.limitations.forEach((item) => element('li', item, limitations));

    const resource = payload.resource_evaluation;
    const resourceSection = element('section', undefined, results);
    element('h4', 'ARC-08 resource evaluator · policy approval pending', resourceSection);
    element('p', resource.warning, resourceSection);
    const summary = resource.result;
    element('p', `Educational result: ${summary.feasible ? 'within this demo scenario limits' : 'exceeds this demo scenario limits'}; abstract totals: budget ${summary.resource_totals.budget_units}, mass ${summary.resource_totals.mass_units}, power ${summary.resource_totals.power_units}, slots ${summary.resource_totals.payload_slots}.`, resourceSection);
    if (summary.violations.length) {
      const violations = element('ul', undefined, resourceSection);
      summary.violations.forEach((violation) => element(
        'li',
        `${violation.code}: ${violation.observed_total} of ${violation.limit} abstract units`,
        violations
      ));
    }

    const grid = element('div', undefined, results);
    grid.className = 'mission-result-grid';
    const chartPanel = element('section', undefined, grid);
    element('h4', 'Projected trajectory (ECI X/Y)', chartPanel);
    drawTrajectory(chartPanel, trajectory);
    const tablePanel = element('section', undefined, grid);
    element('h4', 'Trajectory state table', tablePanel);
    const details = element('details', undefined, tablePanel);
    element('summary', 'View time, position, and velocity samples', details);
    const wrapper = element('div', undefined, details);
    wrapper.className = 'mission-result-table';
    const table = element('table', undefined, wrapper);
    element('caption', 'Synthetic trajectory samples in ECI SI units', table);
    const head = element('thead', undefined, table);
    const headerRow = element('tr', undefined, head);
    ['t (s)', 'x (m)', 'y (m)', 'z (m)', 'vx (m/s)', 'vy (m/s)', 'vz (m/s)']
      .forEach((label) => element('th', label, headerRow));
    const body = element('tbody', undefined, table);
    trajectory.states.forEach((row, index) => {
      const tr = element('tr', undefined, body);
      [trajectory.times_s[index], ...row].forEach((value) =>
        element('td', Number(value).toPrecision(7), tr)
      );
    });
    setStatus(`Simulation complete: ${trajectory.states.length} state samples. Educational output only.`, 'success');
  }

  async function loadDestinations() {
    if (!authReady || !authConfigured || !signedIn) return;
    setControlsDisabled(true);
    result = null;
    publishMissionState('loading', result);
    setStatus('Loading synthetic destination profiles…');
    try {
      const response = await authenticatedFetch('/api/v1/missions/destinations');
      const payload = await responseJson(response);
      if (!payload || !Array.isArray(payload.destinations)) {
        throw new Error('The local service returned an invalid destination list.');
      }
      destination.replaceChildren();
      payload.destinations.forEach((profile) => {
        const option = document.createElement('option');
        option.value = profile.profile_id;
        option.textContent = `${profile.display_name} · ${(profile.altitude_m / 1000).toLocaleString()} km altitude`;
        destination.appendChild(option);
      });
      if (!payload.destinations.length) {
        throw new Error('The local service returned no synthetic destination profiles.');
      }
      destinationsLoaded = true;
      setControlsDisabled(false);
      setStatus('Ready. Configure a synthetic mission, then validate and run it locally.');
      publishMissionState('empty', null);
    } catch (error) {
      if (error instanceof MissionAuthorizationError) {
        showRequestError(error, destinationLoadFallback);
        return;
      }
      const detail = error instanceof Error ? error.message.trim() : '';
      showError(detail
        ? `Could not load synthetic destination profiles: ${detail}. Check that the local mission service is running and try again.`
        : destinationLoadFallback);
    }
  }

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    if (!authReady || !authConfigured || !signedIn || !destinationsLoaded) {
      setControlsDisabled(true);
      setStatus(
        authConfigured
          ? 'Sign in to load synthetic destination profiles and enable mission operations.'
          : 'Clerk sign-in is not configured. Mission operations are disabled.',
        'error'
      );
      return;
    }
    result = null;
    results.hidden = true;
    results.replaceChildren();
    publishMissionState('loading', result);
    const request = missionRequest();
    if (!request.selected_payload_ids.length) {
      showError('Select at least one payload before running the educational simulation.');
      return;
    }
    runButton.disabled = true;
    setStatus('Validating mission configuration…');
    try {
      const validationResponse = await authenticatedFetch(
        '/api/v1/missions/validate',
        {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request)
        }
      );
      const validation = await responseJson(validationResponse);
      if (!validation.valid) throw new Error('The local mission configuration is invalid.');
      setStatus('Configuration validated. Running ARC-05 simulation and ARC-08 evaluation…');
      const runResponse = await authenticatedFetch('/api/v1/missions/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request)
      });
      result = await responseJson(runResponse);
      render(result);
      publishMissionState('ready', result);
    } catch (error) {
      showRequestError(error, 'The local mission run failed.');
    } finally {
      runButton.disabled = !signedIn || !destinationsLoaded;
    }
  });

  function applyAuthState(detail) {
    authStateReceived = true;
    authReady = true;
    authConfigured = Boolean(detail && detail.configured);
    const wasSignedIn = signedIn;
    signedIn = Boolean(detail && detail.signedIn);
    if (!authConfigured || !signedIn) {
      destinationsLoaded = false;
      setControlsDisabled(true);
      clearMissionResults();
      const authStatus = document.getElementById('mission-demo-auth-status');
      const authFailed = authStatus && authStatus.dataset.tone === 'error';
      const message = authFailed
        ? authStatus.textContent
        : authConfigured
          ? 'Sign in above to load synthetic destination profiles.'
          : 'Clerk sign-in is not configured. Mission operations are disabled.';
      setStatus(message, authFailed ? 'error' : undefined);
      return;
    }
    if (!wasSignedIn) loadDestinations();
  }

  setControlsDisabled(true);
  window.addEventListener('nasaq-auth:state', (event) => {
    applyAuthState(event.detail);
  });
  if (
    window.nasaqAuth &&
    window.nasaqAuth.ready &&
    typeof window.nasaqAuth.getToken === 'function'
  ) {
    window.nasaqAuth.ready.then(() => {
      if (!authStateReceived) {
        applyAuthState({ configured: false, signedIn: false });
        setStatus(
          'Sign-in state could not be initialized. Mission operations are disabled.',
          'error'
        );
      }
    }, () => {
      applyAuthState({ configured: false, signedIn: false });
      setStatus(
        'Sign-in state could not be initialized. Mission operations are disabled.',
        'error'
      );
    });
  } else {
    applyAuthState({ configured: false, signedIn: false });
    setStatus(
      'Sign-in controller is unavailable. Mission operations are disabled.',
      'error'
    );
  }
}());
