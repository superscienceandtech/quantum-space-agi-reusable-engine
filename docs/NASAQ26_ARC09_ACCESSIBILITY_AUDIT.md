# NASAQ26 ARC-09 Accessibility Audit

**Status: B. CONDITIONALLY READY — local error messaging verified; accessibility and acceptance checks remain**

This focused audit covers the current ARC-09 prototype, the owner-authorized D-01/D-02/D-03 changes, and the separately authorized local Mission Builder error-presentation fix. It is not a WCAG conformance audit. Screen-reader behavior was not tested.

**Finalization pass:** 2026-11-15. D-01/D-02/D-03 browser and DOM checks were retained. Under the Project Owner's later explicit authorization, the local Mission Builder error handling and status semantics were fixed in `mission-demo.js` and verified with Chrome-backed regressions. Screen-reader and formal handover acceptance remain pending.

## Scope and evidence

Reviewed current source in [index.html](../arc09-ui-prototype/index.html), [app.js](../arc09-ui-prototype/app.js), [charts.js](../arc09-ui-prototype/charts.js), [styles.css](../arc09-ui-prototype/styles.css), and [mission-demo.js](../arc09-ui-prototype/mission-demo.js); ran the Chrome-backed [visualization regression tests](../tests/mission_demo/test_arc09_visualization.py) and the [Mission Builder error regressions](../tests/mission_demo/test_frontend_error_handling.py); and used the integrated browser at 1440, 1024, 768, 500, and 375 CSS pixels. Browser screenshots were captured in-session; no image files were added to the repository.

## Findings

### SVG graph name, description, and relationship context

- `baseChart` creates an SVG `role="group"` and labels it with an SVG `<title>` and `<desc>` through `aria-labelledby`.
- `renderRelationshipGraph` and `addTooltipGroup` provide each relationship as a focusable `role="img"` with an accessible name in `source to target: relationship` form. Names are taken from existing graph data. The graph description explicitly says these are illustrative placeholder relationships, not a confirmed product data model or mission facts.
- A graph table text alternative is available in the dashboard's expandable details section.
- Browser accessibility snapshots exposed the graph title/description and source-target names. No label was observed to be invented or mapped to the wrong edge in the focused fixture.
- In the current Chromium accessibility tree, the SVG group name contains both the `<title>` and `<desc>`, and its four edge children are named `img` nodes with their source, target, and supplied relationship labels.

### Keyboard access and focus

- At 375px, keyboard traversal reached all four dashboard edges. Each edge exposed a visible focus treatment, its actual relationship name, and a visible status tooltip.
- Repeated with real Tab key navigation in this finalization pass at 375px: all four edges were reached in order, and each had `:focus-visible`, a visible label inside the scroller, and a visible tooltip.
- On the narrow layout, a focused edge now scrolls its relationship label into the visible graph host. This behavior is covered by a regression test that fails if an off-screen label stays hidden.
- The mobile navigation was exercised with Enter and Escape. Opening moved focus into the navigation and synchronized its open state. Closing restored focus to the trigger and reinstated `aria-hidden="true"` and `inert`.
- The prototype has visible `:focus-visible` styling for graph edges and relevant controls. This was checked at runtime for the graph edge and mobile navigation; this is not a full keyboard audit of every view/control.

### Contrast and text size

- The graph edge line and label text render in `#475569` against a white panel. The current computed contrast for both pairs is **7.58:1**. The browser test requires graph-edge contrast of at least 3:1. This measurement is limited to these specific color pairs.
- The finalization browser pass recalculated graph-label text contrast as **7.58:1** against its chart-panel background.
- Focused graph edges use the darker `--text` stroke and a thicker line.
- Edge labels remain **11px**. A 12px trial introduced a node collision in the dense graph fixture, so the font was not enlarged without a corresponding layout adjustment. Treat the size as a P3 readability concern and verify at zoom/with low-vision users before closure.
- No complete contrast audit of every foreground, background, opacity, chart mark, focus ring, or state was performed.

### Status and empty-state semantics

