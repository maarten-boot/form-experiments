"""Browser tests for the parent/child editor. Test names carry the TC IDs from TestCases.md."""

from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

INDEX = (Path(__file__).resolve().parent.parent / "index.html").as_uri()


# TC-25 / NFR-3: every test runs in both Chromium and Firefox.
@pytest.fixture(scope="session")
def playwright_instance():
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="session", params=["chromium", "firefox"])
def browser(request, playwright_instance):
    b = getattr(playwright_instance, request.param).launch()
    yield b
    b.close()


@pytest.fixture
def page(browser):
    pg = browser.new_page(viewport={"width": 1400, "height": 800})
    errors = []
    pg.on("pageerror", lambda e: errors.append(e))
    pg.goto(INDEX)
    yield pg
    pg.close()
    assert not errors, errors


# ---------- helpers ----------

def options(page, list_id):
    return page.eval_on_selector_all(f"#{list_id} option", "os => os.map(o => o.textContent)")


def pick_focus(page, label):
    page.select_option("#focus-list", label=label)


def pick(page, list_id, *labels):
    page.select_option(f"#{list_id}", label=list(labels))


def graph(page):
    return page.evaluate(
        """() => {
        const g = document.getElementById('graph');
        const box = n => ({tag: n.tagName, id: n.dataset.id, kind: n.classList[1],
                           x: n.getBBox().x + n.getBBox().width / 2,
                           y: n.getBBox().y + n.getBBox().height / 2});
        return {
          focus: [...g.querySelectorAll('[data-role=focus]')].map(box),
          related: [...g.querySelectorAll('[data-role=related]')].map(box),
          connectors: g.querySelectorAll('.connector').length,
          labels: [...g.querySelectorAll('.label')].map(t => t.textContent),
        };
    }"""
    )


def hidden_links(page):
    return page.eval_on_selector_all("#hidden-links input[name=links]", "is => is.map(i => i.value)")


# ---------- parent view ----------

def test_tc01_layout_order(page):
    ids = ["focus-list", "graph", "selected-list", "btn-add", "candidates-list"]
    xs = [page.locator(f"#{i}").bounding_box()["x"] for i in ids]
    assert xs == sorted(xs)
    # ← above →, both between selected and candidates
    add, rem = page.locator("#btn-add").bounding_box(), page.locator("#btn-remove").bounding_box()
    assert add["y"] < rem["y"]
    assert page.locator("#btn-add").inner_text() == "←"
    assert page.locator("#btn-remove").inner_text() == "→"


def test_tc02_choose_parent(page):
    pick_focus(page, "Team Alpha")
    g = graph(page)
    assert len(g["focus"]) == 1 and g["focus"][0]["tag"] == "rect"
    assert "Team Alpha" in g["labels"]


def test_tc03_initial_candidates(page):
    pick_focus(page, "Team Delta")  # no children in sample data
    assert options(page, "selected-list") == []
    assert len(options(page, "candidates-list")) == 8


def test_tc04_move_to_selected(page):
    pick_focus(page, "Team Delta")
    pick(page, "candidates-list", "Carol")
    page.click("#btn-add")
    assert options(page, "selected-list") == ["Carol"]
    assert "Carol" not in options(page, "candidates-list")


def test_tc05_move_back(page):
    pick_focus(page, "Team Alpha")
    pick(page, "selected-list", "Bob")
    page.click("#btn-remove")
    assert options(page, "selected-list") == ["Alice"]
    assert "Bob" in options(page, "candidates-list")


def test_tc06_shapes(page):
    pick_focus(page, "Team Bravo")  # 3 children
    g = graph(page)
    assert [n["tag"] for n in g["focus"]] == ["rect"]
    assert [n["tag"] for n in g["related"]] == ["circle"] * 3
    assert g["connectors"] == 3


def test_tc07_graph_layout(page):
    pick_focus(page, "Team Bravo")
    g = graph(page)
    fx = g["focus"][0]["x"]
    xs = {n["x"] for n in g["related"]}
    ys = [n["y"] for n in g["related"]]
    assert len(xs) == 1 and fx < xs.pop()
    assert ys == sorted(ys) and len(set(ys)) == 3


def test_tc08_live_update(page):
    pick_focus(page, "Team Alpha")
    assert len(graph(page)["related"]) == 2
    pick(page, "candidates-list", "Eve")
    page.click("#btn-add")
    assert len(graph(page)["related"]) == 3
    pick(page, "selected-list", "Alice")
    page.click("#btn-remove")
    assert len(graph(page)["related"]) == 2


