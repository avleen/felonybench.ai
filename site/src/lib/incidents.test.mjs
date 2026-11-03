import assert from "node:assert/strict";
import { test } from "node:test";
import {
  chargedOrgs, clip, coDefendants, daysSince, fmt, hasCoDefendants, incidentDescription, incidentTitle,
  isLow, modelTitle, newerThanLatest, occurred, scoreViews,
} from "./incidents.ts";

test("one org charged is just its name", () => {
  const i = { charged: ["Anthropic"] };
  assert.equal(coDefendants(i), "Anthropic");
  assert.equal(chargedOrgs(i), "Anthropic");
  assert.equal(hasCoDefendants(i), false);
});

test("co-defendants name the lead first", () => {
  const i = { charged: ["Anthropic", "Moonshot AI"] };
  assert.equal(coDefendants(i), "Anthropic, with Moonshot AI");
  assert.equal(chargedOrgs(i), "Anthropic and Moonshot AI");
  assert.equal(hasCoDefendants(i), true);
});

test("three orgs read as a list", () => {
  const i = { charged: ["A", "B", "C"] };
  assert.equal(coDefendants(i), "A, with B, C");
  assert.equal(chargedOrgs(i), "A, B and C");
});

test("dates only claim the precision they have", () => {
  assert.equal(occurred({ date: "2026-04-01", date_precision: "month" }), "April 2026");
  assert.equal(occurred({ date: "2026-07-23", date_precision: "before" }), "Before 23 July 2026");
  assert.equal(occurred({ date: "2026-07-23", date_precision: "day" }), "2026-07-23");
});

test("a same-day hidden report isn't newer, even sorted after the latest shown", () => {
  const shown = { id: "2026-09-02-a", date: "2026-09-02" };
  const hidden = { id: "2026-09-02-b", date: "2026-09-02" };
  assert.equal(newerThanLatest([shown, hidden], [shown]), 0);
});

test("a later hidden report is newer", () => {
  const shown = { id: "2026-09-02-a", date: "2026-09-02" };
  const hidden = { id: "2026-09-03-b", date: "2026-09-03" };
  assert.equal(newerThanLatest([shown, hidden], [shown]), 1);
});

test("with nothing shown, every report is newer", () => {
  assert.equal(newerThanLatest([{ date: "2026-09-02" }], []), 1);
  assert.equal(newerThanLatest([], []), 0);
});

test("numbers keep up to two decimals", () => {
  assert.equal(fmt(1092.25), "1,092.25");
  assert.equal(fmt(10), "10");
});

test("a hidden prior gives an incident two scores, one per view", () => {
  const i = { id: "a", breakdown: { total: 31.25 }, badges: ["recidivist"] };
  const views = scoreViews(i, { a: { breakdown: { total: 25 }, badges: [] } });
  assert.deepEqual(views.map((v) => [v.key, v.breakdown.total]), [["confident", 25], ["all", 31.25]]);
  assert.deepEqual(views[0].badges, []);
});

test("when both views agree there is one score, with no view key", () => {
  const i = { id: "a", breakdown: { total: 25 }, badges: [] };
  const views = scoreViews(i, { a: { breakdown: { total: 25 }, badges: [] } });
  assert.equal(views.length, 1);
  assert.equal(views[0].key, undefined);
});

test("a low-confidence incident has only its own score", () => {
  const views = scoreViews({ id: "a", breakdown: { total: 25 }, badges: [] }, {});
  assert.deepEqual(views.map((v) => v.breakdown.total), [25]);
});

test("isLow goes by the record's own confidence", () => {
  assert.equal(isLow({ confidence: "low" }), true);
  assert.equal(isLow({ confidence: "medium" }), false);
});

test("days since is whole days, and never negative", () => {
  const now = Date.parse("2026-01-11T12:00:00Z");
  assert.equal(daysSince("2026-01-01", now), 10);
  assert.equal(daysSince("2026-01-12", now), 0);
});

test("clip leaves short text alone and marks long text", () => {
  assert.equal(clip("short", 10), "short");
  assert.equal(clip("a long sentence here", 10), "a long se…");
  assert.equal(clip("x".repeat(200), 155).length, 155);
});

test("model title doesn't repeat a lab already in the name", () => {
  assert.equal(modelTitle({ name: "DeepSeek V4", org: "DeepSeek" }), "DeepSeek V4 rap sheet");
  assert.equal(modelTitle({ name: "Undisclosed model", org: "xAI" }), "xAI Undisclosed model rap sheet");
});

test("low-confidence titles and descriptions carry the qualifier, even when clipped", () => {
  const i = { id: "2026-01-01-x", org: "Acme", confidence: "low", summary: "s".repeat(300), models: [{ name: "M" }] };
  assert.equal(incidentTitle(i), "Low-confidence report: Acme / M: Case FB-2026-01-01-x");
  assert.ok(incidentDescription(i).startsWith("Low-confidence report: "));
  assert.equal(incidentDescription(i).length, 155);
  assert.equal(incidentTitle({ ...i, confidence: "high" }), "Acme / M: Case FB-2026-01-01-x");
});
