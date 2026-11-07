# ARC-09 Prototype Static Source Audit

**Scope:** Initial source inspection and remediation record for the prototype. No JavaScript was executed and no browser was launched. The original findings below describe the pre-fix source; remediation status is recorded at the end. This remains a static review, not a runtime or accessibility conformance test.

## Summary

| Area | Result | Notes |
|---|---|---|
| HTML structure and accessibility source | PASS after source fixes | Semantic landmarks, heading structure, chart descriptions, table alternatives, and a skip link are present. All navigation fragment targets now map to page IDs. |
| CSS tokens and responsive rules | PASS with source fixes; rendering not verified | Referenced custom properties remain defined; responsive breakpoints, focus styles, reduced-motion rules, closed-drawer visibility, and selected text-size adjustments are present. |
| JavaScript source consistency | PASS by source inspection | Selector and route references match HTML; chart data validation and invalid-table handling are present. |
| Scientific/data integrity | PASS | Data and views are explicitly labeled as synthetic/proposed; no NASA data, real mission outputs, or scientific thresholds are claimed. |
| Runtime and browser behavior | NOT VERIFIABLE | Static inspection cannot establish rendering, actual focus behavior, console state, or screen-reader behavior. |

No Critical or High severity issue was identified in this static review.

## Findings

### HTML

1. **PASS — Semantic document and landmarks** (`index.html:1-13,29-33,49-55,118-125`): The document declares English and UTF-8, includes a viewport declaration, a skip link, a header, labeled navigation, a main landmark, and labeled page sections.

2. **PASS — IDs and JavaScript ID references** (`index.html:15,30-31,49,55,59,69,75,84-85,87,93-94,96,103-105,114,121-123`; `app.js:53,66,88,103-104,115,118,122-124,135-137,148-150,168,174,176,180-181,185,195,200,203,207,209`): Static comparison found no duplicate HTML IDs and no `getElementById` target in `app.js` missing from the HTML.

3. **ISSUE — Navigation links point to absent fragment IDs** — **Severity: Medium** (`index.html:18,34-39,55,121`; `app.js:102-119,194-199,212-213`): The brand and six navigation links use fragments such as `#dashboard` and `#mission-builder`, but no element has those IDs. JavaScript currently interprets the fragment and swaps the dashboard/placeholder content, but the links are not valid native fragment destinations and depend on JavaScript for their intended navigation. **Recommended correction:** use real destination IDs or implement navigation with controls and routing semantics whose destinations are explicitly represented; keep direct-link behavior consistent.

4. **PASS — Form label and accessible names** (`index.html:15,18,31-33,103,109-112`): The menu button has an accessible label and controls reference; the activity select has an associated `<label>`; state preview buttons have visible text. The select's extra `aria-label` is redundant but not contradictory.

5. **PASS — Heading outline and chart/table alternatives** (`index.html:55-60,65-68,77-83,87,90-96,101-109,121-123`; `charts.js:14-20,72,78-80,89,100,103`): One page-level `h1` is present for each view state, followed by section and chart headings. The SVGs receive title/description references, and each chart has an expandable HTML data table with a caption and column headers.

6. **ISSUE — Generic elements carry labels without an explicit group role** — **Severity: Low** (`index.html:69,75`; `app.js:43-47`): The overview and resource grid `div`s have `aria-label` attributes without an explicit landmark/group role. The resource progress graphic receives `role="img"`, but its percentage is constructed from a literal `%` rather than the data's `unit` field. The present synthetic data uses `%`, so the current example is consistent; the generic rendering pattern could diverge if data changes. **Recommended correction:** give labeled containers an appropriate semantic role/section label, and derive the accessible text from the same displayed value and unit.

### CSS

7. **PASS — Custom properties and supplied design tokens** (`styles.css:1`): All `var(--...)` references have corresponding definitions. Primary, secondary, background, surface, text, muted, border, status colors, and a 4 px spacing scale are defined. Several declared tokens (status colors and spacing tokens) are currently unused; this is not a broken reference.

