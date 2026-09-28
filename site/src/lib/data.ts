import scores from "../data/scores.json";

export default scores as any;
export const rubric = (scores as any).rubric;
export const REPO = "https://github.com/avleen/felonybench.ai";

export const LEAGUES = [
  { key: "open", label: "Open League" },
  { key: "sandbox", label: "Sandbox League" },
];
export const TIERS = [
  { key: "verified", label: "Verified" },
  { key: "all", label: "Verified + Alleged" },
];
export const VIEWS = [
  { key: "models", label: "By Model" },
  { key: "orgs", label: "By Org" },
];

export const fmt = (n: number) => n.toLocaleString("en-US", { maximumFractionDigits: 2 });
export const blastLabel = (key: string) => rubric.blast_radius[key]?.label ?? key;
export const incidentsFor = (slug: string) =>
  (scores as any).incidents.filter((i: any) => i.models.some((m: any) => m.slug === slug));

// Incidents dated only to the month show as "April 2026", never as a made-up day.
export const occurred = (i: any) =>
  i.date_precision === "month"
    ? new Date(`${i.date}T00:00:00Z`).toLocaleString("en-US", { month: "long", year: "numeric", timeZone: "UTC" })
    : i.date;
