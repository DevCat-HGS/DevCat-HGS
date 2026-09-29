import { useEffect, useMemo, useState, type CSSProperties } from "react";
import { copy, type Locale } from "./content";

const SECTION_IDS = ["intro", "practice", "tenure", "selected", "stack", "close"] as const;

function sectionProgress(el: HTMLElement | null) {
  if (!el) return 0;
  const total = el.offsetHeight - window.innerHeight;
  if (total <= 0) return 0;
  const passed = Math.min(Math.max(-el.getBoundingClientRect().top, 0), total);
  return passed / total;
}

/** Drives --p and --intro on :root; only the tenure beat index goes through React state. */
function useScrollScene() {
  const [beat, setBeat] = useState(0);

  useEffect(() => {
    const root = document.documentElement;
    const intro = document.getElementById("intro");
    const tenure = document.getElementById("tenure");
    let frame = 0;

    const update = () => {
      frame = 0;
      const max = root.scrollHeight - window.innerHeight;
      root.style.setProperty("--p", (max > 0 ? window.scrollY / max : 0).toFixed(4));
      root.style.setProperty("--intro", sectionProgress(intro).toFixed(4));
      const t = sectionProgress(tenure);
      setBeat(t < 0.33 ? 0 : t < 0.66 ? 1 : 2);
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

  return beat;
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

function useReveal() {
  useEffect(() => {
    const nodes = document.querySelectorAll<HTMLElement>("[data-reveal]");
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
  }, []);
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

const stagger = (i: number) => ({ ["--i" as string]: i }) as CSSProperties;

export default function App() {
  const [locale, setLocale] = useState<Locale>("en");
  const t = useMemo(() => copy[locale], [locale]);
  const active = useActiveSection();
  const beat = useScrollScene();
  useReveal();
  useSpotlight();

  useEffect(() => {
    document.documentElement.lang = locale;
    document.title =
      locale === "es"
        ? "Harold G. Salgado — Software Engineer"
        : "Harold G. Salgado — Software Engineer";
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
          onClick={() => setLocale(locale === "en" ? "es" : "en")}
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

      <section className="tenure" id="tenure">
        <div className="wrap tenure-sticky">
          <div>
            <p className="eyebrow">{t.tenureEyebrow}</p>
            <h2 className="display company">{t.tenureCompany}</h2>
            <p className="role">
              {t.tenureRole}
              <br />
              {t.tenurePlace}
            </p>
          </div>
          <div className="beats">
            {t.tenureBeats.map((b, idx) => (
              <article className={idx === beat ? "beat is-on" : "beat"} key={b.n}>
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
                  <div>
                    <span className="tag">{p.tag}</span>
                    <h3>{p.title}</h3>
                    <p className="dek">{p.dek}</p>
                  </div>
                  <div>
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
                    className={`project ${p.size}`}
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
                <article className={`project ${p.size}`} key={p.id} style={stagger(idx)}>
                  {inner}
                </article>
              );
            })}
          </div>
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
          <div className="outlinks">
            {t.links.map((l) => (
              <a key={l.href} href={l.href} target="_blank" rel="noreferrer">
                {l.label}
              </a>
            ))}
          </div>
        </div>
      </section>

      <footer className="footer">
        <div className="wrap">{t.footer}</div>
      </footer>
    </>
  );
}
