import { defineConfig, type Plugin } from "vite";
import react from "@vitejs/plugin-react";

// Las vistas previas (LinkedIn, WhatsApp) exigen URL absoluta en og:image.
// Netlify define URL con el dominio principal del sitio, así que al conectar un dominio propio se actualiza solo.
function siteUrl(): Plugin {
  const raw = process.env.URL || process.env.VITE_SITE_URL || "";
  const base = raw ? raw.replace(/\/+$/, "") + "/" : "";
  return {
    name: "site-url",
    transformIndexHtml: (html) => html.replaceAll("__SITE_URL__", base),
  };
}

export default defineConfig({
  plugins: [react(), siteUrl()],
  base: "./",
});
