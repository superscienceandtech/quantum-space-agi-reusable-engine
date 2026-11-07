# ARC-09 Independent UI Prototype

This is an isolated visual prototype for reviewing a proposed mission-workspace dashboard. It is not the Quantum Space AGI production application, does not use real NASA data, and does not implement confirmed mission requirements.

## Run

Open `index.html` in a modern browser. No packages, network requests, framework, build step, or installation are required. Keep the six files together in this folder.

## Project files

- `index.html` — Semantic app shell, proposed navigation, dashboard cards, chart sections, tables, activity list, and component-state preview.
- `styles.css` — Supplied ARC-09 color baseline, 4 px spacing tokens, responsive layouts, focus styles, and component patterns.
- `data.js` — Clearly labeled synthetic values used only for this visual prototype.
- `charts.js` — Reusable SVG line/bar presentation with accessible titles/descriptions, keyboard-focusable marks, and tooltips.
- `app.js` — Renders the sample UI, filters sample activity, previews feedback states, and handles proposed-view navigation.
- `README.md` — Prototype scope and run instructions.

## Interactions

- Select Dashboard or a proposed view from the sidebar. Non-dashboard views show an explicit placeholder, not a claimed product feature.
- At narrow widths, use the menu button to open navigation; Escape or the backdrop closes it.
- Filter synthetic activity entries and switch among loading, empty, and error visual-state examples.
- Focus chart points or bars with the keyboard to reveal their value descriptions. Use each chart’s table disclosure to inspect exact values.

All displayed names, counts, allocations, activity and chart values are synthetic layout-review examples. Percentage values describe sample allocation shares only; they do not represent actual resources, limits, or mission results.

## Limitations

There is no API, persistence, authentication, simulation, production routing, or real mission data. The six proposed navigation destinations are not confirmed requirements. This prototype is not production-ready.
