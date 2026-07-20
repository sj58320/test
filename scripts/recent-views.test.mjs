import test from "node:test";
import assert from "node:assert/strict";
import {
  RECENT_VIEW_LIMIT,
  addRecentView,
  normalizeRecentViews,
  removeRecentView
} from "../assets/js/recent-views.mjs";

function entry(number) {
  return {
    targetId: `faq-${number}`,
    type: "faq",
    title: `FAQ ${number}`,
    visitedAt: number
  };
}

test("keeps at most five recent views", () => {
  const result = Array.from({ length: 7 }, (_, index) => entry(index + 1))
    .reduce((items, item) => addRecentView(items, item), []);
  assert.equal(result.length, RECENT_VIEW_LIMIT);
  assert.deepEqual(result.map(item => item.targetId), ["faq-7", "faq-6", "faq-5", "faq-4", "faq-3"]);
});

test("moves a repeated item to the front without duplicating it", () => {
  const initial = [entry(3), entry(2), entry(1)];
  const result = addRecentView(initial, { ...entry(1), visitedAt: 10 });
  assert.deepEqual(result.map(item => item.targetId), ["faq-1", "faq-3", "faq-2"]);
  assert.equal(result[0].visitedAt, 10);
});

test("filters malformed and duplicated stored entries", () => {
  const result = normalizeRecentViews([entry(1), null, entry(1), { targetId: "", type: "faq", title: "Missing" }]);
  assert.deepEqual(result.map(item => item.targetId), ["faq-1"]);
});

test("removes one recent view", () => {
  assert.deepEqual(removeRecentView([entry(3), entry(2), entry(1)], "faq-2").map(item => item.targetId), ["faq-3", "faq-1"]);
});
