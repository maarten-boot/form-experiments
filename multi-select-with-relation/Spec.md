# Specification

_Status: draft v0.7 — double-click jump between views added._
_Last updated: 2026-10-21_

## 1. Overview
A web page (prototype first, later embedded in Django, e.g. as a template/widget) for assigning
**children to a parent**. The user picks a parent on the left, moves candidate items into a
"selected children" list on the right, and a graphic pane in the middle visualises the
parent → children relationship.

### Layout (left → right)
```
+-----------+   +-------------------------+   +-----------+  +---+  +------------+
|  Parent   |   |     Graphic pane        |   | Selected  |  | ← |  | Candidates |
|  (select) |   |   [■]────●  child A     |   | children  |  | → |  | (select)   |
|           |   |      ├───●  child B     |   | (select)  |  +---+  |            |
|           |   |      └───●  child C     |   |           |         |            |
+-----------+   +-------------------------+   +-----------+         +------------+
```

Two tabs above the editor: **By parent** (above) and **By child** (same layout, roles swapped):
```
+-----------+   +-------------------------+   +-----------+  +---+  +------------+
|  Child    |   |     Graphic pane        |   | Parents   |  | ← |  | Candidate  |
|  (select) |   |   (●)────■  parent X    |   | (select)  |  | → |  | parents    |
|           |   |      └───■  parent Y    |   |           |  +---+  | (select)   |
+-----------+   +-------------------------+   +-----------+         +------------+
```
The graphic pane has a zoom bar above it: − / Fit / 1:1 / + and the current level.

## 2. Scope
### In scope
- Single standalone HTML page (prototype) with the 4 widgets above.
- Client-side behaviour: moving items, updating the graph live.
- Structure that is easy to port to a Django template / form widget.
### Out of scope (for now)
- Backend persistence / Django models (later phase).
- Authentication, multi-user editing.

## 3. Functional requirements
| ID | Requirement | Source |
|----|-------------|--------|
| FR-1 | The page shows, left → right: Parent list, Graphic pane, Selected-children list, arrow buttons, Candidates list. | Entry 2 |
| FR-2 | The Parent list is a select list; the selected item is the current parent. | Entry 2 |
| FR-3 | The Candidates list (far right) contains items that can become children of the current parent. | Entry 2 |
| FR-4 | The Selected-children list (second from right) contains the current parent's children. | Entry 2 |
| FR-5 | A **left-pointing arrow (←)** button moves the selected item(s) from Candidates to Selected-children. | Entry 2 |
| FR-6 | A **right-pointing arrow (→)** button moves the selected item(s) from Selected-children back to Candidates. | Entry 2 |
| FR-7 | The Graphic pane draws the current parent as a **small square** and each child as a **small circle**, with lines connecting parent to each child. | Entry 2 |
| FR-8 | Graph layout: parent on the left, children stacked vertically on the right, joined by elbow (tree-style) connectors; items labelled. The focus node is level with the first related item, so it stays at the top of the pane however long the list is. | Entry 2, Q3, Q6, Y1 |
| FR-9 | The graph updates immediately when the parent changes or children are moved. | implied by Entry 2 |
| FR-10 | Children assignments are remembered per parent: switching parent shows that parent's children; switching back restores them. | Q1 |
| FR-11 | Multi-select is allowed in both right lists; arrow moves all selected items. | Q5 |
| FR-12 | Double-clicking an item moves it to the other list. | Q5 |
| FR-13 | Arrow buttons are disabled when there is nothing selected to move or no focus item is chosen (either view). | — |
| FR-14 | Two views, switchable via tabs: **By parent** (focus list = parents, right lists = children) and **By child** (focus list = children, right lists = Selected parents / Candidate parents). | Entry 3 |
| FR-15 | In the By-child view the graph shows the current child (circle) on the left and its parents (squares) stacked vertically on the right. Square always = parent, circle always = child. | Entry 3 |
| FR-16 | Both views edit the same many-to-many relation; a change in one view is immediately visible in the other. | Entry 3, Q4 |
| FR-17 | Each view remembers its own focus item when switching tabs. | — |
| FR-18 | Column headings adapt to the view (Parent/Children/Candidate children vs Child/Parents/Candidate parents). | Entry 3 |
| FR-19 | The relation is mirrored into hidden `<input name="links" value="parentId:childId">` fields inside the form, in assignment order. Ids must not contain `:` (a `console.warn` is logged if one does). | Q8, Y3 |
| FR-20 | Initial state: By-parent tab active, nothing focused, both right lists empty, graph shows a hint ("Select a parent on the left"). | crosscheck #1 |
| FR-21 | Re-rendering (after a move) keeps the user's current selection in the right lists where the items still exist. | crosscheck #1 |
| FR-22 | The graph adapts to its content: its drawing area is sized to the measured content, so labels are never clipped. Default mode **Fit** scales it to fit the pane (max 100 %, min 50 %; below that the pane scrolls) and re-fits on changes and pane resize. | Entry 5 |
| FR-23 | The graph is zoomable: buttons − / Fit / 1:1 / + above the pane, and Ctrl + mouse wheel (or trackpad pinch) over the pane; zoom 25 %–400 % in steps of ×1.25; the current level is shown. A manual zoom level is kept across re-renders until Fit is chosen. | Entry 5 |
| FR-24 | Keyboard: pressing Enter in the Candidates or Selected list moves that list's selected items (same as ← / →). | X5 |
| FR-25 | Invalid links in the input data (unknown parent/child id, malformed pair) are skipped with a `console.warn`; the editor still loads, and skipped links are not submitted. Duplicate parent/child ids are skipped the same way (first one wins). | X3, Y2 |
| FR-26 | The graph has a text alternative (`role="img"` + `aria-label`, e.g. "Team Bravo: 3 children — Bob, Carol, Dave"), kept up to date; every `<label>` on the page is tied to a control. | Y4 |
| FR-27 | Items selected in the Selected list are highlighted in the graph (node outline, bold label, darker connector). When the selection changes in the list, the pane scrolls to the first highlighted item if it is out of view. The highlight survives re-renders. | Entry 8 |
| FR-28 | Clicking a related item (node or label) in the graph selects it in the Selected list and scrolls the list to it; Ctrl/Cmd-click toggles it in the selection; clicking empty space in the pane clears the selection. The arrow-button state follows (FR-13). | Entry 8 |
| FR-29 | Double-clicking a related item (node or label) in the graph switches to the other view with that item as focus; the previous focus item is selected (and so highlighted) in the new view's Selected list. A tooltip on each related item explains click and double-click. | Entry 9 |

