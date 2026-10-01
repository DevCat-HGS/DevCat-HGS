import { useEffect, useMemo, useRef, useState, type CSSProperties, type ImgHTMLAttributes } from "react";
import { copy, type Locale } from "./content";

const SECTION_IDS = ["intro", "practice", "startup", "tenure", "selected", "credentials", "stack", "close"] as const;

function sectionProgress(el: HTMLElement | null) {
  if (!el) return 0;
  const total = el.offsetHeight - window.innerHeight;
  if (total <= 0) return 0;
  const passed = Math.min(Math.max(-el.getBoundingClientRect().top, 0), total);
  return passed / total;
}

/** Drives --p (progress bar, aurora) and --intro (hero) only on the elements that read them. */
function useScrollScene() {
  useEffect(() => {
    const root = document.documentElement;
    const intro = document.getElementById("intro");
    const bar = document.querySelector<HTMLElement>(".progress");
    const aurora = document.querySelector<HTMLElement>(".aurora");
    let frame = 0;

    const update = () => {
      frame = 0;
      const max = root.scrollHeight - window.innerHeight;
      const p = (max > 0 ? window.scrollY / max : 0).toFixed(4);
      bar?.style.setProperty("--p", p);
      aurora?.style.setProperty("--p", p);
      intro?.style.setProperty("--intro", sectionProgress(intro).toFixed(4));
    };

    const schedule = () => {
      if (!frame) frame = requestAnimationFrame(update);
    };

    update();
    window.addEventListener("scroll", schedule, { passive: true });
    window.addEventListener("resize", schedule);
    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener("scroll", schedule);
      window.removeEventListener("resize", schedule);
    };
  }, []);
}

function useActiveSection() {
  const [id, setId] = useState<string>("intro");

  useEffect(() => {
    const nodes = SECTION_IDS.map((key) => document.getElementById(key)).filter(
      (n): n is HTMLElement => Boolean(n),
    );
    const io = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((e) => e.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
        if (visible?.target.id) setId(visible.target.id);
      },
      { rootMargin: "-28% 0px -45% 0px", threshold: [0.1, 0.25, 0.5] },
    );
    nodes.forEach((n) => io.observe(n));
    return () => io.disconnect();
  }, []);

  return id;
}

function useReveal(locale: string) {
  useEffect(() => {
    const nodes = document.querySelectorAll<HTMLElement>("[data-reveal]:not(.is-in)");
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (!e.isIntersecting) return;
          e.target.classList.add("is-in");
          io.unobserve(e.target);
        });
      },
      { rootMargin: "0px 0px -10% 0px", threshold: 0 },
    );
    nodes.forEach((n) => io.observe(n));
    return () => io.disconnect();
  }, [locale]);
}

function useSpotlight() {
  useEffect(() => {
    const onMove = (e: PointerEvent) => {
      if (!(e.target instanceof Element)) return;
      const el = e.target.closest<HTMLElement>(".card, .project");
      if (!el) return;
      const r = el.getBoundingClientRect();
      el.style.setProperty("--mx", `${e.clientX - r.left}px`);
      el.style.setProperty("--my", `${e.clientY - r.top}px`);
    };
    document.addEventListener("pointermove", onMove, { passive: true });
    return () => document.removeEventListener("pointermove", onMove);
  }, []);
}

const ICONS = {
  GitHub:
    "M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12",
  LinkedIn:
    "M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z",
} as const;

function Socials({
  links,
  cv,
}: {
  links: readonly { label: string; href: string }[];
  cv: { label: string; href: string };
}) {
  return (
    <div className="socials">
      <a className="social-btn primary" href={cv.href} download>
        <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 3v12m0 0l-4-4m4 4l4-4M5 21h14" />
        </svg>
        {cv.label}
      </a>
      {links
        .filter((l): l is { label: keyof typeof ICONS; href: string } => l.label in ICONS)
        .map((l) => (
          <a key={l.label} className="social-btn" href={l.href} target="_blank" rel="noreferrer">
            <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" fill="currentColor">
              <path d={ICONS[l.label]} />
            </svg>
            {l.label}
          </a>
        ))}
    </div>
  );
}

/** Imagen que aparece con fundido al terminar de cargar (sobre un fondo con brillo mientras tanto). */
function Img({ className = "", ...props }: ImgHTMLAttributes<HTMLImageElement>) {
  const ref = useRef<HTMLImageElement>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (ref.current?.complete) setReady(true);
  }, []);

  return (
    <img
      ref={ref}
      className={`${className} fade${ready ? " is-loaded" : ""}`.trim()}
      decoding="async"
      onLoad={() => setReady(true)}
      {...props}
    />
  );
}