8. **PASS — Responsive and overflow handling** (`styles.css:2,4-6`): Layout changes are defined at 1100 px, 760 px, and 540 px. Grid columns collapse at narrow widths, main content permits shrinking, and chart tables use a horizontally scrollable wrapper. `html` and `body` have a 320 px minimum width, so widths below 320 px can scroll horizontally by design. Actual overflow at target viewports is **NOT VERIFIABLE** without rendering.

9. **ISSUE — Mobile sidebar's visual hiding is not represented in CSS as an accessibility hidden state** — **Severity: Medium** (`styles.css:5`; `index.html:15,31-40`; `app.js:121-163,166-172,204`): On mobile the sidebar is moved off-canvas with `transform`. `inert` and `aria-hidden` are synchronized only after JavaScript starts. If JavaScript is unavailable or `start()` exits at the missing-data/chart guard before navigation synchronization, the visually hidden links may remain exposed to keyboard or assistive-technology navigation. **Recommended correction:** ensure the closed mobile state is inaccessible as well as off-canvas, and initialize it before any early-return path; verify both no-script/failure and normal states in a browser.

10. **PASS with limitation — Focus and reduced motion rules** (`styles.css:2,5-7`): Focus-visible styling is explicitly provided for links, buttons, summaries, and the select class; the activity select retains the browser's default focus outline because it does not have that class. Reduced-motion preferences shorten transitions and disable animated duration. These rules' appearance and behavior have not been rendered or tested.

11. **ISSUE — Several secondary labels use very small type** — **Severity: Low** (`styles.css:1-2,5-6`; especially chart labels, captions, chips, table text, and metadata on line 2): Font sizes from 8–12 px are used for information that may be needed to understand charts and status. Contrast alone does not address legibility at small sizes or zoom. **Recommended correction:** review chart ticks, table content, captions, and status text at 200% zoom and narrow widths; increase sizes where information becomes difficult to read.

12. **PASS — Supplied foreground/background pairs checked from source** (`styles.css:1-2`): Calculated contrast for the main text `#0F172A` on `#F8FAFC` is 17.06:1; muted `#475569` on white is 7.58:1; secondary `#0F766E` on white is 5.47:1; primary `#1D4ED8` on white is 6.70:1; and several label pairs also exceed 4.5:1. This check covers the named static pairs only; it does not validate every state, opacity, focus ring, chart element, or rendered color combination.

### JavaScript and data

13. **PASS — Naming and selector consistency** (`app.js:13-23,25-34,36-50,52-63,65-85,87-100,102-164`; `charts.js:7-21,23-41,43-66,68-106,108-132`): Function names are descriptive and consistent with their roles. Static selector checks found no missing ID targets. The HTML state values match the preview-state keys; view names match the `data-view` values in the navigation.

14. **PASS — Synthetic chart and table data mappings** (`data.js:12-23`; `app.js:178-181`; `charts.js:68-106`; `index.html:87,96`): The line chart and line table both use `data.trend` (`step`, `value`); the grouped bars and bar table both use `data.comparison` (`category`, `seriesA`, `seriesB`). The provided rows are ordered and contain finite numeric values within the chart's fixed 0–10 plotting scale.

15. **ISSUE — Chart routines catch exceptions but do not validate malformed values** — **Severity: Medium** (`charts.js:58-66,68-82,85-106,123-131`): Empty arrays are handled, and thrown errors show an error state. However, a non-finite or out-of-range value can be converted into invalid SVG coordinates or drawn outside the fixed 0–10 scale without triggering an exception. Rows with missing fields are likewise not rejected explicitly. **Recommended correction:** before drawing, validate the expected row shape and finite numeric values, define handling for out-of-range values without inventing domain thresholds, and show a clear error state for invalid input.

16. **PASS — Safe text construction in normal render paths** (`app.js:13-17,52-62,74-82,87-99`; `charts.js:7-11,23-25`): Data labels and tooltip/chart text are assigned with `textContent` or SVG text nodes. Static examples do not interpolate sample strings into HTML. Fixed local state/error markup uses `innerHTML` (`app.js:167-170`; `charts.js:58-65`) and contains only hard-coded strings.

