import assert from "node:assert/strict";
import { test } from "node:test";
import { chargedOrgs, coDefendants, fmt, hasCoDefendants, newerThanLatest, occurred } from "./incidents.ts";

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
