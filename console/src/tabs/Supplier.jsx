import { useEffect, useMemo, useState } from "react";
import { useData, fetchJSON, f3, pct, bandFor, NB } from "../data.js";
import { PageHead, Band, ConfusionMatrix, Source, Skeleton, LoadError, Stat } from "../components/ui.jsx";
import { WhyPanel } from "../components/WhyPanel.jsx";
import { buildScorer } from "../lib/xgbScorer.js";

const FILTERS = [["all", "All"], ["TP", "Caught"], ["FN", "Missed"], ["FP", "False alarms"], ["TN", "Healthy"]];

export default function Supplier() {
  const { data: m, error: e1 } = useData("metrics.json");
  const { data: s, error: e2 } = useData("financial_shap_cases.json");
  const [filter, setFilter] = useState("all");
  const [sel, setSel] = useState(null);
  if (e1 || e2) return <LoadError error={e1 || e2} />;

  const cases = s ? s.cases.filter((c) => filter === "all" || c.cell === filter) : [];
  const current = s && (s.cases.find((c) => c.id === sel) || s.cases[0]);

  return (
    <>
      <PageHead eyebrow="Supplier risk · financial layer" title="Will this supplier still be in business?">
        Pick a test firm to see its bankruptcy score and the factors that moved it. The model flags a firm as high risk
        at a score of 50% or more.
      </PageHead>
      {!m || !s ? <Skeleton h={420} /> : (
        <>
          <div className="grid four">
            <Stat label="F1 (official)" value={f3(m.financial.official.f1)} note="balances caught vs. false alarms" />
            <Stat label="Recall" value={pct(m.financial.official.recall, 0)} note={`caught ${m.financial.official.tp} of ${m.financial.official.tp + m.financial.official.fn} bankruptcies`} />
            <Stat label="Precision" value={pct(m.financial.official.precision, 0)} note="of flagged firms really failed" />
            <Stat label="Accuracy" value={pct(m.financial.official.accuracy, 0)} note="looks great, means little here" />
          </div>
          <div className="callout" style={{ marginTop: 16 }}>
            <b>Why accuracy misleads:</b> only {m.facts.financial.test_bankrupt} of {m.facts.financial.test.toLocaleString("en-US")} test firms went
            bankrupt, so a model that never flags anyone would still be {pct(1 - m.facts.financial.test_bankrupt / m.facts.financial.test, 0)} accurate.
            F1 and recall are the honest measures here.
          </div>

          <div className="grid split" style={{ marginTop: 16 }}>
            <section className="card">
              <h2>Sample firms</h2>
              <p className="sub">{s.cases.length} firms from the test set, picked across all four outcomes</p>
              <div className="filters" role="group" aria-label="Filter firms by outcome">
                {FILTERS.map(([k, label]) => (
                  <button key={k} className="chip" aria-pressed={filter === k} onClick={() => setFilter(k)}>{label}</button>
                ))}
              </div>
              <div className="cases scroll">
                {cases.map((c) => (
                  <button key={c.id} className="case" aria-current={current.id === c.id} onClick={() => setSel(c.id)}>
                    <span className="id">{c.id}</span>
                    <span className="score">{pct(c.proba)}</span>
                    <span className="meta"><Band band={c.band} /> &nbsp;{c.label === 1 ? "went bankrupt" : "stayed solvent"}</span>
                  </button>
                ))}
              </div>
            </section>
            <section className="card">
              <h2>Why this score?</h2>
              <p className="sub">Real SHAP values from the exported model, in probability points</p>
              <WhyPanel c={current} base={s.base_value} kind="fin" />
              <Source>notebook 07, <a href={NB("07_export_web_artifacts.ipynb")}>07_export_web_artifacts.ipynb</a>. Each case is checked: base + all 85 contributions = score, within 1e-6.</Source>
            </section>
          </div>

          <WhatIf caseId={current.id} caseLabel={current.id} />

          <section className="card">
            <h2>Test-set result</h2>
            <p className="sub">Official figures from the submitted report, threshold 0.50</p>
            <ConfusionMatrix {...m.financial.official} pos="Bankrupt" neg="Solvent" />
            <p className="small" style={{ marginTop: 12 }}>
              Reproducibility note: the exported model file, run on this machine's library versions, scores F1 {f3(m.financial.reproduced.f1)}
              {" "}instead of the official {f3(m.financial.official.f1)}. Same code, data and seed. With only {m.facts.financial.test_bankrupt} bankrupt firms in
              the test set, one or two flipped predictions move F1 that much. The official number stays the reported one.
            </p>
            <Source><code>results/week6_financial_tuning_results.csv</code> (row "XGBoost - Week 5 published"), <code>results/web/financial_test_scores.json</code></Source>
          </section>
        </>
      )}
    </>
  );
}

