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