def test_tc09_per_parent_memory(page):
    pick_focus(page, "Team Delta")
    pick(page, "candidates-list", "Frank", "Grace")
    page.click("#btn-add")
    pick_focus(page, "Team Charlie")
    assert options(page, "selected-list") == []
    pick_focus(page, "Team Delta")
    assert options(page, "selected-list") == ["Frank", "Grace"]


def test_tc10_multi_move(page):
    pick_focus(page, "Team Charlie")
    pick(page, "candidates-list", "Alice", "Dave", "Heidi")
    page.click("#btn-add")
    assert options(page, "selected-list") == ["Alice", "Dave", "Heidi"]


def test_tc11_double_click(page):
    pick_focus(page, "Team Charlie")
    page.dblclick("#candidates-list option:text-is('Bob')")
    assert options(page, "selected-list") == ["Bob"]
    page.dblclick("#selected-list option:text-is('Bob')")
    assert options(page, "selected-list") == []
    assert "Bob" in options(page, "candidates-list")


def test_tc12_button_state(page):
    assert page.locator("#btn-add").is_disabled()
    assert page.locator("#btn-remove").is_disabled()
    pick_focus(page, "Team Alpha")
    assert page.locator("#btn-add").is_disabled()
    pick(page, "candidates-list", "Eve")
    assert page.locator("#btn-add").is_enabled()
    assert page.locator("#btn-remove").is_disabled()
    pick(page, "selected-list", "Alice")
    assert page.locator("#btn-remove").is_enabled()


def test_tc13_empty_graph(page):
    pick_focus(page, "Team Delta")
    g = graph(page)
    assert len(g["focus"]) == 1 and g["related"] == [] and g["connectors"] == 0


def test_tc14_no_duplicates(page):
    pick_focus(page, "Team Charlie")
    page.evaluate(
        """() => { const {store} = window.relationApp;
                   store.add('parent', 'p3', ['c1', 'c1']); store.add('parent', 'p3', ['c1']);
                   window.relationApp.render(); }"""
    )
    sel, cand = options(page, "selected-list"), options(page, "candidates-list")
    assert sel.count("Alice") == 1 and "Alice" not in cand


# ---------- child (reverse) view ----------

def switch_view(page, view):
    page.click(f"[data-view-tab={view}]")


def test_tc15_reverse_view_labels(page):
    switch_view(page, "child")
    assert page.inner_text("#focus-label") == "Child"
    assert page.inner_text("#selected-label") == "Parents"
    assert page.inner_text("#candidates-label") == "Candidate parents"
    assert len(options(page, "focus-list")) == 8


def test_tc16_reverse_view_shows_parents(page):
    switch_view(page, "child")
    pick_focus(page, "Bob")  # in Alpha and Bravo
    assert options(page, "selected-list") == ["Team Alpha", "Team Bravo"]
    assert options(page, "candidates-list") == ["Team Charlie", "Team Delta"]


def test_tc17_reverse_view_shapes(page):
    switch_view(page, "child")
    pick_focus(page, "Bob")
    g = graph(page)
    assert [n["tag"] for n in g["focus"]] == ["circle"]
    assert [n["tag"] for n in g["related"]] == ["rect", "rect"]
    assert g["focus"][0]["x"] < g["related"][0]["x"]


def test_tc18_views_share_data(page):
    pick_focus(page, "Team Delta")
    pick(page, "candidates-list", "Heidi")
    page.click("#btn-add")
    switch_view(page, "child")
    pick_focus(page, "Heidi")
    assert options(page, "selected-list") == ["Team Delta"]
    pick(page, "selected-list", "Team Delta")
    page.click("#btn-remove")
    switch_view(page, "parent")
    # parent view kept its focus (Team Delta) and reflects the removal
    assert page.input_value("#focus-list") == "p4"
    assert options(page, "selected-list") == []


def test_tc19_many_to_many(page):
    pick_focus(page, "Team Charlie")
    # Alice already belongs to Alpha; still a candidate for Charlie (Q4: allowed)
    assert "Alice" in options(page, "candidates-list")


# ---------- form submission ----------

def test_tc20_hidden_inputs(page):
    assert hidden_links(page) == ["p1:c1", "p1:c2", "p2:c2", "p2:c3", "p2:c4"]
    pick_focus(page, "Team Alpha")
    pick(page, "candidates-list", "Eve")
    page.click("#btn-add")
    pick(page, "selected-list", "Alice")
    page.click("#btn-remove")
    assert hidden_links(page) == ["p1:c2", "p2:c2", "p2:c3", "p2:c4", "p1:c5"]


