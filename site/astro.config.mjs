import { defineConfig } from "astro/config";
import sitemap from "@astrojs/sitemap";

export default defineConfig({
  site: "https://felonybench.ai",
  integrations: [sitemap({ filter: (page) => !page.endsWith("/404/") })],
});
