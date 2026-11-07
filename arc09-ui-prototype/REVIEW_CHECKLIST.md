# ARC-09 Prototype Review Checklist

**Prototype:** `C:\Nasa AGI\arc09-ui-prototype`  
**Owner:** Hridi  
**Reviewer:** Rafi  
**Review scope:** Isolated prototype only. This checklist does not approve production requirements, stack, or integration.

For each item, select exactly one status: **Accept / Request Changes / Needs Verification**. Add evidence or a short note. The initial status is `Needs Verification`; no reviewer decision is pre-filled.

| # | Rafi review responsibility | Status (Accept / Request Changes / Needs Verification) | Evidence / notes |
|---|---|---|---|
| 1 | Confirm prototype scope and synthetic-data notice are clear; placeholder destinations do not imply working mission features. | Needs Verification | |
| 2 | Review visual hierarchy, dashboard layout, spacing, card consistency, and distinction between global header and page content. | Needs Verification | |
| 3 | Review sidebar destinations, active state, menu trigger, backdrop, and navigation behavior from source and, when available, in-browser. | Needs Verification | |
| 4 | Check mobile keyboard order: open trigger, brand link, then navigation links; Tab and Shift+Tab cycle through intended drawer controls. | Needs Verification | |
| 5 | Check Escape, backdrop, and destination selection close the drawer; focus returns to trigger on close and moves appropriately after navigation. | Needs Verification | |
| 6 | Confirm closed drawer controls are excluded from keyboard navigation and ARIA state matches open/closed state. Verify in a browser when available. | Needs Verification | |
| 7 | Review typography against the supplied baseline: labels about 14px, helper/secondary text generally 13-14px, and no unnecessarily tiny mobile text. | Needs Verification | |
| 8 | Review semantic headings, labels, visible focus, status text that does not rely on color alone, reduced-motion rule, and chart alternatives. | Needs Verification | |
| 9 | Review line and grouped-bar chart titles, labels, legend, tooltips, table alternatives, and validation/error messaging. Confirm all data remains identified as synthetic. | Needs Verification | |
| 10 | Check desktop, tablet, and narrow mobile layout, including navigation, chart legibility, table overflow, and page-level horizontal overflow. Browser rendering is required. | Needs Verification | |
| 11 | Review component reuse and file organization for this prototype; identify any concerns without assuming this architecture is approved for production. | Needs Verification | |
| 12 | Identify production blockers: official repository, approved stack, confirmed initial scope/workflows, API/scientific contracts, and integration expectations. | Needs Verification | |

## Rafi's review responsibilities

- Record a status and supporting note for each item; distinguish source observations from browser observations.
- Request changes for reproducible issues and identify the affected view or interaction.
- Use **Needs Verification** where browser, runtime, or assistive-technology evidence is required but unavailable.
- Treat this as a prototype review. Do not infer team approval, production readiness, or confirmed product scope from the prototype.

## Review outcome

- Overall outcome: `Needs Verification`
- Reviewer notes: ______________________________________________
- Follow-up owner and action: ____________________________________
- Review date: __________________

No review outcome or approval has been recorded in this document.