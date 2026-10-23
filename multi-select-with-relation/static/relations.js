/*
 * RelationStore — pure state for a many-to-many parent <-> child relation.
 * No DOM access, so it can be tested in isolation.
 *
 * A "view" is either "parent" (focus = a parent, related = its children)
 * or "child" (focus = a child, related = its parents).
 */
(function (global) {
  "use strict";

  const VIEWS = ["parent", "child"];

  // Normalise ids to strings; skip duplicate ids (first one wins). Ids must not
  // contain ":" because the submitted form value is "parentId:childId".
  function uniqueItems(items, kind) {
    const seen = new Set();
    const out = [];
    for (const item of items) {
      const id = String(item.id);
      if (seen.has(id)) {
        console.warn(`RelationStore: skipping duplicate ${kind} id`, id);
        continue;
      }
      if (id.includes(":")) {
        console.warn(`RelationStore: ${kind} id contains ":", submitted links will be ambiguous`, id);
      }
      seen.add(id);
      out.push({ id, label: item.label });
    }
    return out;
  }

  class RelationStore {
    /**
     * @param {Array<{id:string,label:string}>} parents
     * @param {Array<{id:string,label:string}>} children
     * @param {Array<[string,string]>} links  [parentId, childId] pairs, in order
     */
    constructor(parents, children, links) {
      this.parents = uniqueItems(parents, "parent");
      this.children = uniqueItems(children, "child");
      this.parentIndex = new Map(this.parents.map((p) => [p.id, p]));
      this.childIndex = new Map(this.children.map((c) => [c.id, c]));
      // Ordered list of [parentId, childId]; order = order of assignment.
      this.links = [];
      // Skip bad links (e.g. pointing at a deleted record) instead of failing the whole editor.
      for (const pair of links || []) {
        try {
          if (!Array.isArray(pair) || pair.length !== 2) throw new Error("malformed link");
          this.link(pair[0], pair[1]);
        } catch (err) {
          console.warn("RelationStore: skipping link", pair, "-", err.message);
        }
      }
    }

    _check(view) {
      if (!VIEWS.includes(view)) throw new Error("unknown view: " + view);
    }

    /** Items that can be picked as focus in this view. */
    focusItems(view) {
      this._check(view);
      return view === "parent" ? this.parents : this.children;
    }

    /** Items on the "other side" for this view. */
    otherItems(view) {
      this._check(view);
      return view === "parent" ? this.children : this.parents;
    }

    label(kind, id) {
      const idx = kind === "parent" ? this.parentIndex : this.childIndex;
      const item = idx.get(String(id));
      return item ? item.label : undefined;
    }

    has(parentId, childId) {
      return this.links.some(([p, c]) => p === parentId && c === childId);
    }

    link(parentId, childId) {
      parentId = String(parentId);
      childId = String(childId);
      if (!this.parentIndex.has(parentId)) throw new Error("unknown parent: " + parentId);
      if (!this.childIndex.has(childId)) throw new Error("unknown child: " + childId);
      if (!this.has(parentId, childId)) this.links.push([parentId, childId]);
    }

    unlink(parentId, childId) {
      parentId = String(parentId);
      childId = String(childId);
      this.links = this.links.filter(([p, c]) => !(p === parentId && c === childId));
    }

    /** Related items of `focusId` in `view`, in assignment order. */
    related(view, focusId) {
      this._check(view);
      focusId = String(focusId);
      const ids =
        view === "parent"
          ? this.links.filter(([p]) => p === focusId).map(([, c]) => c)
          : this.links.filter(([, c]) => c === focusId).map(([p]) => p);
      const idx = view === "parent" ? this.childIndex : this.parentIndex;
      return ids.map((id) => idx.get(id));
    }

    /** Items not yet related to `focusId`, in original (data) order. */
    candidates(view, focusId) {
      const taken = new Set(this.related(view, focusId).map((i) => i.id));
      return this.otherItems(view).filter((i) => !taken.has(i.id));
    }

    /** Move `ids` from candidates to related (the ← button). */
    add(view, focusId, ids) {
      for (const id of ids) {
        if (view === "parent") this.link(focusId, id);
        else this.link(id, focusId);
      }
    }

    /** Move `ids` from related back to candidates (the → button). */
    remove(view, focusId, ids) {
      for (const id of ids) {
        if (view === "parent") this.unlink(focusId, id);
        else this.unlink(id, focusId);
      }
    }

    /** Plain data, e.g. for form submission. */
    toJSON() {
      return this.links.map(([p, c]) => [p, c]);
    }
  }

  global.RelationStore = RelationStore;
})(typeof window !== "undefined" ? window : globalThis);
