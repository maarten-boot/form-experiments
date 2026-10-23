# Plan

_Last updated: 2026-10-21_

## Steps
| # | Step | Covers Spec IDs | Status |
|---|------|-----------------|--------|
| 0 | Set up project docs (Conversation, Spec, Plan, TestCases) | — | done |
| 1 | Capture scenario into Spec.md | FR-1 … FR-9 | done |
| 2 | Resolve open questions Q1–Q8 with user | FR-10 … FR-13, NFR-* | done (defaults) |
| 3 | Static page skeleton: `index.html` + `static/style.css`, layout + sample data | FR-1 … FR-4, NFR-1, NFR-2 | done |
| 4 | `static/relations.js` (pure many-to-many state) + `static/app.js` (lists, moves, multi-select, dbl-click, button state) | FR-5, FR-6, FR-10 … FR-13 | done |
| 5 | SVG graph: square/circle, elbow connectors, labels, live update | FR-7 … FR-9 | done |
| 5b | Reverse "By child" view with tabs, shared data, per-view focus | FR-14 … FR-18 | done |
| 6 | Automated tests (pytest + Playwright, `tests/test_editor.py`) | all FR | done — 29 tests × 2 browsers (Chromium, Firefox) = 58/58 pass |
| 7 | Django-readiness (prototype part): JSON via `<script id="relation-data">`, hidden `links` inputs | NFR-2, FR-19 | done (prototype) |
| 8 | Crosscheck #1 Spec ↔ Plan ↔ Code | — | done — see log |
| 8b | Fix crosscheck #1 findings X3–X5 (X1/X2 via 8c) | FR-24, FR-25, NFR-2, NFR-3 | done — TC-21 … TC-25, TC-30 |
| 8c | Graph auto-fit + zoom (content-sized viewBox, Fit / 1:1 / ± buttons, Ctrl+wheel) — also fixes X1, mostly fixes X2 | FR-22, FR-23 | done — TC-26 … TC-29, 24/24 pass |
| 8d | Crosscheck #2 Spec ↔ Plan ↔ Code | — | done — see log |
| 8e | Fix crosscheck #2 findings Y1–Y4 | FR-8, FR-19, FR-25, FR-26 | done — TC-31 … TC-34; 33 tests × 2 browsers = 66/66 pass |
| 9 | Resolve Q9–Q11 | — | done — defaults accepted |
| 9b | Selection highlight: Selected list ↔ graph (highlight, click to select, scroll into view) | FR-27, FR-28 | done — TC-35 … TC-37; 36 tests × 2 browsers = 72/72 pass |
| 9c | Double-click a graph item → jump to the other view | FR-29 | done — TC-38; 37 tests × 2 browsers = 74/74 pass |
| 10 | Django integration: template/widget, view that builds `relation_data`, parse `links` on POST | NFR-2, FR-19 | pending |

## File layout
```
index.html            # prototype page (sample data inline)
static/style.css
static/relations.js   # RelationStore: pure state, no DOM
static/app.js         # DOM wiring, tabs, SVG graph, hidden inputs
tests/TestCases.md    # test case catalogue
tests/test_editor.py  # Playwright browser tests (TC-01 … TC-38), each run in Chromium + Firefox
.venv/                # local Python env (pytest, playwright)
```

## How to run
- Open `index.html` directly in a browser (no server needed).
- Tests: `.venv/bin/python -m pytest tests -q`
- Recreate env if needed (system has no ensurepip):
  `python3 -m venv --without-pip .venv && python3 -m pip --python .venv/bin/python install pytest playwright && .venv/bin/python -m playwright install chromium firefox`

## Crosscheck log
| Date | Trigger | Findings | Resolved |
|------|---------|----------|----------|
| 2026-10-21 | #1 — after reverse view + hidden inputs (Plan 3–7) | 6 doc fixes (D1–D6), 5 code/test issues (X1–X5), see below | D1–D6 fixed (D1 only really applied in crosscheck #2); X1 fixed by 8c; X2 mostly fixed by 8c, remainder → Y1; X3–X5 fixed by 8b |
| 2026-10-21 | #2 — after zoom (8c) and X3–X5 fixes (8b) | 4 doc fixes (E1–E4), 4 code issues (Y1–Y4), see below | E1–E4 fixed; Y1–Y4 fixed by 8e |

### Crosscheck #1 — 2026-10-21

All 19 FRs are implemented, and all have at least one automated test. Every test passes (20/20).

