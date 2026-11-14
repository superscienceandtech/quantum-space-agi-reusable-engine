# ARC-09 Independent UI Prototype

This is an isolated visual prototype for reviewing a proposed mission-workspace dashboard. It is not the Quantum Space AGI production application, does not use NASA data, and does not implement confirmed mission requirements.

## Run

Open `index.html` in a modern browser. No packages, network requests, framework, build step, or installation are required. Keep the files in this folder together.

## Project files

- `index.html` — Semantic app shell, proposed navigation, dashboard cards, four visualization panels, accessible data alternatives, activity list, and component-state preview.
- `styles.css` — Supplied ARC-09 color baseline, 4 px spacing tokens, responsive layouts, focus styles, and component patterns.
- `data.js` — Synthetic layout-review values, unitless chart points, and explicitly conceptual graph examples.
- `data-provider.js` — Synchronous prototype-only `getData()` boundary that returns the existing frozen fixture from `data.js` unchanged; it performs no I/O and is not a production API client or DTO adapter.
- `data-validation.js` — Prototype presentation-shape/type checks; not an authoritative backend DTO/schema validator.
- `data-validation.test.html` — Isolated browser test page for fixture/provider reference preservation and prototype-validator cases; not a production application page.
- `startup-rejection.test.html` — Isolated browser test page with a test-only rejecting provider for startup failure cleanup; not a production application page.
- `startup-invalid-data.test.html` — Isolated browser test page whose test provider resolves malformed data and whose test-only validator spy delegates to the loaded validator; not a production application page.
- `charts.js` — Reusable SVG line, grouped-bar, scatter, and relationship-graph renderers with validation, keyboard-focusable interactive marks, tooltips, and accessible SVG descriptions.
- `app.js` — Acquires data through the prototype provider (synchronous or Promise-returning), validates the prototype presentation shape before rendering, handles operational loading and startup failures, renders the dashboard and chart/graph tables, filters activity, and previews feedback states.
- `README.md` — Prototype scope, run instructions, and verification limitations.

## Prototype data provider

`index.html` loads the synthetic fixture (`data.js`), prototype provider (`data-provider.js`), chart renderers (`charts.js`), prototype data validator (`data-validation.js`), and application (`app.js`) in that order. `app.js` obtains the same fixture object through `arc09PrototypeProvider.getData()` rather than reading the fixture global directly. The provider is synchronous and only separates this prototype's fixture source from rendering; it does not fetch data, transform the fixture, define API fields, or establish a production contract. If the provider or fixture is unavailable, the app shows a startup error and clears the dashboard data regions instead of inventing replacement data.

This boundary is a prototype preparation seam only. Any future backend transport, DTO mapping, validation policy, authentication, and production UI state behavior require an approved frontend target and authoritative API contract.

## Day 5 and Day 6 practice visualizations

- **Line chart:** synthetic unitless sample index over ordered practice steps.
- **Grouped bar chart:** two synthetic unitless series across placeholder categories, with a legend.
- **Scatter plot:** synthetic unitless X/Y pairs. A plotted pattern does not establish causation.
- **Relationship graph:** conceptual Mission, Spacecraft, Payload, Resources, and Simulation nodes connected by generic illustrative associations. It is not a confirmed product data model.

Each visualization has an accessible title and description, focusable interactive marks with value/context tooltips, and a table-based text alternative. Chart input validation distinguishes missing, empty, and invalid values. The scatter's 0–10 plotting range and the line/bar sample range are display rules for these practice charts, not scientific thresholds.

## Interactions

- Select Dashboard or a proposed view from the sidebar. Non-dashboard views show an explicit placeholder, not a claimed product feature.
- At narrow widths, use the menu button to open navigation; Escape or the backdrop closes it.
- Filter synthetic activity entries and switch among loading, empty, and error visual-state examples.
- Focus chart marks or graph nodes/connections with the keyboard to reveal tooltips. Use each visualization's disclosure to inspect its text/table alternative.

All displayed names, counts, allocations, activity, chart values, nodes, and links are synthetic or conceptual examples. Percentage values do not represent actual resources, limits, or mission results. The graph relationships are illustrative only.

## Verification and limitations

Source-level checks are recorded in `STATIC_AUDIT.md`. The following results were reported by the user and were not independently reproduced for this documentation update: normal dashboard startup, operational loading indicator dismissal, metric-card and chart rendering, activity filtering, and no new browser Console errors. The user also reported the data-validation harness at 10/10 PASS, the rejected-Promise startup test PASS, and the invalid-resolved-data startup test PASS. These reports are not independent browser automation evidence.

The user reported running JavaScript syntax checks with Cursor Node v24.22.1; `app.js`, `charts.js`, `data-provider.js`, and `data-validation.js` each exited with code 0. These are user-run checks, not checks performed for this documentation update. Responsive visual review, keyboard behavior, accessibility-tree output, and screen-reader/assistive-technology testing are not established by these results. The manual verification report records a user-reported `favicon.ico` 404 warning. The exact request URL, current server response, and present status have not been independently verified; this does not establish that the issue is fixed or currently reproducible.

No API, persistence, authentication, simulation, production routing, or real mission data is included. The six proposed navigation destinations are not confirmed requirements. This prototype is not production-ready.
