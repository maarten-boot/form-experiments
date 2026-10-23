/*
 * DOM wiring + SVG graph for the relation editor.
 * Expects RelationStore (relations.js) and a <script id="relation-data"> JSON block
 * shaped like {parents: [...], children: [...], links: [[parentId, childId], ...]}.
 * In Django that block can be produced with {{ data|json_script:"relation-data" }}.
 */
(function () {
  "use strict";

  const SVG_NS = "http://www.w3.org/2000/svg";
  const G = {
    padTop: 30,
    rowH: 30,
    focusX: 40,
    relatedX: 240,
    size: 14, // square side / circle diameter
    margin: 12, // space around the measured content
  };

  // Zoom: "fit" scales the content to the pane, but never above fitMax (so the
  // graph text stays no larger than at 1:1) and never below fitMin (stays readable;
  // the pane scrolls instead). Manual zoom is clamped to min..max.
  const ZOOM = { min: 0.25, max: 4, step: 1.25, fitMin: 0.5, fitMax: 1 };

  const data = JSON.parse(document.getElementById("relation-data").textContent);
  const store = new RelationStore(data.parents, data.children, data.links);

  const el = {
    tabs: document.querySelectorAll("[data-view-tab]"),
    focusLabel: document.getElementById("focus-label"),
    selectedLabel: document.getElementById("selected-label"),
    candidatesLabel: document.getElementById("candidates-label"),
    focus: document.getElementById("focus-list"),
    selected: document.getElementById("selected-list"),
    candidates: document.getElementById("candidates-list"),
    add: document.getElementById("btn-add"),
    remove: document.getElementById("btn-remove"),
    graph: document.getElementById("graph"),
    pane: document.querySelector(".graph-pane"),
    zoomIn: document.getElementById("zoom-in"),
    zoomOut: document.getElementById("zoom-out"),
    zoomFit: document.getElementById("zoom-fit"),
    zoomReset: document.getElementById("zoom-reset"),
    zoomLevel: document.getElementById("zoom-level"),
    hidden: document.getElementById("hidden-links"),
  };

  const state = {
    view: "parent",
    // Remember the focus per view so switching tabs and back restores it.
    focus: { parent: null, child: null },
    zoom: null, // null = fit to pane; otherwise a fixed scale chosen by the user
    scale: 1, // scale currently applied
  };

  const TEXT = {
    parent: { focus: "Parent", selected: "Children", candidates: "Candidate children" },
    child: { focus: "Child", selected: "Parents", candidates: "Candidate parents" },
  };

  // ---------- helpers ----------

  function fillSelect(select, items, keepSelected) {
    const prev = keepSelected ? new Set(selectedIds(select)) : new Set();
    select.replaceChildren(
      ...items.map((item) => {
        const opt = new Option(item.label, item.id);
        opt.selected = prev.has(item.id);
        return opt;
      })
    );
  }

  function selectedIds(select) {
    return Array.from(select.selectedOptions, (o) => o.value);
  }

  function svg(tag, attrs, text) {
    const node = document.createElementNS(SVG_NS, tag);
    for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
    if (text !== undefined) node.textContent = text;
    return node;
  }

  // Square for a parent, circle for a child — regardless of which side it is on.
  function shape(kind, cx, cy, role, id) {
    const s = G.size;
    const common = { class: "node " + kind, "data-role": role, "data-id": id };
    return kind === "parent"
      ? svg("rect", { ...common, x: cx - s / 2, y: cy - s / 2, width: s, height: s })
      : svg("circle", { ...common, cx, cy, r: s / 2 });
  }

  // ---------- rendering ----------

  function renderLists() {
    const view = state.view;
    const focusId = state.focus[view];

    el.focusLabel.textContent = TEXT[view].focus;
    el.selectedLabel.textContent = TEXT[view].selected;
    el.candidatesLabel.textContent = TEXT[view].candidates;
    el.tabs.forEach((t) => t.setAttribute("aria-selected", t.dataset.viewTab === view));

    fillSelect(el.focus, store.focusItems(view), false);
    el.focus.value = focusId ?? "";

    if (focusId == null) {
      el.selected.replaceChildren();
      el.candidates.replaceChildren();
    } else {
      fillSelect(el.selected, store.related(view, focusId), true);
      fillSelect(el.candidates, store.candidates(view, focusId), true);
    }
  }

  function renderGraph() {
    const view = state.view;
    const focusId = state.focus[view];
    const focusKind = view;
    const relatedKind = view === "parent" ? "child" : "parent";

    el.graph.replaceChildren();
    if (focusId == null) {
      const hint = `Select a ${focusKind} on the left`;
      el.graph.setAttribute("aria-label", hint);
      el.graph.append(svg("text", { x: 20, y: 35, class: "hint" }, hint));
      applyZoom();
      return;
    }

    const related = store.related(view, focusId);
    el.graph.setAttribute("aria-label", describeGraph(store.label(focusKind, focusId), relatedKind, related));

    const ys = related.map((_, i) => G.padTop + i * G.rowH);
    // Focus node level with the first related item (tree style), so it stays at the
    // top of the pane however many related items there are.
    const fy = G.padTop;
    const fx = G.focusX;
    const midX = (G.focusX + G.relatedX) / 2;
    const half = G.size / 2;

    // Elbow connectors: out of the focus node, down/up the trunk, across to each related node.
    related.forEach((item, i) => {
      el.graph.append(
        svg("path", {
          class: "connector",
          "data-id": item.id,
          d: `M ${fx + half} ${fy} H ${midX} V ${ys[i]} H ${G.relatedX - half}`,
        })
      );
    });

    el.graph.append(shape(focusKind, fx, fy, "focus", focusId));
    el.graph.append(
      svg("text", { x: fx, y: fy - half - 6, class: "label focus-label", "text-anchor": "middle" },
        store.label(focusKind, focusId))
    );

    // Each related node + its label is one clickable group (see the graph click handler).
    related.forEach((item, i) => {
      const group = svg("g", { class: "related-item", "data-id": item.id });
      const other = relatedKind === "parent" ? "By parent" : "By child";
      group.append(
        svg("title", {}, `${item.label}\nClick to select · Double-click to open in "${other}"`),
        shape(relatedKind, G.relatedX, ys[i], "related", item.id),
        svg("text", { x: G.relatedX + half + 8, y: ys[i] + 4, class: "label" }, item.label)
      );
      el.graph.append(group);
    });

    applyZoom();
    syncHighlight(false);
  }

  // Highlight the graph items that are selected in the Selected list. With `reveal`,
  // scroll the pane so the first highlighted item is visible.
  function syncHighlight(reveal) {
    const ids = new Set(selectedIds(el.selected));
    const focusNode = el.graph.querySelector("[data-role=focus]");
    let first = null;
    el.graph.querySelectorAll(".related-item, .connector").forEach((n) => {
      const on = ids.has(n.dataset.id);
      n.classList.toggle("highlight", on);
      if (!on) return;
      if (n.matches(".related-item")) first = first || n;
      // Connectors share the trunk: draw highlighted ones last (but under the nodes).
      else el.graph.insertBefore(n, focusNode);
    });
    // Scroll to the shape, not the <g>: Firefox does not scroll to a <g>.
    if (reveal && first) first.querySelector(".node").scrollIntoView({ block: "nearest", inline: "nearest" });
  }

  // Text alternative for the graph, e.g. "Team Bravo: 3 children — Bob, Carol, Dave".
  function describeGraph(focusLabel, relatedKind, related) {
    const noun = { child: ["child", "children"], parent: ["parent", "parents"] }[relatedKind];
    if (related.length === 0) return `${focusLabel}: no ${noun[1]}`;
    const count = `${related.length} ${noun[related.length === 1 ? 0 : 1]}`;
    return `${focusLabel}: ${count} — ${related.map((i) => i.label).join(", ")}`;
  }

  // ---------- zoom ----------

  function clamp(v, lo, hi) {
    return Math.min(hi, Math.max(lo, v));
  }

  // Size the viewBox to the drawn content (so long labels are never clipped),
  // then size the <svg> element to content × scale. The pane scrolls if needed.
  function applyZoom() {
    const box = el.graph.getBBox();
    const m = G.margin;
    const w = box.width + 2 * m;
    const h = box.height + 2 * m;
    el.graph.setAttribute("viewBox", `${box.x - m} ${box.y - m} ${w} ${h}`);

    if (state.zoom == null) {
      const fit = Math.min(el.pane.clientWidth / w, el.pane.clientHeight / h);
      state.scale = clamp(fit, ZOOM.fitMin, ZOOM.fitMax);
    } else {
      state.scale = state.zoom;
    }
    el.graph.setAttribute("width", w * state.scale);
    el.graph.setAttribute("height", h * state.scale);

    el.zoomLevel.textContent = Math.round(state.scale * 100) + "%";
    el.zoomFit.setAttribute("aria-pressed", state.zoom == null);
    el.zoomIn.disabled = state.scale >= ZOOM.max;
    el.zoomOut.disabled = state.scale <= ZOOM.min;
  }

  function setZoom(zoom) {
    state.zoom = zoom == null ? null : clamp(zoom, ZOOM.min, ZOOM.max);
    applyZoom();
  }

  // Hidden inputs so a surrounding <form> (e.g. Django) submits the full relation.
  function renderHidden() {
    el.hidden.replaceChildren(
      ...store.toJSON().map(([p, c]) => {
        const input = document.createElement("input");
        input.type = "hidden";
        input.name = "links";
        input.value = `${p}:${c}`;
        return input;
      })
    );
  }

  function renderButtons() {
    const hasFocus = state.focus[state.view] != null;
    el.add.disabled = !hasFocus || selectedIds(el.candidates).length === 0;
    el.remove.disabled = !hasFocus || selectedIds(el.selected).length === 0;
  }

  function render() {
    renderLists();
    renderGraph();
    renderHidden();
    renderButtons();
  }

  // ---------- actions ----------

  function moveToSelected(ids) {
    const focusId = state.focus[state.view];
    if (focusId == null || ids.length === 0) return;
    store.add(state.view, focusId, ids);
    render();
  }

  function moveToCandidates(ids) {
    const focusId = state.focus[state.view];
    if (focusId == null || ids.length === 0) return;
    store.remove(state.view, focusId, ids);
    render();
  }

  el.focus.addEventListener("change", () => {
    state.focus[state.view] = el.focus.value || null;
    el.selected.selectedIndex = -1;
    el.candidates.selectedIndex = -1;
    render();
    el.pane.scrollTo(0, 0);
  });

  // Switch tabs. Optionally set the new view's focus, and select (= highlight) one
  // item in its Selected list.
  function switchView(view, focusId, selectId) {
    state.view = view;
    if (focusId !== undefined) state.focus[view] = focusId;
    el.selected.replaceChildren();
    el.candidates.replaceChildren();
    render();
    el.pane.scrollTo(0, 0);
    const opt = Array.from(el.selected.options).find((o) => o.value === selectId);
    if (opt) {
      opt.selected = true;
      opt.scrollIntoView({ block: "nearest" });
      renderButtons();
      syncHighlight(true);
    }
  }

  el.tabs.forEach((tab) => tab.addEventListener("click", () => switchView(tab.dataset.viewTab)));

  el.add.addEventListener("click", () => moveToSelected(selectedIds(el.candidates)));
  el.remove.addEventListener("click", () => moveToCandidates(selectedIds(el.selected)));

  el.candidates.addEventListener("dblclick", (e) => {
    if (e.target instanceof HTMLOptionElement) moveToSelected([e.target.value]);
  });
  el.selected.addEventListener("dblclick", (e) => {
    if (e.target instanceof HTMLOptionElement) moveToCandidates([e.target.value]);
  });

  el.candidates.addEventListener("change", renderButtons);
  el.selected.addEventListener("change", () => {
    renderButtons();
    syncHighlight(true);
  });

  // Clicking a related item in the graph selects it in the Selected list (Ctrl/Cmd-click
  // toggles it, like in the list) and scrolls the list to it; clicking empty space in the
  // pane (the SVG may be smaller than the pane) clears the selection.
  el.pane.addEventListener("click", (e) => {
    const item = e.target.closest(".related-item");
    const options = Array.from(el.selected.options);
    const opt = item && options.find((o) => o.value === item.dataset.id);
    if (opt && (e.ctrlKey || e.metaKey)) {
      opt.selected = !opt.selected;
    } else {
      options.forEach((o) => (o.selected = o === opt));
    }
    if (opt) opt.scrollIntoView({ block: "nearest" });
    renderButtons();
    syncHighlight(false);
  });

  // Double-clicking a related item jumps to the other view with that item as focus;
  // the item we came from is selected (highlighted) there.
  el.pane.addEventListener("dblclick", (e) => {
    const item = e.target.closest(".related-item");
    if (!item) return;
    const from = state.focus[state.view];
    switchView(state.view === "parent" ? "child" : "parent", item.dataset.id, from);
  });

  // Keyboard: Enter in a list moves its selected items, same as the arrow buttons.
  el.candidates.addEventListener("keydown", (e) => {
    if (e.key !== "Enter") return;
    e.preventDefault();
    moveToSelected(selectedIds(el.candidates));
  });
  el.selected.addEventListener("keydown", (e) => {
    if (e.key !== "Enter") return;
    e.preventDefault();
    moveToCandidates(selectedIds(el.selected));
  });

  el.zoomIn.addEventListener("click", () => setZoom(state.scale * ZOOM.step));
  el.zoomOut.addEventListener("click", () => setZoom(state.scale / ZOOM.step));
  el.zoomFit.addEventListener("click", () => setZoom(null));
  el.zoomReset.addEventListener("click", () => setZoom(1));

  // Ctrl + wheel (also trackpad pinch) zooms the graph; a plain wheel still scrolls the pane.
  el.pane.addEventListener(
    "wheel",
    (e) => {
      if (!e.ctrlKey) return;
      e.preventDefault();
      setZoom(state.scale * (e.deltaY < 0 ? ZOOM.step : 1 / ZOOM.step));
    },
    { passive: false }
  );

  // Re-fit when the pane changes size (window resize) while in fit mode.
  new ResizeObserver(() => {
    if (state.zoom == null) applyZoom();
  }).observe(el.pane);

  // Exposed for tests / debugging.
  window.relationApp = { store, state, render };

  render();
})();
