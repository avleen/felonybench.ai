import scores from "../data/scores.json";

export default scores as any;
export const rubric = (scores as any).rubric;
export const CORRECTIONS_EMAIL = "corrections@felonybench.ai";

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

// Imprecise dates are shown as such, never as a made-up day:
// "month" → "April 2026"; "before" (date is the latest possible day) → "Before 23 July 2026".
export const occurred = (i: any) => {
  const d = new Date(`${i.date}T00:00:00Z`);
  if (i.date_precision === "month") return d.toLocaleString("en-US", { month: "long", year: "numeric", timeZone: "UTC" });
  if (i.date_precision === "before") return `Before ${d.toLocaleString("en-GB", { day: "numeric", month: "long", year: "numeric", timeZone: "UTC" })}`;
  return i.date;
};