17. **PASS — Navigation and focus behavior in source** (`app.js:102-164,194-213`): Navigation updates current-page state; opening the mobile menu focuses the active link; Escape closes the menu and returns focus to the toggle; resizing synchronizes desktop/mobile attributes. **ISSUE — Medium** (`app.js:134-145,203`): Closing from the backdrop does not explicitly restore focus to the toggle, and the source does not keep keyboard focus inside the open off-canvas drawer. Because the backdrop suggests an overlay, assess whether the drawer should behave as a modal. **Recommended correction:** define the intended drawer interaction and consistently manage focus on every close path; verify with keyboard and assistive technology.

18. **NOT VERIFIABLE — Event behavior and runtime error handling** (`app.js:185-217`; `charts.js:43-55,123-131`): Listener targets correspond to present controls, but source inspection cannot prove listeners run, tooltip positioning is correct, hash navigation works in-browser, missing-file handling succeeds, or no console errors occur.

### Scientific and product integrity

19. **PASS — Synthetic data and non-production scope are clearly disclosed** (`index.html:20,24,44,46,50-53,62,67,72-79,86,95,102-108,118,121-123`; `data.js:1-2,9-10,25-28`; `README.md:3,20-25,27-29`): The prototype identifies itself as independent/conceptual, describes synthetic values and sample allocations, calls the six destinations proposed, and states that no live or actual mission data is shown.

20. **PASS — No scientific thresholds, actual simulation results, or NASA data claims found** (`data.js:1-29`; `index.html:50-52,72-79,86,95,123`; `README.md:3,25,29`): Values are described as illustrative/unitless or synthetic allocations with no limits implied. Placeholder views state that confirmed requirements and scientific fields are absent. No API contract or scientific model is represented.

## Remediation log



### Original finding 3: navigation fragment targets

**Status: FIXED in source.** Each navigation link fragment now matches an actual page section ID (`index.html:55,121,125,129,133,137`). The route keys and `data-page` values correspond, while the five non-dashboard sections continue to show placeholder content only. `app.js:102-115,168-207` selects the requested page and keeps `aria-current` synchronized. Static ID review found no duplicates, missing href targets, stale direct ID references, or route/page mismatches.

### Original finding 6: labeled group and unit text

**Status: FIXED in source.** The overview and resource containers now have `role="group"` (`index.html:69,75`). The resource graphic's accessible label is composed from the same displayed value and unit (`app.js:42-46`).

### Original finding 9: closed mobile drawer state

**Status: FIXED in source.** The closed off-canvas drawer uses `visibility:hidden` in the narrow viewport rules, so its links are not focusable while the visual drawer is closed (`styles.css:5`). `setupNavigation()` synchronizes drawer state before the missing-data early return (`app.js:168-172,210-219`). Closed/open state updates `inert`, `aria-hidden`, the backdrop, `aria-expanded`, and the trigger label (`app.js:118-166`).

### Original finding 11: small text

**Status: PARTIALLY ADDRESSED in source.** Chart ticks, axis titles, captions, table text, status badges, chart-type labels, sample labels, and activity metadata have selected size increases (`styles.css:2,5-6`). Some tertiary text remains 8-10 px. No browser zoom or narrow-screen legibility check was performed, so actual readability remains unverified.

### Original finding 15: malformed chart datasets

**Status: FIXED in source for the documented chart shape and scale.** Missing data, non-list data, empty lists, absent/wrong fields, non-finite values, line steps not in increasing order, and values outside the chart's displayed 0-10 axis are handled before drawing (`charts.js:68-109,111-135`). Invalid rows produce an accessible error state; empty arrays retain the empty state. The 0-10 check follows the chart's existing axis, not a scientific or mission threshold. Render functions return success, and the corresponding HTML table is cleared when chart data is rejected (`app.js:224-227`).

### Original finding 17: drawer focus management

**Status: FIXED in source; runtime verification remains outstanding.** Opening focuses the active navigation link. Tab and Shift+Tab wrap between the menu trigger and drawer links; Escape and backdrop dismissal restore focus to the trigger. Selecting a navigation link closes the drawer and moves focus to main content. Desktop synchronization removes the mobile hidden state and leaves navigation available (`app.js:118-207`).