type CredItem = { img: string; title: string; meta: string };

function Lightbox({ item, close, label }: { item: CredItem; close: () => void; label: string }) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && close();
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [close]);

  return (
    <div className="lightbox" role="dialog" aria-modal="true" aria-label={item.title} onClick={close}>
      <figure onClick={(e) => e.stopPropagation()}>
        <Img src={`credentials/${item.img}.webp`} alt={item.title} />
        <figcaption>
          <strong>{item.title}</strong>
          <span>{item.meta}</span>
        </figcaption>
      </figure>
      <button type="button" className="lightbox-close" onClick={close} autoFocus>
        {label}
      </button>
    </div>
  );
}

function initialLocale(): Locale {
  try {
    const saved = localStorage.getItem("locale");
    if (saved === "en" || saved === "es") return saved;
  } catch {
    /* localStorage no disponible: se usa el idioma del navegador */
  }
  return (navigator.languages?.[0] ?? navigator.language ?? "en").toLowerCase().startsWith("es") ? "es" : "en";
}

const stagger = (i: number) => ({ ["--i" as string]: i }) as CSSProperties;

export default function App() {
  const [locale, setLocale] = useState<Locale>(initialLocale);
  const t = useMemo(() => copy[locale], [locale]);
  const [open, setOpen] = useState<CredItem | null>(null);
  const active = useActiveSection();
  useScrollScene();
  useReveal(locale);
  useSpotlight();

  useEffect(() => {
    const splash = document.getElementById("splash");
    if (!splash) return;
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const minShow = reduced ? 250 : 1500;
    const wait = new Promise((r) => window.setTimeout(r, Math.max(0, minShow - performance.now())));
    Promise.all([document.fonts.ready, wait]).then(() => {
      splash.classList.add("hide");
      document.documentElement.classList.remove("is-loading");
      window.setTimeout(() => splash.remove(), 800);
    });
  }, []);

  useEffect(() => {
    document.documentElement.lang = locale;
    document.title =
      locale === "es"
        ? "Harol G. Salgado — Software Engineer"
        : "Harol G. Salgado — Software Engineer";
  }, [locale]);

  return (
    <>
      <a className="skip" href="#intro">
        {t.skip}
      </a>
      <div className="aurora" aria-hidden="true">
        <span className="a1" />
        <span className="a2" />
        <span className="a3" />
      </div>
      <div className="grain" aria-hidden="true" />
      <div className="progress" />

      <header className="nav">
        <a className="wordmark" href="#intro">
          {t.wordmark}
        </a>
        <nav className="nav-index" aria-label="Chapters">
          {t.chapters.map((c) => (
            <a key={c.id} href={`#${c.id}`} className={active === c.id ? "is-active" : ""}>
              {c.n} {c.label}
            </a>
          ))}
        </nav>
        <button
          className="lang"
          type="button"
          onClick={() => {
            const next = locale === "en" ? "es" : "en";
            setLocale(next);
            try {
              localStorage.setItem("locale", next);
            } catch {
              /* sin persistencia */
            }
          }}
          aria-label={locale === "en" ? "Cambiar a español" : "Switch to English"}
        >
          {t.langLabel}
        </button>
      </header>

      <nav className="rail" aria-label="Index">
        {t.chapters.map((c) => (
          <a key={c.id} href={`#${c.id}`} className={active === c.id ? "is-active" : ""}>
            {c.n}
          </a>
        ))}
      </nav>

      <section className="hero" id="intro">
        <div className="hero-sticky">
          <div className="hero-inner">
            <p className="kicker">
              {t.issue}
              <span style={{ color: "var(--accent)" }}>  /  </span>
              {t.heroKicker}
            </p>
            <h1 className="display">
              <span>{t.heroName[0]}</span>
              <span className="line-2">{t.heroName[1]}</span>
            </h1>
            <p className="lede">{t.heroDek}</p>
            <div className="hero-actions">
              <a className="now" href="#startup">
                <i aria-hidden="true" />
                {t.heroNow}
              </a>
              <span className="open">
                <i aria-hidden="true" />
                {t.heroOpen}
              </span>
              <Socials links={t.links} cv={t.cv} />
            </div>
            <div className="hero-foot">
              <div className="meta">
                {t.heroMeta.map((m) => (
                  <span className="chip" key={m}>
                    {m}
                  </span>
                ))}
              </div>
              <span className="scroll-cue">{t.scroll}</span>
            </div>
          </div>
        </div>
      </section>

      <section className="section" id="practice">
        <div className="wrap">
          <div className="section-head" data-reveal>
            <p className="eyebrow">{t.practiceEyebrow}</p>
            <div className="practice-grid">
              <h2 className="display">{t.practiceTitle}</h2>
              <p className="aside">{t.practiceAside}</p>
            </div>
            <p className="lede">{t.practiceBody}</p>
          </div>
          <div className="bento" data-reveal="stagger">
            {t.bento.map((item, idx) => (
              <article className="card" key={item.k} style={stagger(idx)}>
                <span className="k">{item.k}</span>
                <p className="v">{item.v}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="section" id="startup">
        <div className="wrap">
          <div className="section-head" data-reveal>
            <p className="eyebrow">{t.startupEyebrow}</p>
            <div className="startup-top">
              <img className="app-icon" src="migozz-icon.webp" alt="" width={72} height={72} />
              <h2 className="display">{t.startupCompany}</h2>
              <span className="status">
                <i aria-hidden="true" />
                {t.startupStatus}
              </span>
            </div>
            <p className="role">
              {t.startupRole}
              <br />
              {t.startupPeriod}
            </p>
            <p className="lede">{t.startupBody}</p>
            <div className="stores">
              <a href={t.startupLinks.play} target="_blank" rel="noreferrer" aria-label="Google Play">
                <img src="play.png" alt="Google Play" height={48} />
              </a>
              <a href={t.startupLinks.apple} target="_blank" rel="noreferrer" aria-label="App Store">
                <img src="appstore.svg" alt="App Store" height={40} />
              </a>
              <a className="web-link" href={t.startupLinks.web} target="_blank" rel="noreferrer">
                {t.startupWeb} ↗
              </a>
            </div>
          </div>
          <div className="duties" data-reveal="stagger">
            {t.startupDuties.map((d, idx) => (
              <article className="card" key={d.n} style={stagger(idx)}>
                <span className="k">
                  {d.n}  ·  {d.k}
                </span>
                <p className="v">{d.v}</p>
              </article>
            ))}
          </div>
          <div className="tags startup-stack">
            {t.startupStack.map((s) => (
              <span key={s}>{s}</span>
            ))}
          </div>
        </div>
      </section>

      <section className="tenure" id="tenure">
        <div className="wrap tenure-sticky">
          <div>
            <p className="eyebrow">{t.tenureEyebrow}</p>
            <span className="status past">{t.tenureStatus}</span>
            <h2 className="display company">{t.tenureCompany}</h2>
            <p className="role">
              {t.tenureRole}
              <br />
              {t.tenurePlace}
            </p>
          </div>
          <div className="beats">
            {t.tenureBeats.map((b) => (
              <article className="beat" key={b.n}>
                <span className="n">{b.n}</span>
                <div>
                  <h3>{b.title}</h3>
                  <p>{b.body}</p>
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="section" id="selected">
        <div className="wrap">
          <div className="section-head" data-reveal>
            <p className="eyebrow">{t.selectedEyebrow}</p>
            <h2 className="display">{t.selectedTitle}</h2>
            <p className="lede">{t.selectedLead}</p>
          </div>
          <div className="work" data-reveal="stagger">
            {t.projects.map((p, idx) => {
              const inner = (
                <>
                  {"shot" in p && p.shot ? (
                    <figure className="media">
                      <div className="chrome" aria-hidden="true">
                        <i />
                        <i />
                        <i />
                        <span>{"href" in p && p.href ? new URL(p.href).host : p.title}</span>
                      </div>
                      <Img
                        src={p.shot}
                        srcSet={`${p.shot.replace(".webp", "-480.webp")} 480w, ${p.shot} 960w`}
                        sizes="(max-width: 760px) 92vw, 560px"
                        alt={"alt" in p ? p.alt : ""}
                        width={960}
                        height={600}
                        loading="lazy"
                      />
                    </figure>
                  ) : (
                    <div
                      className="media art"
                      aria-hidden="true"
                      style={{ ["--h" as string]: "hue" in p ? p.hue : 260 } as CSSProperties}
                    >
                      {"logo" in p && p.logo ? (
                        <img
                          className="logo"
                          src={p.logo}
                          alt=""
                          loading="lazy"
                          decoding="async"
                        />
                      ) : (
                        <span>{p.title.replace(/[^A-Za-z]/g, "").slice(0, 2)}</span>
                      )}
                    </div>
                  )}
                  <div>
                    <div className="project-top">
                      <span className="tag">{p.tag}</span>
                      <span className="idx">{String(idx + 1).padStart(2, "0")}</span>
                    </div>
                    <h3>{p.title}</h3>
                    <p className="dek">{p.dek}</p>
                  </div>
                  <div>
                    {"client" in p && p.client ? (
                      <p className="client">
                        <span>{"institutional" in p && p.institutional ? t.institutionalLabel : t.clientLabel}</span>
                        {"clientHref" in p && p.clientHref && !("href" in p) ? (
                          <a href={p.clientHref} target="_blank" rel="noreferrer">
                            {p.client} ↗
                          </a>
                        ) : (
                          p.client
                        )}
                      </p>
                    ) : null}
                    <div className="tags">
                      {p.stack.map((s) => (
                        <span key={s}>{s}</span>
                      ))}
                    </div>
                    {"href" in p && p.href ? <div className="visit">{t.visit} →</div> : null}
                  </div>
                </>
              );

              if ("href" in p && p.href) {
                return (
                  <a
                    className="project"
                    key={p.id}
                    href={p.href}
                    target="_blank"
                    rel="noreferrer"
                    style={stagger(idx)}
                  >
                    {inner}
                  </a>
                );
              }

              return (
                <article className="project" key={p.id} style={stagger(idx)}>
                  {inner}
                </article>
              );
            })}
          </div>
          <p className="legal">{t.trademarkNote}</p>
        </div>
      </section>

      <section className="section" id="credentials">
        <div className="wrap">
          <div className="section-head" data-reveal>
            <p className="eyebrow">{t.credEyebrow}</p>
            <h2 className="display">{t.credTitle}</h2>
            <p className="lede">{t.credLead}</p>
          </div>
          {t.credGroups.map((g, gi) => (
            <div className="cred-group" key={gi}>
              <h3 className="cred-k">{g.k}</h3>
              {"compact" in g && g.compact ? (
                <ul className="cred-list" data-reveal>
                  {g.items.map((it) => (
                    <li key={it.img}>
                      <span className="cred-list-title">{it.title}</span>
                      <span className="cred-meta">{it.meta}</span>
                      <button
                        type="button"
                        className="cred-view"
                        onClick={() => setOpen(it)}
                        aria-label={`${t.credView}: ${it.title}`}
                      >
                        {t.credViewShort}
                      </button>
                    </li>
                  ))}
                </ul>
              ) : (
                <div className="cred-grid" data-reveal="stagger">
                  {g.items.map((it, idx) => (
                    <button
                      type="button"
                      className="cred"
                      key={it.img}
                      style={stagger(idx)}
                      onClick={() => setOpen(it)}
                      aria-label={`${t.credView}: ${it.title}`}
                    >
                      <span className="cred-img">
                        <Img
                          src={`credentials/thumb/${it.img}.webp`}
                          srcSet={`credentials/thumb/${it.img}-360.webp 360w, credentials/thumb/${it.img}.webp 560w`}
                          sizes="(max-width: 760px) 92vw, 380px"
                          alt=""
                          width={560}
                          height={420}
                          loading="lazy"
                        />
                      </span>
                      <span className="cred-title">{it.title}</span>
                      <span className="cred-meta">{it.meta}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </section>

      <section className="section" id="stack">
        <div className="wrap">
          <div className="section-head" data-reveal>
            <p className="eyebrow">{t.stackEyebrow}</p>
            <h2 className="display">{t.stackTitle}</h2>
          </div>
          <dl className="stack-list" data-reveal="stagger">
            {t.stackGroups.map((g, idx) => (
              <div className="stack-row" key={g.k} style={stagger(idx)}>
                <dt>{g.k}</dt>
                <dd>{g.v}</dd>
              </div>
            ))}
          </dl>
        </div>
      </section>

      <section className="section close" id="close">
        <div className="wrap" data-reveal>
          <p className="eyebrow">{t.closeEyebrow}</p>
          <h2 className="display">{t.closeTitle}</h2>
          <p className="lede">{t.closeBody}</p>
          <a className="mail" href={`mailto:${t.email}`}>
            {t.email}
          </a>
          <Socials links={t.links} cv={t.cv} />
          <div className="outlinks">
            {t.links
              .filter((l) => l.label !== "GitHub" && l.label !== "LinkedIn")
              .map((l) => (
              <a key={l.href} href={l.href} target="_blank" rel="noreferrer">
                {l.label}
              </a>
            ))}
          </div>
        </div>
      </section>

      {open ? <Lightbox item={open} close={() => setOpen(null)} label={t.credClose} /> : null}

      <footer className="footer">
        <div className="wrap">{t.footer}</div>
      </footer>
    </>
  );
}