**Docs out of sync (fixed during the crosscheck):**
| ID | Where | Finding | Fix |
|----|-------|---------|-----|
| D1 | Spec §1 | Layout diagram showed only the By-parent view | Added By-child diagram + tabs |
| D2 | Spec FR-13 | Said "no parent chosen"; code applies to either view's focus | Reworded to "no focus item" |
| D3 | Spec NFR-2 | Source pointed to Q2 (wrong) | Source → Entry 2, Q8 |
| D4 | Spec | Implemented but unspecified: initial state (By-parent tab, nothing focused), hint text in empty graph, list selection kept across re-render | Added FR-20, FR-21 |
| D5 | TestCases TC-14 | Described "dbl-click spam" but the test calls `store.add` directly with duplicate ids | Description aligned with test |
| D6 | Spec §5 | Not stated that parent and child ids live in separate namespaces (needed for Django: both models will have pk=1) | Added note; code already handles it |

**Code / test issues (need a decision before fixing):**
| ID | Severity | Spec | Finding (verified) | Proposed fix |
|----|----------|------|--------------------|--------------|
| X1 | bug | FR-8 | Long labels are clipped: the focus label is centred on the square and is cut off at the left edge; long related labels are cut off at the right edge (screenshot verified). | Put the focus label below/left-aligned to the square and size the viewBox to the measured label widths, or shorten with "…" + tooltip (`<title>`). |
| X2 | bug | FR-8 | The graph scales with the pane width (viewBox + width 100%), so its text is larger than the list text (≈17px vs 14px). With many children the square is vertically centred and scrolls out of view. | Draw at 1:1 pixel scale (no scaling, pane scrolls); anchor the square at the top row or make it sticky. |
| X3 | robustness | NFR-2 | One link in the JSON with an unknown id makes `RelationStore` throw at load, so the whole editor stays empty. Real Django data could hit this (e.g. a deleted record). | Skip invalid links with `console.warn`; add a test. |
| X4 | test gap | FR-8, FR-9, FR-11 | No test for related-item labels, for the graph updating on a focus change, or for a multi-select move to the right (→). | Add TC-21 … TC-23. |
| X5 | spec gap | NFR-3 | "Firefox" and "keyboard-usable" are untested. Keyboard only: a user can tab and select, but Enter in a list does nothing; only the buttons move items. | Add Playwright Firefox run; add Enter = move (or accept that the buttons are enough) + test. |

### Crosscheck #2 — 2026-10-21

All 25 FRs and 3 NFRs are implemented, and each has at least one automated test. The suite runs in Chromium and Firefox: 58/58 pass.
Extra probes: page starting with the editor hidden (`display:none`) then shown → graph sizes correctly in both browsers; 40 children on one parent → see Y1.

**Docs out of sync (fixed during the crosscheck):**
| ID | Where | Finding | Fix |
|----|-------|---------|-----|
| E1 | Spec §1 | Crosscheck #1 said D1 added the By-child diagram, but it was missing | Added the By-child diagram and the zoom bar |
| E2 | Spec | Enter-to-move and skipping invalid links were implemented but unspecified | Added FR-24, FR-25; NFR-3 now refers to the Firefox run |
| E3 | Plan | Step 6 count, step 8/8b status, test range in the file layout, and the install command (no Firefox) were outdated | Updated |
| E4 | TestCases | TC-21 … TC-25 were only "planned"; TC-30 missing | Rows added, run result updated |

**Code issues (need a decision before fixing):**
| ID | Severity | Spec | Finding (verified) | Proposed fix |
|----|----------|------|--------------------|--------------|
| Y1 | usability | FR-8, FR-22 | Rest of X2: with 40 children Fit stops at 50 %, and the focus square, which is centred vertically, sits at the bottom edge of the pane (about 40 px from the bottom). | Put the focus node at the first row, level with the first related item (tree style), so it is always at the top. |
| Y2 | robustness | NFR-2 | Duplicate ids in `parents` or `children` are not detected: the item appears twice in the list, and both entries act as one. | Skip duplicates with `console.warn`, as FR-25 does for links. |
| Y3 | robustness | FR-19 | The hidden input format `parentId:childId` breaks if an id contains `:`. This is harmless for Django integer pks, but not for slugs or UUID-like keys. | Leave as is, and note in the spec that ids must not contain `:`; or split on the first `:` only and forbid `:` in parent ids. |
| Y4 | a11y | NFR-3 | The "Relationship" `<label>` is not tied to any control, and the SVG has no accessible name or text alternative. | Use a heading/`<span>` and add `role="img"` + `aria-label` (e.g. "Team Bravo: 3 children — Bob, Carol, Dave"). |
