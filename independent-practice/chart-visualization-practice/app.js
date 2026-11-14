/* Connects the separate data module to reusable chart renderers and tables. */
(function () {
  const data = window.practiceData;

  function fillTable(bodyId, rows, cells) {
    const body = document.getElementById(bodyId);
    if (!body || !rows.length) return;
    body.replaceChildren(...rows.map((row) => {
      const tr = document.createElement('tr');
      cells(row).forEach((value) => {
        const td = document.createElement('td');
        td.textContent = String(value);
        tr.appendChild(td);
      });
      return tr;
    }));
  }

  function tooltipFor(card) {
    const tooltip = card.querySelector('.chart-tooltip');
    return function showTooltip(text, event, mark) {
      if (!tooltip) return;
      if (!text) { tooltip.hidden = true; return; }
      tooltip.textContent = text;
      tooltip.hidden = false;
      const cardRect = card.getBoundingClientRect();
      const anchor = event ? { x: event.clientX, y: event.clientY } : mark.getBoundingClientRect();
      const x = event ? anchor.x - cardRect.left : anchor.left - cardRect.left + anchor.width / 2;
      const y = event ? anchor.y - cardRect.top : anchor.top - cardRect.top;
      tooltip.style.left = `${Math.max(95, Math.min(cardRect.width - 95, x))}px`;
      tooltip.style.top = `${Math.max(56, y)}px`;
    };
  }

  function start() {
    if (!data || !window.practiceCharts) {
      document.querySelectorAll('[data-chart]').forEach((container) => {
        container.innerHTML = '<div class="chart-error" role="alert"><strong>Chart could not be loaded</strong><span>Check that all project files are together, then refresh.</span></div>';
        container.setAttribute('aria-busy', 'false');
      });
      return;
    }

    fillTable('line-table', data.line, (row) => [`Step ${row.step}`, row.value]);
    fillTable('bar-table', data.grouped, (row) => [row.category, row.seriesA, row.seriesB]);
    fillTable('scatter-table', data.scatter, (row) => [row.x, row.y]);

    document.querySelectorAll('[data-chart]').forEach((container) => {
      const card = container.closest('.chart-card');
      const kind = container.dataset.chart;
      const rows = kind === 'line' ? data.line : kind === 'bar' ? data.grouped : data.scatter;
      window.practiceCharts.render(container, kind, rows, tooltipFor(card));
    });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();
}());
