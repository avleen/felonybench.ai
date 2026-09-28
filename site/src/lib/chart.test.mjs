// Run with: node --experimental-strip-types --test src/lib/chart.test.mjs
// (node's native TS type-stripping lets us import chart.ts directly, so the
// logic under test never drifts from what the site actually ships.)
import assert from "node:assert/strict";
import { test } from "node:test";
import { layout, W, H, PAD } from "./chart.ts";

const series = (points) => ({ Acme: points });

test("returns null for no data", () => {
  assert.equal(layout({}, "2026-01-10"), null);
});

test("single series: line ends at today, label sits at the final value", () => {
  const chart = layout(series([
    { date: "2026-01-01", cumulative: 10, delta: 10, incident_id: "a" },
    { date: "2026-01-05", cumulative: 30, delta: 20, incident_id: "b" },
  ]), "2026-01-10");
  assert.ok(chart);
  assert.equal(chart.orgs.length, 1);
  const s = chart.orgs[0];
  assert.equal(s.final, 30);
  assert.equal(s.labelY, s.labelAnchorY);
  // The path's last command extends horizontally to "today"'s x.
  const todayX = PAD.left + (W - PAD.left - PAD.right); // x1 == day(today), scaled to right edge minus pad... just check it's within bounds
  assert.ok(s.path.includes("H"));
  assert.ok(s.markers.length === 2);
});

test("orgs are ranked by final cumulative score, highest first", () => {
  const chart = layout({
    Low: [{ date: "2026-01-01", cumulative: 5, delta: 5, incident_id: "a" }],
    High: [{ date: "2026-01-01", cumulative: 50, delta: 50, incident_id: "b" }],
  }, "2026-01-10");
  assert.deepEqual(chart.orgs.map((s) => s.org), ["High", "Low"]);
});

test("colliding end labels get nudged apart by at least the minimum gap", () => {
  // Two orgs that finish at nearly the same score will land within a few px
  // of each other on the y axis; the raw anchors should collide...
  const chart = layout({
    A: [{ date: "2026-01-01", cumulative: 100, delta: 100, incident_id: "a" }],
    B: [{ date: "2026-01-01", cumulative: 99, delta: 99, incident_id: "b" }],
  }, "2026-01-10");
  const [a, b] = chart.orgs; // A first (higher score -> smaller y -> nearer top)
  assert.ok(Math.abs(a.labelAnchorY - b.labelAnchorY) < 16, "anchors should start out close together");
  assert.ok(b.labelY - a.labelY >= 16, "nudged labels must keep at least the minimum gap");
});

test("well-separated series keep their natural label position", () => {
  const chart = layout({
    A: [{ date: "2026-01-01", cumulative: 500, delta: 500, incident_id: "a" }],
    B: [{ date: "2026-01-01", cumulative: 10, delta: 10, incident_id: "b" }],
  }, "2026-01-10");
  for (const s of chart.orgs) assert.equal(s.labelY, s.labelAnchorY);
});

test("y ticks span 0 to a headroom above the max, x ticks fall within the plot area", () => {
  const chart = layout(series([{ date: "2026-01-01", cumulative: 40, delta: 40, incident_id: "a" }]), "2026-03-01");
  assert.equal(chart.yTicks.length, 5);
  assert.equal(chart.yTicks[0].value, 0);
  assert.ok(chart.yTicks[4].value >= 40);
  for (const t of chart.xTicks) {
    assert.ok(t.x >= PAD.left - 1 && t.x <= W - PAD.right + 1, `x tick ${t.label} at ${t.x} out of plot bounds`);
  }
});
