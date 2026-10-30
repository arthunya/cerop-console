/* CEROP deck: starts reveal.js, draws one real SHAP case per layer from the site's JSON,
   and adds the QR code. Charts on other slides are drawn by ../assets/js/site.js. */
(function () {
  "use strict";
  Reveal.initialize({
    width: 1920, height: 1080, margin: 0.02, center: false, hash: true,
    slideNumber: "c/t", controls: true, progress: true, transition: "none",
    pdfSeparateFragments: false, plugins: [RevealNotes],
  });

  const pts = (v) => { const p = v * 100; return (p >= 0.05 ? "+" : p <= -0.05 ? "−" : "") + Math.abs(p).toFixed(1); };

  function whyPanel(box, title, c, base, scoreLabel, outcome) {
    const rows = c.drivers.map((d) => ({ label: d.label, sub: d.value !== undefined ? d.value : null, v: d.contribution }))
      .concat([{ label: c.rest.label, v: c.rest.contribution, rest: true }]);
    const max = Math.max.apply(null, rows.map((r) => Math.abs(r.v)).concat([0.01]));
    box.innerHTML =
      `<h3>${title}</h3><div class="top"><span class="muted">${scoreLabel} · ${c.id} · ${outcome}</span><span class="big">${(c.proba * 100).toFixed(1)}%</span></div>` +
      "<table><tbody>" +
      `<tr class="end"><td>Starting point</td><td class="bar"></td><td class="pts">${(base * 100).toFixed(1)}</td></tr>` +
      rows.map((r) => `<tr class="${r.rest ? "rest" : ""}"><td>${r.label}${r.sub ? ` <span class="muted">(${r.sub})</span>` : ""}</td>` +
        `<td class="bar"><div class="cbar"><i class="${r.v >= 0 ? "up" : "down"}" style="width:${(Math.abs(r.v) / max) * 50}%"></i></div></td>` +
        `<td class="pts">${pts(r.v)}</td></tr>`).join("") +
      `<tr class="end"><td>Model score</td><td class="bar"></td><td class="pts">${(c.proba * 100).toFixed(1)}</td></tr>` +
      "</tbody></table>";
  }

  Promise.all([
    fetch("../assets/data/financial_shap_cases.json").then((r) => r.json()),
    fetch("../assets/data/operations_shap_cases.json").then((r) => r.json()),
  ]).then(([fin, ops]) => {
    const f = fin.cases.find((c) => c.cell === "TP");
    const o = ops.cases.find((c) => c.cell === "TP");
    whyPanel(document.getElementById("why-fin"), "A supplier that failed", f, fin.base_value, "Bankruptcy risk", "went bankrupt");
    whyPanel(document.getElementById("why-ops"), "An order that arrived late", o, ops.base_value, `Late risk · ${o.shipping_mode}`, "arrived late");
  });

  const qr = document.getElementById("qr");
  if (qr && window.QRCode) {
    new QRCode(qr, { text: "https://arthunya.github.io/cerop-console/console/", width: 180, height: 180, colorDark: "#0f172a", colorLight: "#ffffff" });
  }
})();
