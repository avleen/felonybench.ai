import { readFileSync } from "node:fs";
import { defineConfig } from "astro/config";
import sitemap from "@astrojs/sitemap";
import { hiddenPaths } from "./src/lib/incidents.ts";

const site = "https://felonybench.ai";
// `npm run data` writes this before dev and build.
const scores = JSON.parse(readFileSync(new URL("./src/data/scores.json", import.meta.url), "utf8"));
const hidden = new Set(hiddenPaths(scores.incidents).map((path) => site + path));

export default defineConfig({
  site,
  integrations: [sitemap({ filter: (page) => !hidden.has(page) })],
});