## 4. Non-functional requirements
| ID | Requirement | Source |
|----|-------------|--------|
| NFR-1 | Plain HTML + CSS + vanilla JavaScript, inline SVG for the graph; no build step, no framework — so it drops into a Django template easily. | Entry 2 ("later Django") |
| NFR-2 | Data is supplied as JSON (prototype: inline sample data; Django: `json_script`). | Entry 2, Q8 |
| NFR-3 | Works in current Chrome/Firefox (whole test suite runs in Chromium and Firefox); keyboard-usable (buttons focusable, lists native `<select multiple>`, Enter moves — FR-24). | X5 |

## 5. Data / UI model
Implemented as a many-to-many link list (order = assignment order):
```js
parents:  [{id, label}, ...]
children: [{id, label}, ...]
links:    [[parentId, childId], ...]
```
Candidates for focus F = all items on the other side − items already linked to F (data order).
Related items of F are listed in assignment order.
Parent ids and child ids are separate namespaces (parent `1` and child `1` may coexist — matches Django pks of two models).

## 6. Decisions
| ID | Question | Decision |
|----|----------|----------|
| Q1 | Mapping kept per parent? | Yes (FR-10) |
| Q2 | Same pool or two kinds? | Two separate lists (parents, children) |
| Q3 | Connector style | Elbow / tree-style (FR-8) |
| Q4 | Child in multiple parents? | Yes — many-to-many (FR-16) |
| Q5 | Multi-select + double-click | Yes (FR-11, FR-12) |
| Q6 | Labels in graph | Yes (FR-8) |
| Q7 | Graph scope | Current focus only; plus reverse By-child view (FR-14, FR-15) |
| Q8 | Submission | Hidden inputs, order = assignment order (FR-19) |
| Q9 | Two views: tabs or separate pages in Django? | Tabs on one page (one form, one save) |
| Q10 | Reorder children in the Selected list? | No, for now (order = assignment order) |
| Q11 | Filter/search box for large lists? | Not yet; revisit with real data |

## 7. Open questions
None at the moment.
