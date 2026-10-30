import { useState } from "react";
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine } from "recharts";
import { useData, f3, pct, int, NB } from "../data.js";
import { PageHead, Band, ConfusionMatrix, Source, Skeleton, LoadError } from "../components/ui.jsx";
import { WhyPanel } from "../components/WhyPanel.jsx";

const FILTERS = [["all", "All"], ["TP", "Caught"], ["FN", "Missed"], ["FP", "False alarms"], ["TN", "On time"]];

function CurveTip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const p = payload[0].payload;
  return (
    <div className="tt">
      Threshold <b>{p.t.toFixed(2)}</b><br />
      Recall <b>{f3(p.recall)}</b> · Precision <b>{f3(p.precision)}</b> · F1 <b>{f3(p.f1)}</b>
    </div>
  );
}

export default function Shipment() {
  const { data: m, error: e1 } = useData("metrics.json");
  const { data: tc, error: e2 } = useData("ops_threshold_curve.json");
  const { data: s, error: e3 } = useData("operations_shap_cases.json");
  const [t, setT] = useState(null);
  const [filter, setFilter] = useState("all");
  const [sel, setSel] = useState(null);
  if (e1 || e2 || e3) return <LoadError error={e1 || e2 || e3} />;
  const ready = m && tc && s;
  const cal = m?.operations.calibrated_threshold;
  const thr = t ?? cal;
  const point = tc?.curve.find((c) => Math.abs(c.t - thr) < 1e-9);
  const cases = s ? s.cases.filter((c) => filter === "all" || c.cell === filter) : [];
  const current = s && (s.cases.find((c) => c.id === sel) || s.cases[0]);

  return (
    <>
      <PageHead eyebrow="Shipment delay · operations layer" title="Will this shipment arrive late?">
        The model gives every order a probability of arriving late. Where you draw the line is a business choice, not a
        technical one. Drag the threshold and watch the trade-off on all {tc ? int(tc.n) : "…"} held-out test orders.
      </PageHead>
      {!ready ? <Skeleton h={480} /> : (
        <>
          <section className="card">
            <h2>Threshold explorer</h2>
            <p className="sub">Flag an order as "likely late" when its score is at or above the threshold</p>
            <div className="big-slider">
              <div className="thr-readout">
                <span className="mono">{thr.toFixed(2)}</span>
                <span className="muted small">{Math.abs(thr - cal) < 1e-9 ? "calibrated in Week 6" : Math.abs(thr - 0.5) < 1e-9 ? "library default" : "your choice"}</span>
              </div>
              <label htmlFor="thr" className="sr-only">Decision threshold</label>
              <input id="thr" type="range" min={tc.curve[0].t} max={tc.curve[tc.curve.length - 1].t} step={0.01} value={thr}
                onChange={(e) => setT(Math.round(parseFloat(e.target.value) * 100) / 100)} />
              <div className="row">
                <button className="btn sm" onClick={() => setT(cal)} aria-pressed={Math.abs(thr - cal) < 1e-9}>Calibrated ({cal.toFixed(2)})</button>
                <button className="btn sm" onClick={() => setT(0.5)} aria-pressed={Math.abs(thr - 0.5) < 1e-9}>Default (0.50)</button>
              </div>
            </div>
            <p className="sentence">
              At {thr.toFixed(2)}, the model catches <b>{int(point.tp)}</b> of {int(tc.positives)} late shipments and raises <b>{int(point.fp)}</b> false alarms.
            </p>
            <div className="grid two" style={{ marginTop: 14 }}>
              <div>
                <ConfusionMatrix tn={point.tn} fp={point.fp} fn={point.fn} tp={point.tp} />
                <div className="grid two" style={{ marginTop: 10, gridTemplateColumns: "repeat(3, 1fr)", display: "grid", gap: 8 }}>
                  <div className="stat"><div className="label">Recall</div><div className="value" style={{ fontSize: 20 }}>{f3(point.recall)}</div></div>
                  <div className="stat"><div className="label">Precision</div><div className="value" style={{ fontSize: 20 }}>{f3(point.precision)}</div></div>
                  <div className="stat"><div className="label">F1</div><div className="value" style={{ fontSize: 20 }}>{f3(point.f1)}</div></div>
                </div>
              </div>
              <div>
                <div className="chart" role="img" aria-label="Recall, precision and F1 at each threshold on the test set">
                  <ResponsiveContainer>
                    <LineChart data={tc.curve} margin={{ top: 8, right: 12, bottom: 4, left: -16 }}>
                      <CartesianGrid stroke="var(--grid)" vertical={false} />
                      <XAxis dataKey="t" type="number" domain={[tc.curve[0].t, tc.curve[tc.curve.length - 1].t]} ticks={[0.1, 0.3, 0.5, 0.7, 0.9]} stroke="var(--axis)" tickLine={false} />
                      <YAxis domain={[0, 1]} ticks={[0, 0.25, 0.5, 0.75, 1]} stroke="var(--axis)" tickLine={false} />
                      <Tooltip content={<CurveTip />} cursor={{ stroke: "var(--axis)" }} />
                      <ReferenceLine x={0.5} stroke="var(--muted)" strokeWidth={1} label={{ value: "0.50", position: "insideTopRight", fill: "var(--muted)", fontSize: 11 }} />
                      <ReferenceLine x={thr} stroke="var(--text)" strokeWidth={1.5} />
                      <Line type="monotone" dataKey="recall" stroke="var(--series-1)" strokeWidth={2} dot={false} isAnimationActive={false} />
                      <Line type="monotone" dataKey="precision" stroke="var(--series-2)" strokeWidth={2} dot={false} isAnimationActive={false} />
                      <Line type="monotone" dataKey="f1" stroke="var(--series-3)" strokeWidth={2} dot={false} isAnimationActive={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
                <div className="legend">
                  <span><i style={{ background: "var(--series-1)" }} />Recall: share of late orders caught</span>
                  <span><i style={{ background: "var(--series-2)" }} />Precision: share of flags that were right</span>
                  <span><i style={{ background: "var(--series-3)" }} />F1</span>
                </div>
              </div>
            </div>
            <div className="callout" style={{ marginTop: 14 }}>
              Moving from 0.50 to {cal.toFixed(2)} catches <b>{int(m.operations.extra_caught)} more late shipments</b> and adds{" "}
              <b>{int(m.operations.extra_false_alarms)} false alarms</b>. Whether that's worth it depends on what a missed delay costs compared with
              an unnecessary check. The team picked {cal.toFixed(2)} because it gave the best F1 on a validation set held out from training.
            </div>
            <p className="small muted" style={{ marginTop: 10 }}>
              The submitted reports quote 0.39 from the team's earlier Colab run, which caught {int(m.operations.colab_run.extra_caught)} more. The model exported
              to this site comes from the saved notebook re-run, which selected {cal.toFixed(2)}; every number on this page uses that run.
            </p>
            <Source><code>results/web/operations_test_scores.json</code> (34,393 orders scored by the exported Random Forest, notebook 07). At {cal.toFixed(2)} and 0.50 these counts match <code>results/week6_operations_confusion_matrices.csv</code> exactly.</Source>
          </section>

          <div className="grid split">
            <section className="card">
              <h2>Sample orders</h2>
              <p className="sub">{s.cases.length} test orders, ten from each outcome at the {cal.toFixed(2)} threshold</p>
              <div className="filters" role="group" aria-label="Filter orders by outcome">
                {FILTERS.map(([k, label]) => (
                  <button key={k} className="chip" aria-pressed={filter === k} onClick={() => setFilter(k)}>{label}</button>
                ))}
              </div>
              <div className="cases scroll">
                {cases.map((c) => (
                  <button key={c.id} className="case" aria-current={current.id === c.id} onClick={() => setSel(c.id)}>
                    <span className="id">{c.id}</span>
                    <span className="score">{pct(c.proba)}</span>
                    <span className="meta"><Band band={c.band} /> &nbsp;{c.shipping_mode} · {c.scheduled_days} day{c.scheduled_days === 1 ? "" : "s"} scheduled · {c.market} · {c.label === 1 ? "arrived late" : "on time"}</span>
                  </button>
                ))}
              </div>
            </section>
            <section className="card">
              <h2>Why this score?</h2>
              <p className="sub">{current.shipping_mode} · {current.category} · {current.segment} customer</p>
              <WhyPanel c={current} base={s.base_value} kind="ops" />
              <p className="small muted" style={{ marginTop: 10 }}>
                In this dataset each shipping mode has exactly one scheduled window (Same Day 0 days, First Class 1, Second Class 2,
                Standard Class 4). The model splits credit between the two as it likes, so read those drivers as one.
              </p>
              <Source>notebook 07, <a href={NB("07_export_web_artifacts.ipynb")}>07_export_web_artifacts.ipynb</a>. One-hot columns are summed back to their parent feature; each case reconciles to its score within 1e-6.</Source>
            </section>
          </div>
          <p className="small muted" style={{ marginTop: 12 }}>
            The Random Forest file is 1.24 GB, far too big for a browser. Every operations score here was computed ahead of time by the real model on the held-out test set.
          </p>
        </>
      )}
    </>
  );
}
