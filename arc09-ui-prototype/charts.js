/* Reusable, dependency-free SVG chart presentation for synthetic examples. */
(function () {
  const SVG_NS = 'http://www.w3.org/2000/svg';
  const BLUE = '#1D4ED8';
  const TEAL = '#0F766E';

  function el(tag, attrs, text) {
    const node = document.createElementNS(SVG_NS, tag);
    Object.entries(attrs || {}).forEach(([key, value]) => node.setAttribute(key, value));
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function baseChart(host, title, description, width, height) {
    const svg = el('svg', { viewBox: `0 0 ${width} ${height}`, role: 'group', preserveAspectRatio: 'xMidYMid meet' });
    const titleId = `${host.id}-svg-title`;
    const descId = `${host.id}-svg-desc`;
    svg.setAttribute('aria-labelledby', `${titleId} ${descId}`);
    svg.append(el('title', { id: titleId }, title), el('desc', { id: descId }, description));
    return svg;
  }

  function text(svg, value, x, y, className, anchor) {
    svg.appendChild(el('text', { x, y, class: className, 'text-anchor': anchor || 'middle' }, value));
  }

  function grid(svg, bounds, max, steps) {
    const { left, right, top, bottom } = bounds;
    for (let i = 0; i <= steps; i += 1) {
      const value = (max / steps) * i;
      const y = bottom - (value / max) * (bottom - top);
      svg.appendChild(el('line', { x1: left, y1: y, x2: right, y2: y, class: i === 0 ? 'chart-axis' : 'chart-gridline' }));
      text(svg, String(value), left - 9, y + 3, 'chart-tick', 'end');
    }
  }

  function axisTitles(svg, xTitle, yTitle, width, height, bounds) {
    text(svg, xTitle, (bounds.left + bounds.right) / 2, height - 4, 'chart-axis-title');
    const centerY = (bounds.top + bounds.bottom) / 2;
    svg.appendChild(el('text', { x: 13, y: centerY, class: 'chart-axis-title', 'text-anchor': 'middle', transform: `rotate(-90 13 ${centerY})` }, yTitle));
  }

  function addTooltipMark(svg, shape, attrs, accessibleName, tipText, showTip) {
    const group = el('g', { class: 'chart-mark', tabindex: '0', role: 'img', 'aria-label': accessibleName });
    const mark = el(shape, attrs);
    const ring = shape === 'rect'
      ? el('rect', { x: Number(attrs.x) - 3, y: Number(attrs.y) - 3, width: Number(attrs.width) + 6, height: Number(attrs.height) + 6, rx: 4, class: 'chart-focus-ring' })
      : el('circle', { cx: attrs.cx, cy: attrs.cy, r: Number(attrs.r) + 6, class: 'chart-focus-ring' });
    group.append(ring, mark);
    group.addEventListener('pointerenter', (event) => showTip(tipText, event, group));
    group.addEventListener('pointermove', (event) => showTip(tipText, event, group));
    group.addEventListener('pointerleave', () => showTip('', null, group));
    group.addEventListener('focus', () => showTip(tipText, null, group));
    group.addEventListener('blur', () => showTip('', null, group));
    svg.appendChild(group);
  }

  function addTooltipGroup(svg, children, accessibleName, tipText, showTip, className) {
    const group = el('g', { class: `chart-mark ${className || ''}`.trim(), tabindex: '0', role: 'img', 'aria-label': accessibleName });
    group.append(...children);
    group.addEventListener('pointerenter', (event) => showTip(tipText, event, group));
    group.addEventListener('pointermove', (event) => showTip(tipText, event, group));
    group.addEventListener('pointerleave', () => showTip('', null, group));
    group.addEventListener('focus', () => showTip(tipText, null, group));
    group.addEventListener('blur', () => showTip('', null, group));
    svg.appendChild(group);
    return group;
  }

  function showEmpty(host) {
    host.innerHTML = '<div class="state-box state-empty" role="status"><strong>No sample data</strong><span>This practice chart has no values to display.</span></div>';
    host.setAttribute('aria-busy', 'false');
    return false;
  }

  function showError(host, message) {
    const box = document.createElement('div');
    box.className = 'state-box state-error';
    box.setAttribute('role', 'alert');
    const title = document.createElement('strong');
    title.textContent = 'Chart preview unavailable';
    const detail = document.createElement('span');
    detail.textContent = message || 'Check the local prototype files and reload the page.';
    box.append(title, detail);
    host.replaceChildren(box);
    host.setAttribute('aria-busy', 'false');
    return false;
  }

  function validChartValue(value) {
    return typeof value === 'number' && Number.isFinite(value) && value >= 0 && value <= 10;
  }

  function validateLineRows(rows) {
    if (rows === null || rows === undefined) return 'Chart data is missing.';
    if (!Array.isArray(rows)) return 'Chart data must be a list of rows.';
    if (rows.length === 0) return 'empty';
    let previousStep = -Infinity;
    for (const row of rows) {
      if (!row || typeof row !== 'object' || !Number.isFinite(row.step) || !validChartValue(row.value)) {
        return 'Each row needs a numeric step and a finite value from 0 to 10.';
      }
      if (row.step <= previousStep) return 'Steps must be provided in increasing order.';
      previousStep = row.step;
    }
    return null;
  }

  function validateBarRows(rows) {
    if (rows === null || rows === undefined) return 'Chart data is missing.';
    if (!Array.isArray(rows)) return 'Chart data must be a list of rows.';
    if (rows.length === 0) return 'empty';
    for (const row of rows) {
      if (!row || typeof row !== 'object' || typeof row.category !== 'string' || !row.category.trim() ||
          !validChartValue(row.seriesA) || !validChartValue(row.seriesB)) {
        return 'Each row needs a category and finite series values from 0 to 10.';
      }
    }
    return null;
  }

  function validateScatterRows(rows) {
    if (rows === null || rows === undefined) return 'Chart data is missing.';
    if (!Array.isArray(rows)) return 'Chart data must be a list of points.';
    if (rows.length === 0) return 'empty';
    for (const point of rows) {
      if (!point || typeof point !== 'object' || !validChartValue(point.x) || !validChartValue(point.y)) {
        return 'Each point needs finite numeric X and Y values from 0 to 10 for this sample plot.';
      }
    }
    return null;
  }

  function validateGraph(graph) {
    if (!graph || typeof graph !== 'object') return 'Graph data is missing.';
    if (!Array.isArray(graph.nodes) || !Array.isArray(graph.edges)) return 'Graph nodes and connections must be lists.';
    if (graph.nodes.length === 0) return 'empty';
    if (graph.nodes.length > 5) return 'This example layout supports up to five conceptual nodes.';
    const ids = new Set();
    for (const item of graph.nodes) {
      if (!item || typeof item.id !== 'string' || !item.id.trim() || typeof item.label !== 'string' || !item.label.trim() || ids.has(item.id)) {
        return 'Each graph node needs a unique identifier and a label.';
      }
      ids.add(item.id);
    }
    for (const edge of graph.edges) {
      if (!edge || !ids.has(edge.from) || !ids.has(edge.to) || typeof edge.label !== 'string' || !edge.label.trim()) {
        return 'Each connection must refer to existing nodes and include a label.';
      }
    }
    return null;
  }

  function drawLine(host, rows, showTip) {
    const issue = validateLineRows(rows);
    if (issue === 'empty') return showEmpty(host);
    if (issue) return showError(host, issue);
    const width = 560, height = 260;
    const bounds = { left: 54, right: 544, top: 20, bottom: 202 };
    const svg = baseChart(host, 'Synthetic sample index by step', 'Line chart of synthetic, unitless sample values across ordered steps. This is not mission data.', width, height);
    grid(svg, bounds, 10, 5);
    const points = rows.map((row, index) => ({ x: bounds.left + index * ((bounds.right - bounds.left) / Math.max(1, rows.length - 1)), y: bounds.bottom - (row.value / 10) * (bounds.bottom - bounds.top), row }));
    svg.appendChild(el('path', { d: points.map((p, i) => `${i ? 'L' : 'M'} ${p.x} ${p.y}`).join(' '), class: 'line-series' }));
    points.forEach(({ x, y, row }) => {
      text(svg, `Step ${row.step}`, x, bounds.bottom + 21, 'chart-tick');
      addTooltipMark(svg, 'circle', { cx: x, cy: y, r: 5.5, class: 'line-dot' }, `Step ${row.step}, sample index ${row.value}, unitless`, `Step ${row.step} · ${row.value} unitless`, showTip);
    });
    axisTitles(svg, 'Ordered sample step', 'Sample index (unitless)', width, height, bounds);
    host.replaceChildren(svg);
    host.setAttribute('aria-busy', 'false');
    return true;
  }

  function drawBars(host, rows, showTip) {
    const issue = validateBarRows(rows);
    if (issue === 'empty') return showEmpty(host);
    if (issue) return showError(host, issue);
    const width = 520, height = 260;
    const bounds = { left: 47, right: 506, top: 20, bottom: 202 };
    const svg = baseChart(host, 'Synthetic sample category comparison', 'Grouped bar chart comparing Series A and Series B across placeholder categories. Values are unitless synthetic examples.', width, height);
    grid(svg, bounds, 10, 5);
    const groupWidth = (bounds.right - bounds.left) / rows.length;
    const barWidth = Math.min(30, groupWidth * 0.24);
    rows.forEach((row, index) => {
      const center = bounds.left + groupWidth * (index + 0.5);
      text(svg, row.category, center, bounds.bottom + 21, 'chart-tick');
      [[row.seriesA, 'Series A', BLUE, -barWidth / 2], [row.seriesB, 'Series B', TEAL, barWidth / 2]].forEach(([value, name, color, offset]) => {
        const x = center + offset - barWidth / 2;
        const y = bounds.bottom - (value / 10) * (bounds.bottom - bounds.top);
        const barHeight = bounds.bottom - y;
        addTooltipMark(svg, 'rect', { x, y, width: barWidth, height: barHeight, rx: 4, fill: color, class: name === 'Series A' ? 'bar-series-a' : 'bar-series-b' }, `Category ${row.category}, ${name}, ${value} unitless`, `${name} · Category ${row.category} · ${value} unitless`, showTip);
      });
    });
    axisTitles(svg, 'Sample category', 'Sample score (unitless)', width, height, bounds);
    host.replaceChildren(svg);
    host.setAttribute('aria-busy', 'false');
    return true;
  }

  function drawScatter(host, rows, showTip) {
    const issue = validateScatterRows(rows);
    if (issue === 'empty') return showEmpty(host);
    if (issue) return showError(host, issue);
    const width = 560, height = 260;
    const bounds = { left: 54, right: 544, top: 20, bottom: 202 };
    const svg = baseChart(host, 'Synthetic sample point plot', 'Scatter plot of synthetic, unitless X and Y sample pairs. The display range is 0 to 10 for practice. This example does not establish causation or describe mission data.', width, height);
    grid(svg, bounds, 10, 5);
    for (let i = 0; i <= 5; i += 1) {
      const value = i * 2;
      const x = bounds.left + (value / 10) * (bounds.right - bounds.left);
      svg.appendChild(el('line', { x1: x, y1: bounds.top, x2: x, y2: bounds.bottom, class: i === 0 ? 'chart-axis' : 'chart-gridline' }));
      text(svg, String(value), x, bounds.bottom + 17, 'chart-tick');
    }
    rows.forEach((point, index) => {
      const x = bounds.left + (point.x / 10) * (bounds.right - bounds.left);
      const y = bounds.bottom - (point.y / 10) * (bounds.bottom - bounds.top);
      addTooltipMark(svg, 'circle', { cx: x, cy: y, r: 6, class: 'scatter-dot' }, `Sample point ${index + 1}: X ${point.x}, Y ${point.y}; unitless`, `Point ${index + 1} · X ${point.x} · Y ${point.y} (unitless)`, showTip);
    });
    axisTitles(svg, 'X value (unitless)', 'Y value (unitless)', width, height, bounds);
    host.replaceChildren(svg);
    host.setAttribute('aria-busy', 'false');
    return true;
  }

  function drawRelationshipGraph(host, graph, showTip) {
    const issue = validateGraph(graph);
    if (issue === 'empty') return showEmpty(host);
    if (issue) return showError(host, issue);
    const width = 560, height = 330;
    const positions = [
      { x: 280, y: 55 }, { x: 145, y: 145 }, { x: 415, y: 145 },
      { x: 155, y: 260 }, { x: 405, y: 260 }
    ];
    const svg = baseChart(host, 'Conceptual relationship graph', 'Illustrative links among Mission, Spacecraft, Payload, Resources, and Simulation concepts. The relationships are placeholders, not a confirmed product data model or mission facts.', width, height);
    const lookup = new Map(graph.nodes.map((item, index) => [item.id, { ...item, ...positions[index] }]));

    graph.edges.forEach((edge) => {
      const from = lookup.get(edge.from);
      const to = lookup.get(edge.to);
      const line = el('line', { x1: from.x, y1: from.y, x2: to.x, y2: to.y, class: 'graph-edge' });
      const midX = (from.x + to.x) / 2;
      const midY = (from.y + to.y) / 2 - 5;
      const label = el('text', { x: midX, y: midY, class: 'graph-edge-label', 'text-anchor': 'middle' }, 'example link');
      addTooltipGroup(svg, [line, label], `${from.label} to ${to.label}: ${edge.label.toLowerCase()}`, `${from.label} to ${to.label}: ${edge.label.toLowerCase()}. No confirmed product relationship is implied.`, showTip, 'graph-edge-mark');
    });

    graph.nodes.forEach((item, index) => {
      const point = lookup.get(item.id);
      const x = point.x - 62;
      const y = point.y - 22;
      const rect = el('rect', { x, y, width: 124, height: 44, rx: 10, class: `graph-node graph-node-${index % 2}` });
      const ring = el('rect', { x: x - 3, y: y - 3, width: 130, height: 50, rx: 12, class: 'chart-focus-ring' });
      const label = el('text', { x: point.x, y: point.y + 5, class: 'graph-node-label', 'text-anchor': 'middle' }, item.label);
      addTooltipGroup(svg, [ring, rect, label], `Conceptual node: ${item.label}`, `${item.label}. Illustrative concept only; no mission data.`, showTip, 'graph-node-mark');
    });

    host.replaceChildren(svg);
    host.setAttribute('aria-busy', 'false');
    return true;
  }

  function tooltipFor(card) {
    const tooltip = card.querySelector('.chart-tooltip');
    return function showTip(message, event, mark) {
      if (!message) { tooltip.hidden = true; return; }
      tooltip.textContent = message;
      tooltip.hidden = false;
      const cardRect = card.getBoundingClientRect();
      const markRect = mark.getBoundingClientRect();
      const x = event ? event.clientX - cardRect.left : markRect.left - cardRect.left + markRect.width / 2;
      const y = event ? event.clientY - cardRect.top : markRect.top - cardRect.top;
      tooltip.style.left = `${Math.max(110, Math.min(cardRect.width - 110, x))}px`;
      tooltip.style.top = `${Math.max(54, y)}px`;
    };
  }

  window.arc09Charts = {
    renderLine(host, rows) {
      try { return drawLine(host, rows, tooltipFor(host.closest('.chart-panel'))); }
      catch (error) { console.error(error); return showError(host); }
    },
    renderBars(host, rows) {
      try { return drawBars(host, rows, tooltipFor(host.closest('.chart-panel'))); }
      catch (error) { console.error(error); return showError(host); }
    },
    renderScatter(host, rows) {
      try { return drawScatter(host, rows, tooltipFor(host.closest('.chart-panel'))); }
      catch (error) { console.error(error); return showError(host); }
    },
    renderRelationshipGraph(host, graph) {
      try { return drawRelationshipGraph(host, graph, tooltipFor(host.closest('.chart-panel'))); }
      catch (error) { console.error(error); return showError(host); }
    }
  };
}());
