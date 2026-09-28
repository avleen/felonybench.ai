export interface Point { date: string; cumulative: number; delta: number; incident_id: string }

export const W = 960, H = 420;
export const PAD = { top: 16, right: 160, bottom: 32, left: 56 };

// Minimum vertical gap between two end-of-line labels before we nudge them apart.
const LABEL_GAP = 16;

const day = (d: string) => Date.parse(d) / 86_400_000;

export interface Series {
  org: string;
  points: Point[];
  final: number;
  color: string;
  path: string;
  markers: (Point & { cx: number; cy: number })[];
  /** Where the line actually ends, before any collision nudge. */
  labelAnchorY: number;
  /** Where the label is drawn, after nudging apart from neighbors. */
  labelY: number;
}

export interface Layout {
  orgs: Series[];
  yTicks: { value: number; y: number }[];
  xTicks: { label: string; x: number }[];
  labelX: number;
}

/** Push overlapping labels apart, top to bottom, by the smallest amount that clears them. */
function resolveLabelCollisions(orgs: { labelAnchorY: number }[]): number[] {
  const order = orgs.map((_, i) => i).sort((a, b) => orgs[a].labelAnchorY - orgs[b].labelAnchorY);
  const y: number[] = orgs.map((s) => s.labelAnchorY);
  for (let k = 1; k < order.length; k++) {
    const i = order[k], prev = order[k - 1];
    if (y[i] - y[prev] < LABEL_GAP) y[i] = y[prev] + LABEL_GAP;
  }
  return y;
}

export function layout(series: Record<string, Point[]>, today: string): Layout | null {
  const all = Object.values(series).flat();
  if (all.length === 0) return null;
  const x0 = Math.min(...all.map((p) => day(p.date))) - 14;
  const x1 = day(today);
  const yMax = Math.max(...all.map((p) => p.cumulative)) * 1.1;
  const x = (d: string) => PAD.left + ((day(d) - x0) / (x1 - x0)) * (W - PAD.left - PAD.right);
  const y = (v: number) => H - PAD.bottom - (v / yMax) * (H - PAD.top - PAD.bottom);

  const orgs = Object.entries(series)
    .map(([org, points]) => ({ org, points, final: points[points.length - 1].cumulative }))
    .sort((a, b) => b.final - a.final)
    .map((s, i) => {
      let d = `M${x(s.points[0].date)},${y(0)}`;
      for (const p of s.points) d += ` H${x(p.date)} V${y(p.cumulative)}`;
      d += ` H${x(today)}`;
      const labelAnchorY = y(s.final);
      return {
        ...s,
        color: `var(--series-${(i % 8) + 1})`,
        path: d,
        markers: s.points.map((p) => ({ ...p, cx: x(p.date), cy: y(p.cumulative) })),
        labelAnchorY,
        labelY: labelAnchorY,
      };
    });

  const nudged = resolveLabelCollisions(orgs);
  orgs.forEach((s, i) => (s.labelY = nudged[i]));

  const yTicks = [0, 0.25, 0.5, 0.75, 1].map((f) => ({ value: Math.round(yMax * f), y: y(yMax * f) }));
  const xTicks: { label: string; x: number }[] = [];
  const start = new Date((x0 + 14) * 86_400_000);
  for (let d = new Date(Date.UTC(start.getUTCFullYear(), start.getUTCMonth(), 1)); day(d.toISOString().slice(0, 10)) <= x1; d.setUTCMonth(d.getUTCMonth() + 1)) {
    const iso = d.toISOString().slice(0, 10);
    if (day(iso) >= x0) xTicks.push({ label: d.toLocaleString("en-US", { month: "short", year: "2-digit", timeZone: "UTC" }), x: x(iso) });
  }
  return { orgs, yTicks, xTicks, labelX: x(today) + 12 };
}
