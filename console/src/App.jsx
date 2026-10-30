import { useCallback, useEffect, useState } from "react";
import { Icon, GitHubIcon } from "./components/ui.jsx";
import { SITE, REPO } from "./data.js";
import Intro from "./tabs/Intro.jsx";
import Overview from "./tabs/Overview.jsx";
import Supplier from "./tabs/Supplier.jsx";
import Shipment from "./tabs/Shipment.jsx";
import HowBuilt from "./tabs/HowBuilt.jsx";
import Limits from "./tabs/Limits.jsx";

const TABS = [
  { id: "overview", label: "Overview", short: "Overview", icon: "overview", C: Overview },
  { id: "supplier", label: "Supplier risk", short: "Supplier", icon: "supplier", C: Supplier },
  { id: "shipment", label: "Shipment delay", short: "Shipment", icon: "shipment", C: Shipment },
  { id: "built", label: "How it was built", short: "Method", icon: "built", C: HowBuilt },
  { id: "limits", label: "Limits", short: "Limits", icon: "limits", C: Limits },
];

const store = {
  get(k) { try { return localStorage.getItem(k); } catch { return null; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch { /* storage unavailable: fine */ } },
};

function initialTab() {
  const h = window.location.hash.replace("#", "");
  return TABS.some((t) => t.id === h) ? h : "overview";
}

export default function App() {
  const [tab, setTab] = useState(initialTab);
  const [intro, setIntro] = useState(() => new URLSearchParams(window.location.search).get("intro") !== "0" && store.get("cerop-intro-done") !== "1");
  const [theme, setTheme] = useState(() => document.documentElement.getAttribute("data-theme"));

  const go = useCallback((id) => {
    setTab(id);
    history.replaceState(null, "", `#${id}`);
    window.scrollTo({ top: 0 });
  }, []);
  useEffect(() => {
    const onHash = () => setTab(initialTab());
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  const isDark = theme === "dark" || (!theme && window.matchMedia("(prefers-color-scheme: dark)").matches);
  const toggleTheme = () => {
    const next = isDark ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    store.set("cerop-theme", next);
    setTheme(next);
  };
  const closeIntro = useCallback(() => { setIntro(false); store.set("cerop-intro-done", "1"); }, []);

  const Current = TABS.find((t) => t.id === tab).C;
  const tabButtons = (cls) => TABS.map((t) => (
    <button key={t.id} role="tab" aria-selected={tab === t.id} aria-controls="panel" onClick={() => go(t.id)}>
      <Icon name={t.icon} />{cls === "short" ? t.short : t.label}
    </button>
  ));

  return (
    <>
      <a href="#panel" className="sr-only">Skip to content</a>
      <header className="topbar">
        <a className="brand" href={SITE} aria-label="CEROP project home">
          <img src={`${import.meta.env.BASE_URL}favicon.svg`} alt="" />
          <b>CEROP</b><span className="hide-sm">Risk Console</span>
        </a>
        <div className="spacer" />
        <a className="iconbtn" href={SITE}><Icon name="back" /><span>Project</span></a>
        <button className="iconbtn" onClick={() => setIntro(true)} aria-label="Show the introduction"><Icon name="help" /></button>
        <button className="iconbtn" onClick={toggleTheme} aria-label={`Switch to ${isDark ? "light" : "dark"} mode`}><Icon name={isDark ? "sun" : "moon"} /></button>
        <a className="iconbtn" href={REPO} aria-label="Source code on GitHub"><GitHubIcon /></a>
      </header>
      <div className="layout">
        <nav className="tabs" role="tablist" aria-label="Console sections">{tabButtons("long")}</nav>
        <main id="panel" role="tabpanel" tabIndex={-1}>
          <Current go={go} />
        </main>
      </div>
      <nav className="tabselect" role="tablist" aria-label="Console sections">{tabButtons("short")}</nav>
      <footer className="foot">
        <p>Research prototype from AIT 506 Machine Learning (Westcliff University), built on public datasets. Not for real credit or logistics decisions.</p>
        <p>Team: Arthunya Kanoklertwongse, Ankit Kumar, Divya Gopal, Aswin Shriram Thiagarajan · <a href={`${REPO}/blob/main/LICENSE`}>MIT license</a></p>
      </footer>
      {intro && <Intro onClose={closeIntro} />}
    </>
  );
}