### Source-level checks performed after changes

- Every in-page `href` fragment resolves to a unique ID.
- Each navigation link's fragment and `data-view` match a section ID and its `data-page` value.
- Every static `getElementById` reference found in `app.js` resolves to an HTML ID; obsolete page selectors are absent.
- Source branches for missing/empty datasets, required fields, finite numeric values, the displayed 0-10 range, error rendering, and clearing invalid chart tables are present.
- Source branches for mobile closed/open `inert` and `aria-hidden` state, opening focus, Escape/backdrop restoration, Tab focus wrapping, navigation focus transfer, initialization before the data guard, and CSS visibility hiding are present.

These checks compare source text and relationships only. They do not execute the application.

## Updated readiness and remaining limitations

**Isolated prototype source readiness: CONDITIONAL.** The identified static defects are corrected. A real browser check is still needed before claiming responsive behavior, keyboard behavior, focus order, or accessibility has been verified. Tertiary microcopy remains small and needs a visual legibility check.

**Production readiness: NO-GO.** The prototype remains isolated and does not establish approved product requirements, production behavior, or scientific/API contracts.

No JavaScript runtime, browser, screen reader, or automated test suite was used. Rendering, CSS visibility and focus behavior as interpreted by browsers, actual responsive overflow, tooltip positioning, console output, and assistive-technology behavior remain unverified. Files changed for this remediation: `index.html`, `app.js`, `charts.js`, `styles.css`, and this report.

## Day 5/6 visualization follow-up — 2026-11-08

### Source findings and changes reviewed

- Day 5 line and grouped-bar SVG implementations were retained. A scatter plot was added with synthetic unitless X/Y data, axis labels, keyboard/pointer tooltips, a table alternative, and a no-causation notice.
- Day 6 adds a simple SVG graph with Mission, Spacecraft, Payload, Resources, and Simulation concepts. Its generic example links are explicitly illustrative and are not a confirmed product schema. Nodes and connections are keyboard/pointer focusable and have a table text alternative.
- Scatter and graph input paths handle missing, empty, and invalid data. Numeric chart values are checked as finite and against the displayed 0–10 practice range. Graph node IDs are checked for uniqueness and connection endpoints are checked against the supplied node list.
- Responsive CSS includes a taller graph viewport and a smaller mobile height, retaining the existing layout breakpoints.

### Source-level checks performed

- PASS: HTML IDs are unique; internal fragment links, ARIA ID references, label targets, and local CSS/JS references resolve.
- PASS: HTML chart/graph hosts and their table alternatives exist and match the app renderer wiring.
- PASS: renderer functions for line, grouped bar, scatter, and relationship graph are defined and called by `app.js`.
- PASS: source contains finite/range and graph-reference validation branches, plus synthetic-data disclosure.
- PASS: all CSS custom-property references have definitions.
- PASS: `git diff --check` found no content whitespace errors. Git reported its normal LF-to-CRLF working-copy warnings for the edited files; line endings were not normalized.

### Limits and readiness

These checks inspect source only. Python and Node.js were unavailable in the environment, so no JavaScript syntax/runtime test was run. No browser, responsive rendering, tooltip behavior, keyboard interaction, console, or screen-reader verification was performed. Day 5 and Day 6 implementation is present in source, but browser-dependent verification remains outstanding.

**Visualization source readiness: CONDITIONAL — suitable for team source review; browser verification is still needed.** Production readiness remains **NO-GO** because the prototype is not production-integrated and product/API/scientific requirements remain unconfirmed.

Files changed for this follow-up: `index.html`, `styles.css`, `app.js`, `charts.js`, `data.js`, `README.md`, `PROTOTYPE_HANDOFF.md`, `REVIEW_CHECKLIST.md`, `FINAL_REVIEW_SUMMARY.md`, and this report. No files outside `arc09-ui-prototype/` were changed; no Git operations changed the branch or staging area.