# ---------- graph zoom / auto-fit ----------

def graph_size(page):
    return page.evaluate(
        """() => {
        const g = document.getElementById('graph'), p = document.querySelector('.graph-pane');
        const vb = g.viewBox.baseVal;
        // every drawn element must lie inside the viewBox (nothing clipped)
        const inside = [...g.children].every(n => { const b = n.getBBox();
            return b.x >= vb.x && b.y >= vb.y &&
                   b.x + b.width <= vb.x + vb.width && b.y + b.height <= vb.y + vb.height; });
        return {w: g.width.baseVal.value, h: g.height.baseVal.value,
                pw: p.clientWidth, ph: p.clientHeight,
                level: document.getElementById('zoom-level').textContent, inside};
    }"""
    )


def test_tc26_graph_fits_pane(page):
    pick_focus(page, "Team Bravo")
    s = graph_size(page)
    assert s["w"] <= s["pw"] and s["h"] <= s["ph"]
    assert s["inside"]
    assert page.get_attribute("#zoom-fit", "aria-pressed") == "true"


def test_tc27_long_labels_not_clipped(page):
    page.evaluate(
        """() => { const {store} = window.relationApp;
                   store.parentIndex.get('p1').label = 'A really very long parent team name';
                   store.childIndex.get('c1').label = 'Alice with an extraordinarily long surname';
                   window.relationApp.render(); }"""
    )
    pick_focus(page, "A really very long parent team name")
    s = graph_size(page)
    assert s["inside"]
    assert s["w"] <= s["pw"]  # fit mode shrinks to keep it all visible


def test_tc28_zoom_buttons(page):
    pick_focus(page, "Team Bravo")
    page.click("#zoom-reset")
    one = graph_size(page)
    assert one["level"] == "100%"
    assert page.get_attribute("#zoom-fit", "aria-pressed") == "false"
    page.click("#zoom-in")
    bigger = graph_size(page)
    assert bigger["level"] == "125%" and bigger["w"] > one["w"]
    page.click("#zoom-out")
    page.click("#zoom-out")
    assert graph_size(page)["level"] == "80%"
    # manual zoom survives a re-render (moving an item)
    pick(page, "candidates-list", "Eve")
    page.click("#btn-add")
    assert graph_size(page)["level"] == "80%"
    page.click("#zoom-fit")
    assert page.get_attribute("#zoom-fit", "aria-pressed") == "true"


def test_tc29_ctrl_wheel_zoom(page):
    pick_focus(page, "Team Bravo")
    page.click("#zoom-reset")
    page.hover(".graph-pane")
    page.keyboard.down("Control")
    page.mouse.wheel(0, -100)
    page.keyboard.up("Control")
    assert graph_size(page)["level"] == "125%"


# ---------- crosscheck #1 follow-ups (X3, X4, X5) ----------

def test_tc21_related_labels(page):
    pick_focus(page, "Team Bravo")
    assert graph(page)["labels"] == ["Team Bravo", "Bob", "Carol", "Dave"]


def test_tc22_graph_follows_focus_change(page):
    pick_focus(page, "Team Bravo")
    pick_focus(page, "Team Alpha")
    g = graph(page)
    assert [n["id"] for n in g["focus"]] == ["p1"]
    assert [n["id"] for n in g["related"]] == ["c1", "c2"]
    assert g["labels"] == ["Team Alpha", "Alice", "Bob"]


def test_tc23_multi_move_back(page):
    pick_focus(page, "Team Bravo")
    pick(page, "selected-list", "Bob", "Dave")
    page.click("#btn-remove")
    assert options(page, "selected-list") == ["Carol"]
    assert {"Bob", "Dave"} <= set(options(page, "candidates-list"))
    assert len(graph(page)["related"]) == 1


def load_variant(browser, tmp_path, *replacements):
    """Open a copy of index.html with its sample data edited; returns (page, warnings).

    Each replacement is (old, new) on the HTML source; <base> keeps static/ paths working.
    """
    root = Path(__file__).resolve().parent.parent
    html = (root / "index.html").read_text()
    html = html.replace("<head>", f'<head><base href="{root.as_uri()}/">', 1)
    for old, new in replacements:
        assert old in html, old
        html = html.replace(old, new, 1)
    f = tmp_path / "variant.html"
    f.write_text(html)

    pg = browser.new_page(viewport={"width": 1400, "height": 800})
    errors, warnings = [], []
    pg.on("pageerror", lambda e: errors.append(e))
    pg.on("console", lambda m: m.type == "warning" and warnings.append(m.text))
    pg.goto(f.as_uri())
    assert not errors, errors
    return pg, warnings


