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

// Everyone charged with an incident, jointly and severally. The scorer decides who: this only formats it.
// e.g. "Anthropic, with Moonshot AI".
export const coDefendants = (i: any) => {
  const [lead, ...others] = i.charged;
  return others.length ? `${lead}, with ${others.join(", ")}` : lead;
};

// The same orgs as a plain list: "Anthropic and Moonshot AI".
export const chargedOrgs = (i: any) =>
  i.charged.length > 2 ? `${i.charged.slice(0, -1).join(", ")} and ${i.charged.at(-1)}` : i.charged.join(" and ");
export const hasCoDefendants = (i: any) => i.charged.length > 1;

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
