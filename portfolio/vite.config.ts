import { defineConfig, type Plugin } from "vite";
import react from "@vitejs/plugin-react";

const SITE_URL = (process.env.URL || process.env.VITE_SITE_URL || "").replace(/\/+$/, "");
const base = SITE_URL ? `${SITE_URL}/` : "";

const LINKEDIN = "https://www.linkedin.com/in/harold-salgado-498a60354/";
const GITHUB = "https://github.com/DevCat-HGS";

/** Datos estructurados (schema.org): le dicen a Google quién es la persona y dónde más aparece en la web. */
function structuredData() {
  const person = {
    "@type": "Person",
    "@id": `${base}#person`,
    name: "Harol Guerrero Salgado",
    givenName: "Harol",
    familyName: "Guerrero Salgado",
    alternateName: ["Harol G. Salgado", "Harol Salgado", "Harol Guerrero", "DevCat-HGS"],
    jobTitle: "Full Stack Software Developer",
    description:
      "Desarrollador de software Full Stack en Colombia. JavaScript, TypeScript, Python, React, Next.js, Node.js, Flutter y AWS.",
    sameAs: [LINKEDIN, GITHUB],
    knowsAbout: ["JavaScript", "TypeScript", "Python", "React", "Next.js", "Node.js", "Flutter", "AWS", "Firebase", "SAP Fiori"],
    knowsLanguage: ["es", "en"],
    worksFor: { "@type": "Organization", name: "MIGOZZ", url: "https://migozz.com" },
    alumniOf: { "@type": "EducationalOrganization", name: "SENA - Servicio Nacional de Aprendizaje" },
    ...(base ? { url: base, image: `${base}og.png` } : {}),
  };
  const graph: unknown[] = [person];
  if (base) {
    graph.push({
      "@type": "WebSite",
      "@id": `${base}#website`,
      url: base,
      name: "Harol Guerrero Salgado — Portafolio",
      inLanguage: ["es", "en"],
      publisher: { "@id": `${base}#person` },
    });
  }
  return JSON.stringify({ "@context": "https://schema.org", "@graph": graph });
}

// Netlify define URL con el dominio principal del sitio; al conectar un dominio propio todo se actualiza solo.
function seo(): Plugin {
  return {
    name: "seo",
    transformIndexHtml(html) {
      let out = html.replaceAll("__SITE_URL__", base).replace("__JSONLD__", () => structuredData());
      // Sin URL conocida no se emiten etiquetas que la exigen (canonical, og:url).
      if (!base) out = out.split("\n").filter((l) => !l.includes("data-needs-url")).join("\n");
      return out.replaceAll(" data-needs-url", "");
    },
    generateBundle() {
      this.emitFile({
        type: "asset",
        fileName: "robots.txt",
        source: `User-agent: *\nAllow: /\n${base ? `\nSitemap: ${base}sitemap.xml\n` : ""}`,
      });
      if (base) {
        this.emitFile({
          type: "asset",
          fileName: "sitemap.xml",
          source:
            `<?xml version="1.0" encoding="UTF-8"?>\n` +
            `<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n` +
            `  <url><loc>${base}</loc><changefreq>monthly</changefreq><priority>1.0</priority></url>\n` +
            `</urlset>\n`,
        });
      }
    },
  };
}

export default defineConfig({
  plugins: [react(), seo()],
  base: "./",
});