def test_tc24_invalid_links_skipped(browser, tmp_path):
    pg, warnings = load_variant(
        browser, tmp_path, ('["p2", "c4"]', '["p2", "c4"], ["p9", "c1"], ["p1", "c99"], ["p3"]')
    )
    assert len(warnings) == 3
    assert hidden_links(pg) == ["p1:c1", "p1:c2", "p2:c2", "p2:c3", "p2:c4"]
    pick_focus(pg, "Team Alpha")
    assert options(pg, "selected-list") == ["Alice", "Bob"]
    pg.close()


def test_tc30_keyboard_enter_moves(page):
    pick_focus(page, "Team Charlie")
    page.focus("#candidates-list")
    page.keyboard.press("ArrowDown")  # selects first candidate (Alice)
    page.keyboard.press("Enter")
    assert options(page, "selected-list") == ["Alice"]
    page.focus("#selected-list")
    page.keyboard.press("ArrowDown")
    page.keyboard.press("Enter")
    assert options(page, "selected-list") == []
    assert "Alice" in options(page, "candidates-list")


# ---------- crosscheck #2 follow-ups (Y1 … Y4) ----------

def test_tc31_focus_node_at_top(browser, tmp_path):
    kids = "".join(f', {{"id": "k{i}", "label": "Kid {i}"}}' for i in range(40))
    links = "".join(f', ["p4", "k{i}"]' for i in range(40))
    pg, _ = load_variant(
        browser, tmp_path,
        ('{"id": "c8", "label": "Heidi"}', '{"id": "c8", "label": "Heidi"}' + kids),
        ('["p2", "c4"]', '["p2", "c4"]' + links),
    )
    pick_focus(pg, "Team Delta")
    g = graph(pg)
    assert g["focus"][0]["y"] == g["related"][0]["y"]
    # square is visible near the top of the pane, not scrolled away
    pane = pg.locator(".graph-pane").bounding_box()
    sq = pg.locator("[data-role=focus]").bounding_box()
    assert pane["y"] <= sq["y"] <= pane["y"] + 60
    pg.close()


def test_tc32_duplicate_ids_skipped(browser, tmp_path):
    pg, warnings = load_variant(
        browser, tmp_path,
        ('{"id": "p4", "label": "Team Delta"}', '{"id": "p4", "label": "Team Delta"}, {"id": "p1", "label": "Dup"}'),
        ('{"id": "c8", "label": "Heidi"}', '{"id": "c8", "label": "Heidi"}, {"id": "c2", "label": "Dup"}'),
    )
    assert len(warnings) == 2
    assert options(pg, "focus-list") == ["Team Alpha", "Team Bravo", "Team Charlie", "Team Delta"]
    pick_focus(pg, "Team Charlie")
    assert "Dup" not in options(pg, "candidates-list")
    pg.close()


def test_tc33_colon_in_id_warns(browser, tmp_path):
    pg, warnings = load_variant(browser, tmp_path, ('"id": "p4"', '"id": "p:4"'))
    assert len(warnings) == 1 and ":" in warnings[0]
    assert len(options(pg, "focus-list")) == 4  # still loaded
    pg.close()


def test_tc34_graph_text_alternative(page):
    g = page.locator("#graph")
    assert g.get_attribute("role") == "img"
    assert g.get_attribute("aria-label") == "Select a parent on the left"
    pick_focus(page, "Team Bravo")
    assert g.get_attribute("aria-label") == "Team Bravo: 3 children — Bob, Carol, Dave"
    pick_focus(page, "Team Delta")
    assert g.get_attribute("aria-label") == "Team Delta: no children"
    switch_view(page, "child")
    pick_focus(page, "Alice")
    assert g.get_attribute("aria-label") == "Alice: 1 parent — Team Alpha"
    # every <label> on the page is tied to a control
    assert page.eval_on_selector_all("label", "ls => ls.every(l => l.control)")


# ---------- selection highlight, list <-> graph ----------

def highlighted(page):
    return page.evaluate(
        """() => {
        const ids = sel => [...document.querySelectorAll('#graph ' + sel + '.highlight')].map(n => n.dataset.id);
        return {items: ids('.related-item'), connectors: ids('.connector')};
    }"""
    )


