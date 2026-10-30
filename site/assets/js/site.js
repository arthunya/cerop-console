/* CEROP site: theme toggle, mobile menu, and small inline-SVG charts.
   Charts read the JSON in assets/data/ (built from results/ by site/build_data.py),
   so no chart value is written into the HTML. Each chart also gets a table view. */
(function () {
  "use strict";
  const doc = document.documentElement;
  const siteCss = document.querySelector('link[href$="assets/css/site.css"]');
  const ROOT = doc.dataset.root || (siteCss ? siteCss.getAttribute("href").replace("assets/css/site.css", "") : "");
  const store = {
    get: (k) => { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set: (k, v) => { try { localStorage.setItem(k, v); } catch (e) { /* storage blocked: ignore */ } },
  };

  // ---------- theme + menu ----------
  function isDark() {
    const t = doc.getAttribute("data-theme");
    return t ? t === "dark" : window.matchMedia("(prefers-color-scheme: dark)").matches;
  }
  document.querySelectorAll(".theme-toggle").forEach((b) => b.addEventListener("click", () => {
    const next = isDark() ? "light" : "dark";
    doc.setAttribute("data-theme", next);
    store.set("cerop-theme", next);
    document.querySelectorAll(".chart[data-chart]").forEach(draw);
  }));
  const menu = document.querySelector(".menu-btn");
  const nav = document.getElementById("nav");
  if (menu && nav) {
    menu.addEventListener("click", () => {
      const open = nav.classList.toggle("open");
      menu.setAttribute("aria-expanded", String(open));
    });
  }
  const here = location.pathname.split("/").filter(Boolean).slice(-2).join("/");
  document.querySelectorAll(".jsteps a").forEach((a) => {
    if (here.endsWith(a.dataset.p)) a.setAttribute("aria-current", "page");
  });
  const section = location.pathname.includes("/journey/") ? "journey" : location.pathname.endsWith("resources.html") ? "resources" : location.pathname.endsWith("compare.html") ? "compare" : "";
  document.querySelectorAll(`.nav a[data-section="${section}"]`).forEach((a) => a.classList.add("here"));

  // ---------- helpers ----------
  const NS = "http://www.w3.org/2000/svg";
  const css = (name) => getComputedStyle(doc).getPropertyValue(name).trim();
  function el(tag, attrs, parent) {
    const n = document.createElementNS(NS, tag);
    for (const k in attrs) n.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(n);
    return n;
  }
  const f3 = (v) => v.toFixed(3);
  const pct = (v, d) => (v * 100).toFixed(d == null ? 1 : d) + "%";
  const int = (v) => Math.round(v).toLocaleString("en-US");
  let metrics = null;
  const jsonCache = {};
  function getJSON(name) {
    jsonCache[name] = jsonCache[name] || fetch(ROOT + "assets/data/" + name).then((r) => r.json());
    return jsonCache[name];
  }

  function tooltip(box) {
    let tip = box.querySelector(".tip");
    if (!tip) { tip = document.createElement("div"); tip.className = "tip"; tip.setAttribute("role", "status"); box.appendChild(tip); }
    return {
      show(html, x, y) { tip.innerHTML = html; tip.style.left = x + "px"; tip.style.top = y + "px"; tip.classList.add("on"); },
      hide() { tip.classList.remove("on"); },
    };
  }
  function legend(box, items) {
    const ul = document.createElement("ul");
    ul.className = "legend";
    items.forEach((i) => { const li = document.createElement("li"); li.innerHTML = `<i style="background:${i.color}"></i>${i.name}`; ul.appendChild(li); });
    box.appendChild(ul);
  }
  function tableView(box, head, rows) {
    const d = document.createElement("details");
    d.className = "table-view";
    d.innerHTML = "<summary>Show as table</summary>";
    const wrap = document.createElement("div"); wrap.className = "tbl";
    const t = document.createElement("table");
    t.innerHTML = "<thead><tr>" + head.map((h, i) => `<th${i ? ' class="n"' : ""}>${h}</th>`).join("") + "</tr></thead><tbody>" +
      rows.map((r) => "<tr>" + r.map((c, i) => `<td${i ? ' class="n"' : ""}>${c}</td>`).join("") + "</tr>").join("") + "</tbody>";
    wrap.appendChild(t); d.appendChild(wrap); box.appendChild(d);
  }

  // Grouped vertical bars: groups on x, one bar per series. 4px rounded tops, 2px gaps.
  function groupedBars(box, { groups, series, max = 1, fmt = f3, label }) {
    const W = 640, H = 260, m = { t: 16, r: 8, b: 34, l: 38 };
    const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": label });
    box.appendChild(svg);
    const iw = W - m.l - m.r, ih = H - m.t - m.b;
    const y = (v) => m.t + ih - (v / max) * ih;
    for (let k = 0; k <= 4; k++) {
      const v = (max * k) / 4;
      el("line", { x1: m.l, x2: W - m.r, y1: y(v), y2: y(v), class: k ? "grid-line" : "axis" }, svg);
      el("text", { x: m.l - 6, y: y(v) + 4, "text-anchor": "end" }, svg).textContent = max === 1 ? v.toFixed(2) : int(v);
    }
    const gw = iw / groups.length, pad = gw * 0.18, bw = (gw - 2 * pad - (series.length - 1) * 2) / series.length;
    const tip = tooltip(box);
    groups.forEach((g, gi) => {
      const gx = m.l + gi * gw;
      el("text", { x: gx + gw / 2, y: H - 12, "text-anchor": "middle", class: "lab" }, svg).textContent = g.name;
      series.forEach((s, si) => {
        const v = g[s.key], x = gx + pad + si * (bw + 2), top = y(v), h = m.t + ih - top;
        const r = Math.min(4, bw / 2, h);
        const d = `M${x},${m.t + ih} V${top + r} Q${x},${top} ${x + r},${top} H${x + bw - r} Q${x + bw},${top} ${x + bw},${top + r} V${m.t + ih} Z`;
        const p = el("path", { d, fill: s.color }, svg);
        const hit = el("rect", { x, y: m.t, width: bw, height: ih, fill: "transparent", tabindex: 0, "aria-label": `${g.name} ${s.name} ${fmt(v)}` }, svg);
        const on = () => { p.setAttribute("opacity", "0.8"); const bb = box.getBoundingClientRect(), sb = svg.getBoundingClientRect(); tip.show(`${g.name}<br>${s.name} <b>${fmt(v)}</b>`, (x + bw / 2) / W * sb.width + (sb.left - bb.left), top / H * sb.height + (sb.top - bb.top)); };
        const off = () => { p.removeAttribute("opacity"); tip.hide(); };
        hit.addEventListener("mouseenter", on); hit.addEventListener("focus", on);
        hit.addEventListener("mouseleave", off); hit.addEventListener("blur", off);
      });
    });
    legend(box, series);
    tableView(box, ["Model"].concat(series.map((s) => s.name)), groups.map((g) => [g.name].concat(series.map((s) => fmt(g[s.key])))));
  }

  // Horizontal bars, one series (mean |SHAP| etc.).
  function hBars(box, { rows, color, fmt, label, valueName }) {
    const W = 640, rowH = 28, m = { t: 6, r: 64, b: 6, l: 230 };
    const H = m.t + m.b + rows.length * rowH;
    const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": label });
    box.appendChild(svg);
    const max = Math.max(...rows.map((r) => r.value));
    const iw = W - m.l - m.r;
    rows.forEach((r, i) => {
      const yy = m.t + i * rowH;
      el("text", { x: m.l - 10, y: yy + rowH / 2 + 4, "text-anchor": "end", class: "lab" }, svg).textContent = r.label;
      const w = Math.max(2, (r.value / max) * iw);
      el("rect", { x: m.l, y: yy + 6, width: w, height: rowH - 12, rx: 4, fill: color }, svg);
      el("text", { x: m.l + w + 6, y: yy + rowH / 2 + 4, class: "val" }, svg).textContent = fmt(r.value);
    });
    el("line", { x1: m.l, x2: m.l, y1: m.t, y2: H - m.b, class: "axis" }, svg);
    tableView(box, ["Feature", valueName], rows.map((r) => [r.label, fmt(r.value)]));
  }

  // 100% bars showing a class split.
  function splitBars(box, { rows, label }) {
    const W = 640, rowH = 58, H = rows.length * rowH;
    const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": label });
    box.appendChild(svg);
    rows.forEach((r, i) => {
      const yy = i * rowH;
      el("text", { x: 0, y: yy + 14, class: "lab" }, svg).textContent = r.name;
      const w = r.share * W;
      el("rect", { x: 0, y: yy + 22, width: W, height: 18, rx: 4, fill: css("--card") }, svg);
      el("rect", { x: 0, y: yy + 22, width: Math.max(w, 4), height: 18, rx: 4, fill: r.color }, svg);
      const t = el("text", { x: Math.min(Math.max(w, 4) + 8, W - 4), y: yy + 36, class: "val", "text-anchor": w > W - 120 ? "end" : "start" }, svg);
      t.textContent = `${pct(r.share)} ${r.posName}`;
      if (w > W - 120) t.setAttribute("x", W - 8), t.setAttribute("style", "fill:" + css("--accent-ink"));
    });
    tableView(box, ["Dataset", "Positive share"], rows.map((r) => [r.name, pct(r.share)]));
  }

  // Line chart with a vertical marker the caller can move; crosshair tooltip on hover.
  function lines(box, { data, xKey, series, markers = [], label, xTicks, onPick }) {
    const W = 640, H = 280, m = { t: 14, r: 12, b: 30, l: 38 };
    const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": label });
    box.appendChild(svg);
    const xs = data.map((d) => d[xKey]);
    const x0 = Math.min(...xs), x1 = Math.max(...xs);
    const iw = W - m.l - m.r, ih = H - m.t - m.b;
    const x = (v) => m.l + ((v - x0) / (x1 - x0)) * iw;
    const y = (v) => m.t + ih - v * ih;
    for (let k = 0; k <= 4; k++) {
      el("line", { x1: m.l, x2: W - m.r, y1: y(k / 4), y2: y(k / 4), class: k ? "grid-line" : "axis" }, svg);
      el("text", { x: m.l - 6, y: y(k / 4) + 4, "text-anchor": "end" }, svg).textContent = (k / 4).toFixed(2);
    }
    (xTicks || []).forEach((t) => { el("text", { x: x(t), y: H - 10, "text-anchor": "middle" }, svg).textContent = t.toFixed(1); });
    const fixed = markers.map((mk) => {
      const g = el("g", {}, svg);
      el("line", { x1: x(mk.x), x2: x(mk.x), y1: m.t, y2: m.t + ih, stroke: css(mk.strong ? "--text" : "--muted"), "stroke-width": mk.strong ? 1.5 : 1 }, g);
      el("text", { x: x(mk.x) + 4, y: m.t + 10, style: `fill:${css("--text-2")}` }, g).textContent = mk.label;
      return { g, mk };
    });
    series.forEach((s) => {
      el("path", { d: data.map((d, i) => `${i ? "L" : "M"}${x(d[xKey]).toFixed(1)},${y(d[s.key]).toFixed(1)}`).join(""), fill: "none", stroke: s.color, "stroke-width": 2, "stroke-linejoin": "round" }, svg);
    });
    const cross = el("line", { y1: m.t, y2: m.t + ih, stroke: css("--axis"), "stroke-width": 1, visibility: "hidden" }, svg);
    const dots = series.map((s) => el("circle", { r: 4, fill: s.color, stroke: css("--panel"), "stroke-width": 2, visibility: "hidden" }, svg));
    const tip = tooltip(box);
    const hit = el("rect", { x: m.l, y: m.t, width: iw, height: ih, fill: "transparent" }, svg);
    function at(evt) {
      const sb = svg.getBoundingClientRect(), bb = box.getBoundingClientRect();
      const px = ((evt.clientX - sb.left) / sb.width) * W;
      const v = x0 + ((px - m.l) / iw) * (x1 - x0);
      let best = data[0];
      data.forEach((d) => { if (Math.abs(d[xKey] - v) < Math.abs(best[xKey] - v)) best = d; });
      const cx = x(best[xKey]);
      cross.setAttribute("x1", cx); cross.setAttribute("x2", cx); cross.setAttribute("visibility", "visible");
      dots.forEach((dt, i) => { dt.setAttribute("cx", cx); dt.setAttribute("cy", y(best[series[i].key])); dt.setAttribute("visibility", "visible"); });
      tip.show(`Threshold <b>${best[xKey].toFixed(2)}</b><br>` + series.map((s) => `${s.name} <b>${f3(best[s.key])}</b>`).join(" · "),
        (cx / W) * sb.width + (sb.left - bb.left), (m.t / H) * sb.height + (sb.top - bb.top) + 40);
      return best;
    }
    hit.addEventListener("mousemove", at);
    hit.addEventListener("mouseleave", () => { cross.setAttribute("visibility", "hidden"); dots.forEach((d) => d.setAttribute("visibility", "hidden")); tip.hide(); });
    if (onPick) hit.addEventListener("click", (e) => onPick(at(e)));
    legend(box, series);
    return {
      move(i, v) { const f = fixed[i]; f.g.querySelector("line").setAttribute("x1", x(v)); f.g.querySelector("line").setAttribute("x2", x(v)); const t = f.g.querySelector("text"); t.setAttribute("x", x(v) + 4); t.textContent = v.toFixed(2); },
    };
  }

  // Compare charts: groups are metrics, one bar per source (report, presentation, repo).
  function cmpChart(box, rows, label) {
    const colors = S();
    const series = rows.map((r, i) => ({ name: r.source, key: "v" + i, color: colors[i] }));
    const groups = ["precision", "recall", "f1"].map((m) => {
      const g = { name: m === "f1" ? "F1" : m[0].toUpperCase() + m.slice(1) };
      rows.forEach((r, i) => { g["v" + i] = r[m]; });
      return g;
    });
    groupedBars(box, { groups, series, label });
  }

  // ---------- chart registry ----------
  const S = () => [css("--series-1"), css("--series-2"), css("--series-3")];
  const CHARTS = {
    "imbalance": (box, m) => splitBars(box, {
      label: "Share of positive cases in each dataset",
      rows: [
        { name: `Taiwan bankruptcy (${int(m.facts.financial.firms)} firms)`, share: m.facts.financial.bankrupt_rate, posName: "went bankrupt", color: S()[1] },
        { name: `DataCo orders (${int(m.facts.operations.orders)} after cleaning)`, share: m.facts.operations.late_rate, posName: "arrived late", color: S()[0] },
      ],
    }),
    "fin-models": (box, m) => groupedBars(box, {
      label: "Financial models compared on recall, precision and F1",
      groups: m.financial.model_comparison_reported.models.map((r) => ({ name: r.model, recall: r.recall, precision: r.precision, f1: r.f1 })),
      series: [{ name: "Recall", key: "recall", color: S()[0] }, { name: "Precision", key: "precision", color: S()[1] }, { name: "F1", key: "f1", color: S()[2] }],
    }),
    "ops-models": (box, m) => groupedBars(box, {
      label: "Operations models compared in Week 5 on recall, precision and F1",
      groups: m.operations.week5_comparison.models.map((r) => ({ name: r.model, recall: r.recall, precision: r.precision, f1: r.f1 })),
      series: [{ name: "Recall", key: "recall", color: S()[0] }, { name: "Precision", key: "precision", color: S()[1] }, { name: "F1", key: "f1", color: S()[2] }],
    }),
    "ops-tuning": (box, m) => groupedBars(box, {
      label: "Operations random forest before and after tuning and threshold calibration",
      groups: m.operations.week6.map((r) => ({ name: r.model.replace("Tuned RF at Calibrated Threshold", `Tuned RF at ${r.threshold.toFixed(2)}`).replace("Corrected Baseline RF", "Baseline RF"), recall: r.recall, precision: r.precision, f1: r.f1 })),
      series: [{ name: "Recall", key: "recall", color: S()[0] }, { name: "Precision", key: "precision", color: S()[1] }, { name: "F1", key: "f1", color: S()[2] }],
    }),
    "cmp-fin": (box) => getJSON("comparison.json").then((c) => cmpChart(box, c.financial, "Financial XGBoost: precision, recall and F1 in the report, the presentation and this repo")),
    "cmp-ops": (box) => getJSON("comparison.json").then((c) => cmpChart(box, c.operations, "Operations Random Forest: precision, recall and F1 in the report, the presentation and this repo")),
    "shap-global": (box) => getJSON("financial_shap_cases.json").then((s) => hBars(box, {
      label: "Average size of each feature's effect on the bankruptcy score, top ten",
      rows: s.global_mean_abs_shap.slice(0, 10).map((r) => ({ label: r.label, value: r.value * 100 })),
      color: S()[0], fmt: (v) => v.toFixed(2) + " pts", valueName: "Mean |SHAP| (points)",
    })),
    "ops-threshold": (box, m) => {
      const data = m.operations.validation_curve;
      const cal = m.operations.calibrated_threshold;
      const chart = lines(box, {
        data, xKey: "t", label: "Validation precision, recall and F1 across thresholds", xTicks: [0.1, 0.3, 0.5, 0.7, 0.9],
        series: [{ name: "Recall", key: "recall", color: S()[0] }, { name: "Precision", key: "precision", color: S()[1] }, { name: "F1", key: "f1", color: S()[2] }],
        markers: [{ x: cal, label: cal.toFixed(2), strong: true }, { x: 0.5, label: "0.50" }],
        onPick: (d) => set(d.t),
      });
      const wrap = document.createElement("div"); wrap.className = "slider-wrap";
      wrap.innerHTML = `<label for="vt" class="small muted">Move the threshold</label><input id="vt" type="range" min="${data[0].t}" max="${data[data.length - 1].t}" step="0.01" value="${cal}"><p class="readout" aria-live="polite"></p>`;
      box.insertBefore(wrap, box.firstChild);
      const input = wrap.querySelector("input"), out = wrap.querySelector(".readout");
      function set(t) {
        t = Math.round(t * 100) / 100; input.value = t;
        const d = data.find((r) => Math.abs(r.t - t) < 1e-9);
        chart.move(0, t);
        out.innerHTML = `At <b>${t.toFixed(2)}</b> on the validation set: recall <b>${f3(d.recall)}</b>, precision <b>${f3(d.precision)}</b>, F1 <b>${f3(d.f1)}</b>.` +
          (Math.abs(t - cal) < 1e-9 ? " This is the highest F1, so it became the threshold." : "");
      }
      input.addEventListener("input", () => set(parseFloat(input.value)));
      set(cal);
      tableView(box, ["Threshold", "Recall", "Precision", "F1"], data.filter((d) => Math.round(d.t * 100) % 5 === 0).map((d) => [d.t.toFixed(2), f3(d.recall), f3(d.precision), f3(d.f1)]));
    },
  };

  function draw(box) {
    if (!metrics) return;
    box.innerHTML = "";
    const fn = CHARTS[box.dataset.chart];
    if (fn) fn(box, metrics);
  }
  const boxes = document.querySelectorAll(".chart[data-chart]");
  if (boxes.length) {
    getJSON("metrics.json").then((m) => { metrics = m; boxes.forEach(draw); });
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    if (mq.addEventListener) mq.addEventListener("change", () => boxes.forEach(draw));
  }
})();
