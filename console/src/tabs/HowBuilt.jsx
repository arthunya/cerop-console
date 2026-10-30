import { useData, f3, int, NB } from "../data.js";
import { PageHead, Source, Skeleton, LoadError } from "../components/ui.jsx";

const SITE_PAGE = (p) => `/cerop/journey/${p}`;

export default function HowBuilt() {
  const { data: m, error } = useData("metrics.json");
  if (error) return <LoadError error={error} />;
  return (
    <>
      <PageHead eyebrow="How it was built" title="From raw data to a score you can question">
        The short version of eight weeks of work. Each step links to the notebook that did it and the page that tells the story.
      </PageHead>
      {!m ? <Skeleton h={400} /> : (
        <>
          <section className="card">
            <h2>Pipeline</h2>
            <ol className="steps" style={{ marginTop: 8 }}>
              <li><div><b>Three public datasets</b><span>Taiwan bankruptcy ({int(m.facts.financial.firms)} firms), DataCo supply chain ({int(m.facts.operations.rows_before_cleaning)} order lines before cleaning), and the New York Fed's supply-chain pressure index. <a href={SITE_PAGE("02-data.html")}>Data &amp; exploration</a></span></div></li>
              <li><div><b>Cleaning, one layer at a time</b><span>Sentinel values capped or dropped in the financial data; identifiers, free text and outcome fields removed from the orders. <a href={NB("02a_financial_cleaning.ipynb")}>02a</a> · <a href={NB("02b_operations_cleaning.ipynb")}>02b</a></span></div></li>
              <li><div><b>Leakage checks</b><span>Anything that's only known after delivery was removed, including actual shipping days and, later, eight Order Status columns. <a href={SITE_PAGE("03-pipeline.html")}>Cleaning &amp; pipeline</a></span></div></li>
              <li><div><b>Split, then scale</b><span>Stratified 80/20 splits with a fixed seed; scalers and encoders fitted on training data only. <a href={NB("03_pipeline_integration.ipynb")}>03</a></span></div></li>
              <li><div><b>Model selection</b><span>Three candidates per layer, judged on F1, recall and PR-AUC rather than accuracy. <a href={SITE_PAGE("04-model-selection.html")}>Model selection</a></span></div></li>
              <li><div><b>Tuning and threshold</b><span>Hyperparameter search, then a decision threshold chosen on a validation set. <a href={SITE_PAGE("05-tuning.html")}>Tuning &amp; thresholds</a></span></div></li>
              <li><div><b>Export, score, explain</b><span>Models saved once and loaded read-only; every explanation checked to add up to its score. <a href={SITE_PAGE("06-explainability.html")}>Explainability &amp; demo</a></span></div></li>
            </ol>
          </section>

          <div className="grid two">
            <section className="card">
              <h2>Catching leakage</h2>
              <p>A model that can see the answer looks brilliant in testing and fails in use. Two kinds of leak were found and removed:</p>
              <ul style={{ paddingLeft: 18, margin: 0, color: "var(--text-2)" }}>
                <li>fields filled in only after delivery, such as actual shipping days and delivery status;</li>
                <li>eight <code>Order Status</code> columns. Week 4 kept them as pre-delivery information; the Week 6 review judged they could carry information about the delivery outcome and dropped them, taking the model from 35 to {m.facts.operations.model_features} inputs.</li>
              </ul>
              <p className="small muted" style={{ marginTop: 10 }}>Sales and order counts turn erratic after September 2017, so orders from 1 October 2017 onward were removed before the split as a data-quality filter.</p>
            </section>
            <section className="card">
              <h2>Tuning didn't help, and that's a result</h2>
              <p>
                Financial: on the same tuning split, the Week 5 setup scored F1 {f3(m.financial.tuning.before.f1)} and the tuned one {f3(m.financial.tuning.after.f1)}.
                Operations: the tuned forest scored F1 {f3(m.operations.week6[1].f1)} at 0.50 against {f3(m.operations.week6[0].f1)} for the untuned baseline.
              </p>
              <p>The gain came from somewhere else: moving the operations threshold to {m.operations.calibrated_threshold.toFixed(2)} lifted F1 to {f3(m.operations.week6[2].f1)} and recall to {f3(m.operations.week6[2].recall)}.</p>
              <Source><code>results/week6_financial_tuning_results.csv</code>, <code>results/week6_operations_tuning_results.csv</code></Source>
            </section>
          </div>

          <section className="card">
            <h2>Financial model comparison</h2>
            <p className="sub">Test set, threshold 0.50, as reported in the Final Report</p>
            <div className="tbl-wrap">
              <table className="data">
                <thead><tr><th>Model</th><th>Accuracy</th><th>Precision</th><th>Recall</th><th>F1</th><th>ROC-AUC</th></tr></thead>
                <tbody>
                  {m.financial.model_comparison_reported.models.map((r) => (
                    <tr key={r.model} className={r.model === "XGBoost" ? "win" : ""}>
                      <td>{r.model}</td><td className="n">{f3(r.accuracy)}</td><td className="n">{f3(r.precision)}</td><td className="n">{f3(r.recall)}</td><td className="n">{f3(r.f1)}</td><td className="n">{f3(r.roc_auc)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="small" style={{ marginTop: 10 }}>Logistic Regression catches the most bankruptcies but flags so many healthy firms that most of its alarms are wrong. XGBoost gives the best balance.</p>
            <Source>Final Report Table 7, extracted by <code>scripts/extract_report_tables.py</code></Source>
          </section>

          <section className="card">
            <h2>How the explanations are checked</h2>
            <ul style={{ paddingLeft: 18, margin: 0, color: "var(--text-2)" }}>
              <li>SHAP values are computed straight from the exported model files, in probability space, so they're in the same units as the score.</li>
              <li>For every case shown, the starting point plus all feature contributions has to equal the model's score to within one in a million. The export stops if any case fails.</li>
              <li>Category columns that were split into several one-hot columns are added back together, and labelled with the order's real value (say, "First Class"), not the encoded column name.</li>
              <li>The top drivers rarely explain the whole move, so the remainder is always shown as its own line.</li>
            </ul>
          </section>
        </>
      )}
    </>
  );
}