def selected_values(page):
    return page.eval_on_selector("#selected-list", "s => [...s.selectedOptions].map(o => o.value)")


def test_tc35_list_selection_highlights_graph(page):
    pick_focus(page, "Team Bravo")
    pick(page, "selected-list", "Bob", "Dave")
    h = highlighted(page)
    assert sorted(h["items"]) == ["c2", "c4"] and sorted(h["connectors"]) == ["c2", "c4"]
    # survives a re-render: add a candidate, selection in Selected is kept (FR-21)
    pick(page, "candidates-list", "Eve")
    page.click("#btn-add")
    assert sorted(highlighted(page)["items"]) == ["c2", "c4"]
    pick(page, "selected-list")  # deselect all
    assert highlighted(page) == {"items": [], "connectors": []}


def test_tc36_graph_click_selects_in_list(page):
    pick_focus(page, "Team Bravo")
    page.click("#graph .related-item[data-id=c3] .node")
    assert selected_values(page) == ["c3"]
    assert highlighted(page)["items"] == ["c3"]
    assert page.locator("#btn-remove").is_enabled()
    page.click("#graph .related-item[data-id=c4] .label", modifiers=["ControlOrMeta"])
    assert selected_values(page) == ["c3", "c4"]
    page.click("#graph .related-item[data-id=c3] .node", modifiers=["ControlOrMeta"])
    assert selected_values(page) == ["c4"]
    page.click("#graph .related-item[data-id=c2] .label")  # plain click replaces selection
    assert selected_values(page) == ["c2"]
    page.click("#graph .related-item[data-id=c2] .node")
    page.click("#btn-remove")  # graph selection drives the → button
    assert "Bob" in options(page, "candidates-list")
    pick(page, "selected-list", "Carol")
    box = page.locator(".graph-pane").bounding_box()
    page.mouse.click(box["x"] + box["width"] - 20, box["y"] + box["height"] - 20)  # empty space
    assert selected_values(page) == [] and highlighted(page)["items"] == []
    assert page.locator("#btn-remove").is_disabled()


def test_tc37_scrolls_to_selected_item(browser, tmp_path):
    kids = "".join(f', {{"id": "k{i}", "label": "Kid {i}"}}' for i in range(40))
    links = "".join(f', ["p4", "k{i}"]' for i in range(40))
    pg, _ = load_variant(
        browser, tmp_path,
        ('{"id": "c8", "label": "Heidi"}', '{"id": "c8", "label": "Heidi"}' + kids),
        ('["p2", "c4"]', '["p2", "c4"]' + links),
    )
    pick_focus(pg, "Team Delta")
    # graph -> list: clicking the last node scrolls the Selected list to it
    pg.click("#graph .related-item[data-id=k39] .node")
    assert pg.eval_on_selector("#selected-list", "s => s.scrollTop") > 0
    # list -> graph: selecting in the list scrolls the pane to the node
    pg.eval_on_selector(".graph-pane", "p => p.scrollTo(0, 0)")
    pick(pg, "selected-list", "Kid 38")
    pane = pg.locator(".graph-pane").bounding_box()
    node = pg.locator("#graph .related-item[data-id=k38] .node").bounding_box()
    assert pane["y"] <= node["y"] and node["y"] + node["height"] <= pane["y"] + pane["height"]
    pg.close()


def test_tc38_dblclick_jumps_to_other_view(page):
    pick_focus(page, "Team Bravo")
    page.dblclick("#graph .related-item[data-id=c2] .node")  # Bob
    assert page.get_attribute("[data-view-tab=child]", "aria-selected") == "true"
    assert page.inner_text("#focus-label") == "Child"
    assert page.input_value("#focus-list") == "c2"
    assert options(page, "selected-list") == ["Team Alpha", "Team Bravo"]
    assert selected_values(page) == ["p2"]  # where we came from, highlighted
    assert highlighted(page)["items"] == ["p2"]
    assert [n["tag"] for n in graph(page)["focus"]] == ["circle"]
    # and back again via the label: lands on Team Alpha with Bob highlighted
    page.dblclick("#graph .related-item[data-id=p1] .label")
    assert page.inner_text("#focus-label") == "Parent"
    assert page.input_value("#focus-list") == "p1"
    assert highlighted(page)["items"] == ["c2"]
    # the jumped-from view kept nothing stale: By child still remembers Bob
    switch_view(page, "child")
    assert page.input_value("#focus-list") == "c2"
