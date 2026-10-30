import { int } from "../data.js";

export function Icon({ name }) {
  const p = {
    overview: <><rect x="3" y="3" width="7" height="9" rx="1.5" /><rect x="14" y="3" width="7" height="5" rx="1.5" /><rect x="14" y="12" width="7" height="9" rx="1.5" /><rect x="3" y="16" width="7" height="5" rx="1.5" /></>,
    supplier: <><path d="M3 21h18" /><path d="M5 21V8l7-4 7 4v13" /><path d="M9 21v-6h6v6" /></>,
    shipment: <><path d="M3 7h11v9H3z" /><path d="M14 10h4l3 3v3h-7" /><circle cx="7" cy="18" r="2" /><circle cx="17" cy="18" r="2" /></>,
    built: <><path d="M14.7 6.3a4 4 0 0 0-5.4 5.4L3 18l3 3 6.3-6.3a4 4 0 0 0 5.4-5.4l-2.5 2.5-2.4-.6-.6-2.4z" /></>,
    limits: <><circle cx="12" cy="12" r="9" /><path d="M12 8v5" /><path d="M12 16.5v.5" /></>,
    sun: <><circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" /></>,
    moon: <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z" />,
    back: <path d="M15 18l-6-6 6-6" />,
    help: <><circle cx="12" cy="12" r="9" /><path d="M9.5 9.5a2.5 2.5 0 1 1 3.5 2.3c-.6.3-1 .9-1 1.6v.6" /><path d="M12 17v.5" /></>,
    up: <path d="M12 19V5M5 12l7-7 7 7" />,
    check: <path d="M5 12l5 5 9-10" />,
    alert: <><path d="M12 3l9.5 17h-19z" /><path d="M12 10v4M12 17v.5" /></>,
  }[name];
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{p}</svg>
  );
}

export function GitHubIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 .5a11.5 11.5 0 0 0-3.6 22.4c.6.1.8-.3.8-.6v-2c-3.2.7-3.9-1.5-3.9-1.5-.5-1.3-1.3-1.7-1.3-1.7-1.1-.7.1-.7.1-.7 1.2.1 1.8 1.2 1.8 1.2 1 1.8 2.8 1.3 3.5 1 .1-.8.4-1.3.7-1.6-2.6-.3-5.3-1.3-5.3-5.7 0-1.3.5-2.3 1.2-3.1-.1-.3-.5-1.5.1-3.1 0 0 1-.3 3.3 1.2a11.4 11.4 0 0 1 6 0C17.3 4.4 18.3 4.7 18.3 4.7c.6 1.6.2 2.8.1 3.1.8.8 1.2 1.8 1.2 3.1 0 4.4-2.7 5.4-5.3 5.7.4.4.8 1.1.8 2.2v3.3c0 .3.2.7.8.6A11.5 11.5 0 0 0 12 .5z" /></svg>
  );
}

export function Band({ band }) {
  const icon = band === "High" ? "alert" : band === "Watch" ? "up" : "check";
  const text = band === "High" ? "High risk" : band === "Watch" ? "Watch" : "Clear";
  return <span className={`band ${band}`}><Icon name={icon} />{text}</span>;
}

export function Stat({ label, value, note }) {
  return (
    <div className="stat">
      <div className="label">{label}</div>
      <div className="value">{value}</div>
      {note && <div className="note">{note}</div>}
    </div>
  );
}

export function Source({ children }) {
  return <p className="source">Source: {children}</p>;
}

export function Skeleton({ h = 120 }) {
  return <div className="skel" style={{ height: h }} aria-hidden="true" />;
}

export function LoadError({ error }) {
  return <div className="callout" role="alert"><b>Couldn't load data.</b> {String(error?.message || error)}</div>;
}

// Rows: actual outcome. Columns: what the model said.
export function ConfusionMatrix({ tn, fp, fn, tp, pos = "Late", neg = "On time" }) {
  return (
    <div className="cm" role="table" aria-label="Confusion matrix">
      <div role="row" style={{ display: "contents" }}>
        <div className="h" role="columnheader"><span className="sr-only">Actual outcome</span></div>
        <div className="h" role="columnheader">Model said {neg.toLowerCase()}</div>
        <div className="h" role="columnheader">Model said {pos.toLowerCase()}</div>
      </div>
      <div role="row" style={{ display: "contents" }}>
        <div className="v" role="rowheader">Really {neg.toLowerCase()}</div>
        <div className="c" role="cell"><b>{int(tn)}</b><span>correctly left alone</span></div>
        <div className="c miss" role="cell"><b>{int(fp)}</b><span>false alarms</span></div>
      </div>
      <div role="row" style={{ display: "contents" }}>
        <div className="v" role="rowheader">Really {pos.toLowerCase()}</div>
        <div className="c miss" role="cell"><b>{int(fn)}</b><span>missed</span></div>
        <div className="c hit" role="cell"><b>{int(tp)}</b><span>caught</span></div>
      </div>
    </div>
  );
}

export function PageHead({ eyebrow, title, children }) {
  return (
    <header className="page-head">
      <div className="eyebrow">{eyebrow}</div>
      <h1>{title}</h1>
      {children && <p>{children}</p>}
    </header>
  );
}
