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

// Whole words, so "Metamorph" from Meta keeps its lab.
const namesLab = (model: any) => model.name === model.org || model.name.startsWith(`${model.org} `) || model.name.startsWith(`${model.org}-`);
const modelLabel = (model: any) => (namesLab(model) ? model.name : `${model.org} ${model.name}`);
export const modelTitle = (model: any) => `${modelLabel(model)} rap sheet`;

// Titles identify the case, and the summary goes in the description: a full summary gets cut off in search results.
export const incidentTitle = (i: any) => {
  const suffix = `: Case FB-${i.id}`;
  const title = clip(`${i.charged.join(", ")} / ${i.models.map((m: any) => m.name).join(", ")}`, Math.max(40, 120 - suffix.length)) + suffix;
  return isLow(i) ? `Low-confidence report: ${title}` : title;
};
export const incidentDescription = (i: any) => clip(isLow(i) ? `Low-confidence report: ${i.summary}` : i.summary, 155);

// Pages hidden by default, which search engines shouldn't list: low-confidence reports, and models with nothing else.
export const hiddenPaths = (incidents: any[]) => {
  const slugs = (list: any[]) => list.flatMap((i) => i.models.map((m: any) => m.slug));
  const visible = new Set(slugs(incidents.filter((i) => !isLow(i))));
  return [
    ...incidents.filter(isLow).map((i) => `/incident/${i.id}/`),
    ...[...new Set(slugs(incidents))].filter((slug) => !visible.has(slug)).map((slug) => `/model/${slug}/`),
  ];
};

// The score to show in each confidence view. One entry, with no key, when both views agree;
// two when a hidden low-confidence prior changes this incident's score.
export const scoreViews = (i: any, confidentScores: Record<string, any>) => {
  const all = { breakdown: i.breakdown, badges: i.badges };
  const confident = confidentScores[i.id];
  if (!confident || JSON.stringify(confident) === JSON.stringify(all)) return [{ key: undefined, ...all }];
  return [{ key: "confident", ...confident }, { key: "all", ...all }];
};
