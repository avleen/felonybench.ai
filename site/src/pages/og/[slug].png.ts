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

const el = (type: string, style: object, children: any) => ({ type, props: { style, children } });

export async function GET({ props }: { props: { model: any } }) {
  const font = await fs.readFile(path.join(process.cwd(), "src/assets/fonts/IBMPlexMono-Bold.ttf"));
  const m = props.model;
  const lines = m
    ? [el("div", { fontSize: 28, opacity: 0.7 }, m.org), el("div", { fontSize: 72 }, m.name),
       el("div", { fontSize: 36, color: "#ff6b5e" }, `#${m.rank} · ${fmt(m.score)} FBS · ${m.incidents.length} incident(s)`)]
    : [el("div", { fontSize: 72 }, "FELONYBENCH.ai"),
       el("div", { fontSize: 36, color: "#ff6b5e" }, "The leading benchmark for AI crime. Higher is better.")];
  const svg = await satori(
    el("div", { width: 1200, height: 630, display: "flex", flexDirection: "column", justifyContent: "center",
      padding: 72, gap: 16, background: "#151412", color: "#ece8df", fontFamily: "Plex Mono" }, lines),
    { width: 1200, height: 630, fonts: [{ name: "Plex Mono", data: font, weight: 700, style: "normal" }] },
  );
  const png = new Resvg(svg).render().asPng();
  return new Response(png, { headers: { "Content-Type": "image/png" } });
}
