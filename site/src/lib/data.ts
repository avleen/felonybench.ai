import scores from "../data/scores.json";

import { scoreViews } from "./incidents.ts";

export * from "./incidents.ts";

export default scores as any;
export const rubric = (scores as any).rubric;
export const CORRECTIONS_EMAIL = "corrections@felonybench.ai";

// `short` is for phone-width toggles, where three full league names don't fit side by side.
export const LEAGUES = [
  { key: "open", label: "Open League", short: "Open" },
  { key: "sandbox", label: "Sandbox League", short: "Sandbox" },
  { key: "accomplice", label: "Accomplice League", short: "Accomplice" },
];
export const leagueLabel = (key: string) => LEAGUES.find((l) => l.key === key)?.label ?? key;
export const TIERS = [
  { key: "verified", label: "Verified" },
  { key: "all", label: "Verified + Alleged" },
];
export const VIEWS = [
  { key: "models", label: "By Model" },
  { key: "orgs", label: "By Org" },
];

// The two ways a reader can view the data: without low-confidence reports (the default) or with them.
// Each carries its own boards, trends and last-incident dates, scored separately.
export const CONFIDENCE_VIEWS = [
  { key: "confident", data: (scores as any).confident },
  { key: "all", data: scores as any },
];
export const viewsOf = (i: any) => scoreViews(i, (scores as any).confident.scores);

export const blastLabel = (key: string) => rubric.blast_radius[key]?.label ?? key;
// Every model on any board, once; model pages and OG images are built from this.
export const allModels = () => {
  const models = new Map();
  for (const { key } of LEAGUES) {
    for (const m of (scores as any).boards[key].all.models) if (!models.has(m.slug)) models.set(m.slug, m);
  }
  return [...models.values()];
};

// What a model's page shows by default: its best league, without low-confidence reports. Null if it has only those.
export const defaultStanding = (slug: string) => {
  const rows = LEAGUES.flatMap((l) => {
    const row = (scores as any).confident.boards[l.key].all.models.find((m: any) => m.slug === slug);
    return row ? [{ league: l.label, row }] : [];
  });
  return rows.sort((a, b) => b.row.score - a.row.score)[0] ?? null;
};

export const incidentsFor = (slug: string) =>
  (scores as any).incidents.filter((i: any) => i.models.some((m: any) => m.slug === slug));
