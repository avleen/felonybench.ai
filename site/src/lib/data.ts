import scores from "../data/scores.json";

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
export const isLow = (i: any) => !(scores as any).confident.incident_ids.includes(i.id);

export const fmt = (n: number) => n.toLocaleString("en-US", { maximumFractionDigits: 2 });
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

// Everyone charged with an incident, jointly and severally: the lab, then each other lab and modifier.
// e.g. "Alibaba, with OrcaRouter (abliterated)".
export const coDefendants = (i: any) => {
  // An org can be both a model's lab and a modifier, so keep what it did even if it was seen first as a lab.
  const roles = new Map<string, string | undefined>([[i.org, undefined]]);
  for (const m of i.models) {
    if (m.org && !roles.has(m.org)) roles.set(m.org, undefined);
    if (m.modified_by && !roles.get(m.modified_by)) roles.set(m.modified_by, m.modification);
  }
  const [lead, ...extra] = [...roles].map(([org, did]) => (did ? `${org} (${did})` : org));
  return extra.length ? `${lead}, with ${extra.join(", ")}` : lead;
};

// The same orgs as a plain list: "Alibaba and OrcaRouter".
export const chargedOrgs = (i: any) => {
  const orgs = [...new Set([i.org, ...i.models.flatMap((m: any) => [m.org, m.modified_by]).filter(Boolean)])] as string[];
  return orgs.length > 2 ? `${orgs.slice(0, -1).join(", ")} and ${orgs.at(-1)}` : orgs.join(" and ");
};
export const hasCoDefendants = (i: any) => i.models.some((m: any) => [m.org, m.modified_by].some((org) => org && org !== i.org));

export const incidentsFor = (slug: string) =>
  (scores as any).incidents.filter((i: any) => i.models.some((m: any) => m.slug === slug));

// Imprecise dates are shown as such, never as a made-up day:
// "month" → "April 2026"; "before" (date is the latest possible day) → "Before 23 July 2026".
export const occurred = (i: any) => {
  const d = new Date(`${i.date}T00:00:00Z`);
  if (i.date_precision === "month") return d.toLocaleString("en-US", { month: "long", year: "numeric", timeZone: "UTC" });
  if (i.date_precision === "before") return `Before ${d.toLocaleString("en-GB", { day: "numeric", month: "long", year: "numeric", timeZone: "UTC" })}`;
  return i.date;
};