- Overview/resource empty collections use the exact approved messages in `role="status"` elements. Missing or invalid collections use `role="alert"` and do not display the empty messages.
- Loading and Error buttons in the generic state-preview component update its live region; regression tests verified both states remain functional.
- Dashboard collection rendering is synchronous. The preview is not an API loading/error flow.
- The current browser DOM/accessibility tree exposed the empty preview as `role="status"` and error preview as `role="alert"` inside the preview's polite live region. These are semantic/DOM observations only; announcement priority, timing, and possible duplicate announcements were not tested with assistive technology.
- The DOM roles and accessible tree were inspected, but live-region timing and announcements were **NOT TESTED** with a screen reader or assistive technology.

### Headings, landmarks, and responsive presentation

- The dashboard and placeholder views have labeled sections and headings in source; the browser exposed the Mission Dashboard as a named region. The graph is contained in the named chart panel.
- At 1440/1024px the graph fits its host. At 768/500/375px the 560px graph canvas uses an internal horizontal scroller; the page itself has no horizontal overflow. Keyboard focus reveals each edge label within the scroller.
- The fixed graph width means pointer/touch users must pan horizontally to view the whole graph on narrow displays. This behavior was verified but remains a usability limitation.

## Not tested / unavailable

- Screen-reader output/announcement timing, including SVG relationships, tooltip status updates, and D-03 empty states.
- Automated axe scan. `window.axe` was absent in the shared browser, and no local axe script asset was found. The browser accessibility-tree snapshot and targeted DOM/keyboard checks were used as partial equivalents, not as an axe audit.
- Full keyboard traversal of all screens and controls.
- 200% zoom, forced-colors/high-contrast mode, and a complete manual WCAG review.

No supported screen-reader runtime was detected in this environment (`orca`, `espeak`, `espeak-ng`, `speech-dispatcher`, and `spd-say` were not available), so screen-reader testing was not performed. A browser accessibility snapshot is not a substitute for assistive-technology testing. **No WCAG conformance or accessibility-compliance claim is made.**

## Mission Builder local error handling — FIXED (frontend only)

- **Reproduction:** A temporary static-only server served the prototype and returned `404 text/html` for `GET /api/v1/missions/destinations`. In headless Google Chrome 156.0.8078.79, the updated page displayed `Could not load synthetic destination profiles: HTTP 404. Check that the local mission service is running and try again.`
- **Verified root cause:** `responseJson` converted a non-JSON body to `null`; for a non-OK response without a structured error it created an empty `Error`. `loadDestinations` passed that empty message to `showError`.
- **Fix:** `mission-demo.js` preserves non-empty JSON message/details, uses the HTTP status when an unsuccessful response has no usable detail, and provides a non-empty fallback for empty/network errors. Errors use `role="alert"`/`aria-live="assertive"`; loading and ready states use `role="status"`/`aria-live="polite"`. Mission controls remain disabled after load failure.
- **Regression coverage:** The dedicated browser test covers structured JSON, non-JSON 404, empty JSON, empty error object, blank detail strings, empty network rejection, and successful destination loading. All seven cases passed.
- **Boundary:** This frontend-only fix was explicitly authorized by the Project Owner. No endpoint, backend, contract, production API, or ARC-10 behavior was added or changed. The 404 is not evidence about a production API.

## Outstanding accessibility-related work

1. Perform and record a screen-reader review using a named browser and assistive technology, including edge relationships, focus tooltips, and D-03 status/error messages.
2. Revisit 11px graph labels together with graph layout/canvas space; do not increase text size without rechecking dense-graph overlap.
3. Keep the local Mission Builder fallback distinct from API work: the frontend now explains non-JSON failures, but no API endpoint or production integration is implemented or authorized.

**Audit result:** The tested D-01/D-02/D-03 browser semantics and keyboard behavior are present, and the separately authorized local Mission Builder error presentation is fixed and browser-verified. Assistive-technology behavior remains **NOT TESTED**, the 11px text readability limitation remains, and handover acceptance is pending. No formal ARC-09 closure is claimed.
