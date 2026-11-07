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
    }
  };
}());
