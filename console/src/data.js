import { useEffect, useState } from "react";

// All data comes from JSON built by site/build_data.py from the files in results/.
// Nothing numeric is written into the components.
const BASE = import.meta.env.BASE_URL;
const cache = new Map();

export function fetchJSON(name) {
  if (!cache.has(name)) {
    cache.set(name, fetch(`${BASE}data/${name}`).then((r) => {
      if (!r.ok) throw new Error(`${name}: HTTP ${r.status}`);
      return r.json();
    }));
  }
  return cache.get(name);
}

export function useData(name) {
  const [state, setState] = useState({ data: null, error: null });
  useEffect(() => {
    let live = true;
    fetchJSON(name).then(
      (data) => live && setState({ data, error: null }),
      (error) => live && setState({ data: null, error }),
    );
    return () => { live = false; };
  }, [name]);
  return state;
}

export const SITE = "/cerop-console/";
export const REPO = "https://github.com/arthunya/cerop-console";
export const NB = (file) => `${REPO}/blob/main/notebooks/${file}`;

export const pct = (v, d = 1) => `${(v * 100).toFixed(d)}%`;
export const f3 = (v) => v.toFixed(3);
export const int = (v) => Math.round(v).toLocaleString("en-US");
export const pts = (v) => {
  const p = v * 100;
  const s = Math.abs(p) < 0.05 ? "0.0" : p.toFixed(1);
  return (p > 0.049 ? "+" : p < -0.049 ? "−" : "") + s.replace("-", "");
};

export function bandFor(p, thr) {
  if (p >= thr) return "High";
  if (p >= thr / 2) return "Watch";
  return "Clear";
}

export const CELL_TEXT = {
  TP: "Flagged, and it really happened",
  FN: "Missed: not flagged, but it happened",
  FP: "False alarm: flagged, didn't happen",
  TN: "Not flagged, and it didn't happen",
};
