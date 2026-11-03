// Pure helpers over incident records. Nothing here imports the data, so tests can hand-build incidents.

export const fmt = (n: number) => n.toLocaleString("en-US", { maximumFractionDigits: 2 });

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

// Imprecise dates are shown as such, never as a made-up day:
// "month" → "April 2026"; "before" (date is the latest possible day) → "Before 23 July 2026".
export const occurred = (i: any) => {
  const d = new Date(`${i.date}T00:00:00Z`);
  if (i.date_precision === "month") return d.toLocaleString("en-US", { month: "long", year: "numeric", timeZone: "UTC" });
  if (i.date_precision === "before") return `Before ${d.toLocaleString("en-GB", { day: "numeric", month: "long", year: "numeric", timeZone: "UTC" })}`;
  return i.date;
};

// Reports dated after the newest one in this view. Compares dates: incidents sort by (date, id),
// so a same-day hidden report sits later in the list without being newer.
export const newerThanLatest = (all: any[], counted: any[]) =>
  counted.length ? all.filter((i) => i.date > counted.at(-1).date).length : all.length;

export const isLow = (i: any) => i.confidence === "low";

// Whole days since a date, floored at 0 for a date later today elsewhere in the world.
export const daysSince = (date: string, now: number) => Math.max(0, Math.floor((now - Date.parse(date)) / 86_400_000));

export const clip = (text: string, max: number) => (text.length <= max ? text : `${text.slice(0, max - 1).trimEnd()}…`);

const modelLabel = (model: any) => (model.name.startsWith(model.org) ? model.name : `${model.org} ${model.name}`);
export const modelTitle = (model: any) => `${modelLabel(model)} rap sheet`;

// Titles identify the case, and the summary goes in the description: a full summary gets cut off in search results.
export const incidentTitle = (i: any) => {
  const title = clip(`${i.org} / ${i.models.map((m: any) => m.name).join(", ")}: Case FB-${i.id}`, 120);
  return isLow(i) ? `Low-confidence report: ${title}` : title;
};
export const incidentDescription = (i: any) => clip(isLow(i) ? `Low-confidence report: ${i.summary}` : i.summary, 155);

// The score to show in each confidence view. One entry, with no key, when both views agree;
// two when a hidden low-confidence prior changes this incident's score.
export const scoreViews = (i: any, confidentScores: Record<string, any>) => {
  const all = { breakdown: i.breakdown, badges: i.badges };
  const confident = confidentScores[i.id];
  if (!confident || JSON.stringify(confident) === JSON.stringify(all)) return [{ key: undefined, ...all }];
  return [{ key: "confident", ...confident }, { key: "all", ...all }];
};
