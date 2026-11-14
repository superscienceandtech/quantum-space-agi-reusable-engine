# ARC-09 Independent UI Prototype

This is an isolated visual prototype for reviewing a proposed mission-workspace dashboard. It is not the Quantum Space AGI production application, does not use NASA data, and does not implement confirmed mission requirements.

## Run

Open `index.html` in a modern browser. No packages, network requests, framework, build step, or installation are required. Keep the files in this folder together.

## Project files

- `index.html` — Semantic app shell, proposed navigation, dashboard cards, four visualization panels, accessible data alternatives, activity list, and component-state preview.
- `styles.css` — Supplied ARC-09 color baseline, 4 px spacing tokens, responsive layouts, focus styles, and component patterns.
- `data.js` — Synthetic layout-review values, unitless chart points, and explicitly conceptual graph examples.
- `charts.js` — Reusable SVG line, grouped-bar, scatter, and relationship-graph renderers with validation, keyboard-focusable interactive marks, tooltips, and accessible SVG descriptions.
- `app.js` — Renders the sample UI, filters sample activity, previews feedback states, fills chart/graph tables, and handles proposed-view navigation.
- `README.md` — Prototype scope, run instructions, and verification limitations.

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

Source-level checks are recorded in `STATIC_AUDIT.md`. They do not execute JavaScript or establish browser rendering. Browser/runtime, responsive visual, console, keyboard interaction, and screen-reader testing remain unverified. No API, persistence, authentication, simulation, production routing, or real mission data is included. The six proposed navigation destinations are not confirmed requirements. This prototype is not production-ready.
