import fs from "node:fs/promises";
import path from "node:path";
import satori from "satori";
import { Resvg } from "@resvg/resvg-js";
import scores, { fmt } from "../../lib/data";

export function getStaticPaths() {
  const models = new Map();
  for (const league of ["open", "sandbox"]) {
    for (const m of scores.boards[league].all.models) if (!models.has(m.slug)) models.set(m.slug, m);
  }
  return [
    { params: { slug: "default" }, props: { model: null } },
    ...[...models.values()].map((model: any) => ({ params: { slug: model.slug }, props: { model } })),
  ];
}

// Satori requires an explicit display on any box with more than one child; default every box to flex.
const el = (type: string, style: object, children: any) => ({ type, props: { style: { display: "flex", ...style }, children } });

export async function GET({ props }: { props: { model: any } }) {
  const font = await fs.readFile(path.join(process.cwd(), "src/assets/fonts/IBMPlexMono-Bold.ttf"));
  const m = props.model;
  // The mark, drawn with boxes: four rising bars crossed by a red bar.
  const bar = (left: number, top: number) =>
    el("div", { position: "absolute", left, top, width: 14, height: 104 - top, background: "#151412", borderRadius: 2 }, []);
  const mark = el("div", { display: "flex", position: "relative", width: 128, height: 128, borderRadius: 24, background: "#ece8df" }, [
    bar(24, 76), bar(46, 60), bar(68, 44), bar(90, 24),
    el("div", { position: "absolute", left: 16, top: 80, width: 96, height: 10, background: "#ff6b5e", borderRadius: 2 }, []),
  ]);
  const lines = m
    ? [el("div", { fontSize: 28, opacity: 0.7 }, m.org), el("div", { fontSize: 72 }, m.name),
       el("div", { fontSize: 36, color: "#ff6b5e" }, `#${m.rank} · ${fmt(m.score)} FBS · ${m.incidents.length} incident(s)`)]
    : [el("div", { fontSize: 80, letterSpacing: 2 }, "FELONYBENCH.ai"),
       el("div", { fontSize: 34, color: "#ff6b5e" }, "The leading benchmark for AI crime. Higher is better.")];
  const svg = await satori(
    el("div", { width: 1200, height: 630, display: "flex", flexDirection: "column", justifyContent: "center",
      padding: 72, gap: 16, background: "#151412", color: "#ece8df", fontFamily: "Plex Mono" },
      [el("div", { display: "flex", marginBottom: 24 }, [mark]), ...lines]),
    { width: 1200, height: 630, fonts: [{ name: "Plex Mono", data: font, weight: 700, style: "normal" }] },
  );
  const png = new Resvg(svg).render().asPng();
  return new Response(png, { headers: { "Content-Type": "image/png" } });
}
