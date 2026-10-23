# Test Cases

_Last updated: 2026-10-21_

Each test case traces back to a Spec requirement ID. Automated in `tests/test_editor.py` (`test_tcNN_*`). Run: `.venv/bin/python -m pytest tests -q`.

_Last run: 2026-10-22 — 74/74 pass (37 tests × Chromium + Firefox)._

TC-21 … TC-25 and TC-30 come from crosscheck #1 (X3–X5). TC-25 is not a separate test: the `browser` fixture runs every test in both browsers.

| TC ID | Spec ID | Description | Steps | Expected result | Automated? | Status |
|-------|---------|-------------|-------|-----------------|------------|--------|
| TC-01 | FR-1 | Layout order | Open page | Left→right: Parent, Graph, Selected, arrows, Candidates | yes | pass |
| TC-02 | FR-2 | Choose parent | Click a parent | It becomes current parent; graph shows its square + label | yes | pass |
| TC-03 | FR-3 | Initial candidates | Choose parent with no children | Candidates holds all items; Selected empty | yes | pass |
| TC-04 | FR-5 | Move to selected | Select 1 candidate, click ← | Item leaves Candidates, appears in Selected | yes | pass |
| TC-05 | FR-6 | Move back | Select 1 child, click → | Item leaves Selected, appears in Candidates | yes | pass |
| TC-06 | FR-7 | Shapes | Parent with 3 children | Graph has 1 square, 3 circles, 3 connectors | yes | pass |
| TC-07 | FR-8 | Layout of graph | Parent with 3 children | Square x < all circle x; circles share x, distinct increasing y | yes | pass |
| TC-08 | FR-9 | Live update | Move a child in/out | Circle count follows Selected count immediately | yes | pass |
| TC-09 | FR-10 | Per-parent memory | Give A 2 children, switch to B, back to A | A shows its 2 children again; B independent | yes | pass |
| TC-10 | FR-11 | Multi-move | Ctrl-select 3 candidates, click ← | All 3 moved | yes | pass |
| TC-11 | FR-12 | Double-click | Double-click candidate, then double-click it in Selected | Moves over and back | yes | pass |
| TC-12 | FR-13 | Button state | Nothing selected / no parent | Arrow buttons disabled | yes | pass |
| TC-13 | FR-7 | Empty graph | Parent with 0 children | Only the square, no circles/lines | yes | pass |
| TC-14 | FR-4/FR-5 | No duplicates | Add the same child repeatedly via the store API (`add` with duplicate ids, then again) | Item appears exactly once across both lists | yes | pass |
| TC-15 | FR-14, FR-18 | Reverse view headings | Click "By child" | Headings Child / Parents / Candidate parents; focus list holds children | yes | pass |
| TC-16 | FR-14 | Reverse view lists | By child, pick Bob | Selected = Team Alpha, Team Bravo; Candidates = Charlie, Delta | yes | pass |
| TC-17 | FR-15 | Reverse view shapes | By child, pick Bob | Focus is circle (left), related are squares (right) | yes | pass |
| TC-18 | FR-16, FR-17 | Views share data | Add Heidi to Delta; in By child remove Delta from Heidi; back to By parent | Parent view still focused on Delta, Heidi gone | yes | pass |
| TC-19 | FR-16 (Q4) | Many-to-many | Alice in Alpha; pick Charlie | Alice still a candidate | yes | pass |
| TC-20 | FR-19 | Hidden inputs | Initial; then add Eve / remove Alice on Alpha | `links` inputs mirror relation in assignment order | yes | pass |
| TC-21 | FR-8 | Related labels | Pick Team Bravo | Graph labels: Team Bravo, Bob, Carol, Dave | yes | pass |
| TC-22 | FR-9 | Graph follows focus change | Pick Bravo, then Alpha | Graph shows only Alpha (p1) with Alice, Bob | yes | pass |
| TC-23 | FR-6, FR-11 | Multi-move back (→) | Bravo: select Bob + Dave, click → | Selected = Carol; Bob, Dave in Candidates; 1 circle | yes | pass |
| TC-24 | FR-25 | Invalid links skipped | Load page whose data has unknown parent, unknown child, malformed pair | No page error; 3 warnings; valid links shown and submitted | yes | pass |
| TC-25 | NFR-3 | Firefox | Run the whole suite | Every test passes in Chromium and Firefox | yes | pass |
| TC-26 | FR-22 | Graph fits pane | Pick Team Bravo | SVG ≤ pane size; all elements inside viewBox; Fit active | yes | pass |
| TC-27 | FR-22 | Long labels not clipped (X1) | Give a parent and a child very long labels, pick that parent | All elements inside viewBox; graph fits pane width | yes | pass |
| TC-28 | FR-23 | Zoom buttons | 1:1 → 100 %; + → 125 % and wider; − − → 80 %; move an item; Fit | Levels as stated; manual zoom kept after the move; Fit re-activates | yes | pass |
| TC-29 | FR-23 | Ctrl + wheel | At 1:1, Ctrl + wheel up over the pane | 125 % | yes | pass |
| TC-30 | FR-24 | Keyboard Enter | Charlie: focus Candidates, ↓, Enter; focus Selected, ↓, Enter | Alice moves over and back | yes | pass |
| TC-31 | FR-8 (Y1) | Focus node at top | Team Delta with 40 children, Fit | Square level with the first child, within 60 px of the pane top | yes | pass |
| TC-32 | FR-25 (Y2) | Duplicate ids skipped | Data with a duplicate parent id and a duplicate child id | 2 warnings; duplicates not listed | yes | pass |
| TC-33 | FR-19 (Y3) | `:` in id warns | Parent id `p:4` | 1 warning mentioning `:`; editor still loads | yes | pass |
| TC-34 | FR-26 (Y4) | Graph text alternative | Initial; Bravo; Delta; By child → Alice | aria-label: hint / "Team Bravo: 3 children — Bob, Carol, Dave" / "Team Delta: no children" / "Alice: 1 parent — Team Alpha"; all labels tied to controls | yes | pass |
| TC-35 | FR-27 | List selection highlights graph | Bravo: select Bob + Dave; add Eve; deselect all | Bob, Dave items + connectors highlighted, still after the move; none after deselect | yes | pass |
| TC-36 | FR-28 | Graph click selects in list | Bravo: click Carol; Ctrl-click Dave; Ctrl-click Carol; click Bob; → ; select Carol, click empty pane | [c3] → [c3,c4] → [c4] → [c2]; → moves Bob; empty click clears; → disabled | yes | pass |
| TC-37 | FR-27, FR-28 | Scroll to selected item | Delta with 40 children: click Kid 39 in graph; scroll pane to top, select Kid 38 in list | List scrolls to Kid 39; pane scrolls so Kid 38 is visible | yes | pass |
| TC-38 | FR-29 | Double-click jumps to other view | Bravo: dbl-click Bob; then dbl-click Team Alpha label; then By child tab | By child on Bob, Team Bravo selected + highlighted; then By parent on Alpha, Bob highlighted; By child still on Bob | yes | pass |