function WhatIf({ caseId }) {
  const [model, setModel] = useState(null);
  const [err, setErr] = useState(null);
  const [vals, setVals] = useState({});

  useEffect(() => {
    let live = true;
    fetchJSON("financial_whatif.json").then((w) => live && setModel({ w, scorer: buildScorer(w) }), (e) => live && setErr(e));
    return () => { live = false; };
  }, []);

  const baseRow = model?.w.cases[caseId];
  useEffect(() => { setVals({}); }, [caseId]);

  const result = useMemo(() => {
    if (!model || !baseRow) return null;
    const row = baseRow.slice();
    const names = model.w.feature_names;
    for (const [k, v] of Object.entries(vals)) row[names.indexOf(k)] = v;
    return { original: model.scorer.predictRaw(baseRow), now: model.scorer.predictRaw(row) };
  }, [model, baseRow, vals]);

  if (err) return null; // the what-if is optional; the rest of the page works without it
  return (
    <section className="card">
      <h2>What if this firm's numbers changed?</h2>
      <p className="sub">Move the six factors the model leans on most. The score is recomputed in your browser by the same XGBoost trees.</p>
      {!model || !result ? <Skeleton h={220} /> : (
        <div className="grid two">
          <div>
            {model.w.top_features.map((f) => {
              const i = model.w.feature_names.indexOf(f.feature);
              const orig = baseRow[i];
              const lo = Math.min(f.p01, orig), hi = Math.max(f.p99, orig);
              const v = vals[f.feature] ?? orig;
              const step = (hi - lo) / 200 || 0.0001;
              return (
                <div className="slider-row" key={f.feature}>
                  <label className="top" htmlFor={`wi-${i}`}>
                    <span>{f.label}</span><b>{v.toPrecision(4)}</b>
                  </label>
                  <input id={`wi-${i}`} type="range" min={lo} max={hi} step={step} value={v}
                    onChange={(e) => setVals((s) => ({ ...s, [f.feature]: parseFloat(e.target.value) }))} />
                  <div className="ends"><span>{lo.toPrecision(3)}</span><span>original {orig.toPrecision(4)}</span><span>{hi.toPrecision(3)}</span></div>
                </div>
              );
            })}
            <button className="btn sm" onClick={() => setVals({})} disabled={!Object.keys(vals).length}>Reset to original</button>
          </div>
          <div>
            <div className="stat">
              <div className="label">Score for {caseId}</div>
              <div className="value">{pct(result.now)}</div>
              <div className="note">was {pct(result.original)} · <Band band={bandFor(result.now, 0.5)} /></div>
            </div>
            <p className="small" style={{ marginTop: 12 }}>
              Slider ranges run from the 1st to the 99th percentile of the training data (widened to include this firm's own value).
              The SHAP bars above still describe the original case, not your edited one.
            </p>
            <p className="small muted">
              Before this shipped, the browser scorer was checked against Python on all {model.w.parity.rows.toLocaleString("en-US")} test firms:
              largest difference {model.w.parity.max_abs_diff.toExponential(1)}.
            </p>
          </div>
        </div>
      )}
    </section>
  );
}
