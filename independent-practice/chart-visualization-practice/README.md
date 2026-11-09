# Chart Lab — Data Visualization Practice

A small, standalone frontend for practicing three interactive chart types. This folder is independent of the Quantum Space AGI application. All chart values are **synthetic practice data — not real mission data**.

## Run it

No package install, build step, Node.js, or chart library is required. Open `index.html` in a modern browser. Keep all five project files in the same folder so the browser can load the styles, data, and chart scripts.

## Project structure

- `index.html` — Dashboard content, chart cards, notices, and accessible data-table disclosures.
- `styles.css` — Responsive layout, colors, typography, and SVG chart styling.
- `data.js` — Synthetic values kept separate from chart presentation.
- `charts.js` — Reusable SVG chart drawing functions and empty/error states.
- `app.js` — Connects data to charts, builds the tables, and controls interactive tooltips.

## How the charts work

The chart functions create SVG elements in the browser. SVG is a web format made of shapes and text, so it stays sharp when resized. Each point or bar can receive keyboard focus; focus or pointer hover shows its value in a tooltip. Each chart also has a title, description, and a table containing the exact values.

- **Line chart:** Plots five ordered practice steps. The connected line makes the change across steps easy to see.
- **Grouped bar chart:** Draws two adjacent bars for each category so the series can be compared. Shape placement and labels support comparison in addition to color.
- **Scatter plot:** Draws one point for each X/Y pair. The page notes that an observed relationship does not establish cause.

The synthetic numeric examples use arbitrary units. They are for learning chart mechanics only and do not represent physical measurements.

## Change the data

Edit the arrays in `data.js`, keeping the property names used by `app.js` and `charts.js`. The chart code reads those arrays and redraws the visualization and table when the page loads.

## Dependencies and checks

There are no runtime or development package dependencies, network requests, or external fonts. The page uses system font stacks.

The project can be opened directly as a static page. If a browser developer console is available, check it for errors after loading. No automated build or browser test is configured.
