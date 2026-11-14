/* Small reusable SVG chart functions. Data comes from data.js; this file draws it. */
(function () {
  const NS = 'http://www.w3.org/2000/svg';
  const BLUE = '#315bd6';
  const ORANGE = '#c26317';
  const TEAL = '#087f80';

  function svgElement(name, attributes, text) {
    const node = document.createElementNS(NS, name);
    Object.entries(attributes || {}).forEach(([key, value]) => node.setAttribute(key, value));
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function baseSvg(container, title, description, width, height) {
    const svg = svgElement('svg', { viewBox: `0 0 ${width} ${height}`, role: 'group', preserveAspectRatio: 'xMidYMid meet' });
    const titleId = `${container.id}-title`;
    const descId = `${container.id}-description`;
    svg.setAttribute('aria-labelledby', `${titleId} ${descId}`);
    svg.append(svgElement('title', { id: titleId }, title), svgElement('desc', { id: descId }, description));
    return svg;
  }

  function addText(svg, text, x, y, className, anchor) {
    svg.appendChild(svgElement('text', { x, y, class: className, 'text-anchor': anchor || 'middle' }, text));
  }

  function addYGrid(svg, left, right, top, bottom, max, ticks, formatter) {
    for (let i = 0; i <= ticks; i += 1) {
      const value = (max / ticks) * i;
      const y = bottom - (value / max) * (bottom - top);
      svg.appendChild(svgElement('line', { x1: left, y1: y, x2: right, y2: y, class: i === 0 ? 'axis-line' : 'grid-line' }));
      addText(svg, formatter(value), left - 10, y + 3.5, 'tick-label', 'end');
    }
  }

  function addAxesTitles(svg, xTitle, yTitle, width, height, left, top, bottom) {
    addText(svg, xTitle, (left + width - 18) / 2, height - 5, 'axis-title');
    const y = svgElement('text', { x: 14, y: (top + bottom) / 2, class: 'axis-title', 'text-anchor': 'middle', transform: `rotate(-90 14 ${(top + bottom) / 2})` }, yTitle);
    svg.appendChild(y);
  }

  function makeMark(svg, shape, attrs, label, tooltip, callback) {
    const group = svgElement('g', { class: 'chart-mark', tabindex: '0', role: 'img', 'aria-label': label });
    const mark = svgElement(shape, attrs);
    const ring = shape === 'rect'
      ? svgElement('rect', { x: Number(attrs.x) - 3, y: Number(attrs.y) - 3, width: Number(attrs.width) + 6, height: Number(attrs.height) + 6, rx: 4, class: 'focus-ring' })
      : svgElement('circle', { cx: attrs.cx, cy: attrs.cy, r: Number(attrs.r) + 6, class: 'focus-ring' });
    group.append(ring, mark);
    group.addEventListener('pointerenter', (event) => callback(tooltip, event));
    group.addEventListener('pointermove', (event) => callback(tooltip, event));
    group.addEventListener('pointerleave', () => callback('', null));
    group.addEventListener('focus', () => callback(tooltip, null, group));
    group.addEventListener('blur', () => callback('', null));
    svg.appendChild(group);
  }

  function drawLine(container, data, tooltip) {
    const width = 700, height = 260, left = 52, right = 680, top = 20, bottom = 205, max = 10;
    if (!data.length) return empty(container);
    const svg = baseSvg(container, 'Value across ordered steps', 'Line chart. The horizontal axis shows Step 1 through Step 5. The vertical axis shows practice values from zero to ten arbitrary units.', width, height);
    addYGrid(svg, left, right, top, bottom, max, 5, (v) => String(v));
    const points = data.map((d, i) => ({ x: left + i * ((right - left) / Math.max(data.length - 1, 1)), y: bottom - (d.value / max) * (bottom - top), d }));
    const area = `M ${points[0].x} ${bottom} ` + points.map((p) => `L ${p.x} ${p.y}`).join(' ') + ` L ${points[points.length - 1].x} ${bottom} Z`;
    const defs = svgElement('defs');
    const gradient = svgElement('linearGradient', { id: 'lineFill', x1: '0', x2: '0', y1: '0', y2: '1' });
    gradient.append(svgElement('stop', { offset: '0%', 'stop-color': BLUE, 'stop-opacity': '.16' }), svgElement('stop', { offset: '100%', 'stop-color': BLUE, 'stop-opacity': '0' }));
    defs.appendChild(gradient); svg.appendChild(defs);
    svg.appendChild(svgElement('path', { d: area, class: 'line-area' }));
    svg.appendChild(svgElement('path', { d: points.map((p, i) => `${i ? 'L' : 'M'} ${p.x} ${p.y}`).join(' '), class: 'line-path' }));
    points.forEach(({ x, y, d }) => {
      addText(svg, `Step ${d.step}`, x, bottom + 21, 'tick-label');
      makeMark(svg, 'circle', { cx: x, cy: y, r: 5.5, class: 'line-point' }, `Step ${d.step}, value ${d.value} arbitrary units`, `Step ${d.step} · ${d.value} arbitrary units`, tooltip);
    });
    addAxesTitles(svg, 'Ordered step', 'Practice value (arbitrary units)', width, height, left, top, bottom);
    container.replaceChildren(svg); container.setAttribute('aria-busy', 'false');
  }

  function drawGrouped(container, data, tooltip) {
    const width = 520, height = 260, left = 45, right = 505, top = 20, bottom = 205, max = 10;
    if (!data.length) return empty(container);
    const svg = baseSvg(container, 'Compare categories', 'Grouped bar chart comparing Series A and Series B in categories A, B, and C. Values are synthetic practice values.', width, height);
    addYGrid(svg, left, right, top, bottom, max, 5, (v) => String(v));
    const groupWidth = (right - left) / data.length, barWidth = Math.min(30, groupWidth * .25);
    data.forEach((d, i) => {
      const center = left + groupWidth * (i + .5);
      addText(svg, d.category, center, bottom + 21, 'tick-label');
      [[d.seriesA, 'Series A', BLUE, -barWidth / 2], [d.seriesB, 'Series B', ORANGE, barWidth / 2]].forEach(([value, series, color, offset]) => {
        const x = center + offset - barWidth / 2, y = bottom - (value / max) * (bottom - top), h = bottom - y;
        makeMark(svg, 'rect', { x, y, width: barWidth, height: h, rx: 4, fill: color, class: series === 'Series A' ? 'bar-a' : 'bar-b' }, `Category ${d.category}, ${series}, ${value} arbitrary units`, `${series} · Category ${d.category} · ${value} arbitrary units`, tooltip);
      });
    });
    addAxesTitles(svg, 'Category', 'Practice value (arbitrary units)', width, height, left, top, bottom);
    container.replaceChildren(svg); container.setAttribute('aria-busy', 'false');
  }

  function drawScatter(container, data, tooltip) {
    const width = 520, height = 260, left = 52, right = 505, top = 20, bottom = 205, max = 6;
    if (!data.length) return empty(container);
    const svg = baseSvg(container, 'Explore a relationship', 'Scatter plot of five synthetic practice pairs. The points show a loose upward pattern; association does not prove causation.', width, height);
    addYGrid(svg, left, right, top, bottom, max, 6, (v) => String(v));
    for (let value = 1; value <= 5; value += 1) {
      const x = left + (value / max) * (right - left);
      addText(svg, String(value), x, bottom + 19, 'tick-label');
    }
    data.forEach((d) => {
      const x = left + (d.x / max) * (right - left), y = bottom - (d.y / max) * (bottom - top);
      makeMark(svg, 'circle', { cx: x, cy: y, r: 7, class: 'scatter-point' }, `X ${d.x}, Y ${d.y}, arbitrary units`, `X ${d.x} · Y ${d.y} arbitrary units`, tooltip);
    });
    addAxesTitles(svg, 'X (arbitrary units)', 'Y (arbitrary units)', width, height, left, top, bottom);
    container.replaceChildren(svg); container.setAttribute('aria-busy', 'false');
  }

  function empty(container) {
    container.innerHTML = '<div class="chart-empty" role="status"><strong>No practice data available</strong><span>This chart needs at least one data point.</span></div>';
    container.setAttribute('aria-busy', 'false');
  }

  function showError(container) {
    container.innerHTML = '<div class="chart-error" role="alert"><strong>Chart could not be displayed</strong><span>Refresh the page to try again.</span></div>';
    container.setAttribute('aria-busy', 'false');
  }

  window.practiceCharts = {
    render(container, kind, data, tooltip) {
      try {
        if (!container || !Array.isArray(data)) throw new Error('Chart input is unavailable');
        if (kind === 'line') drawLine(container, data, tooltip);
        else if (kind === 'bar') drawGrouped(container, data, tooltip);
        else if (kind === 'scatter') drawScatter(container, data, tooltip);
        else throw new Error('Unknown chart type');
      } catch (error) {
        console.error(error);
        if (container) showError(container);
      }
    }
  };
}());
