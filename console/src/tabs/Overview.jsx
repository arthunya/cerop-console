import { useData, f3, pct, int } from "../data.js";
import { PageHead, Stat, Source, Skeleton, LoadError } from "../components/ui.jsx";

export default function Overview({ go }) {
  const { data: m, error } = useData("metrics.json");
  if (error) return <LoadError error={error} />;
  return (
    <>
      <PageHead eyebrow="Overview" title={<>Two risks, <em>two scores</em></>}>
        A buyer that sources across borders worries about two different things: will this supplier still be in
        business, and will this shipment show up on time? Different teams own those questions, so CEROP answers
        them with two separate models and never blends them into one number.
      </PageHead>
      {!m ? <Skeleton h={320} /> : (
        <>
          <div className="grid two">
            <section className="card">
              <h2>Supplier risk</h2>
              <p className="sub">For a credit or procurement analyst vetting a supplier</p>
              <p>An XGBoost model reads {m.facts.financial.features} financial ratios and estimates the chance a firm goes bankrupt.
                Built from {int(m.facts.financial.firms)} Taiwanese firms, of which only {pct(m.facts.financial.bankrupt_rate)} went bankrupt; {int(m.facts.financial.train)} were used for training.</p>
              <div className="grid two" style={{ marginTop: 12 }}>
                <Stat label="F1 score" value={f3(m.financial.official.f1)} note={`on a ${pct(m.facts.financial.bankrupt_rate, 1)} positive class`} />
                <Stat label="ROC-AUC" value={f3(m.financial.official.roc_auc)} note="ranks failing firms above healthy ones" />
              </div>
              <div className="row" style={{ marginTop: 14 }}><button className="btn sm" onClick={() => go("supplier")}>Explore supplier risk →</button></div>
            </section>
            <section className="card">
              <h2>Shipment delay</h2>
              <p className="sub">For a logistics or supply-chain planner</p>
              <p>A Random Forest reads {m.facts.operations.model_features} order features and estimates the chance a shipment arrives late.
                Trained on {int(m.facts.operations.train)} orders from the DataCo dataset, where {pct(m.facts.operations.late_rate, 0)} arrived late.</p>
              <div className="grid two" style={{ marginTop: 12 }}>
                <Stat label="Recall" value={f3(m.operations.week6[2].recall)} note={`at the calibrated threshold of ${m.operations.calibrated_threshold.toFixed(2)}`} />
                <Stat label="Extra late shipments caught" value={`+${int(m.operations.extra_caught)}`} note="versus the default 0.50 threshold" />
              </div>
              <div className="row" style={{ marginTop: 14 }}><button className="btn sm" onClick={() => go("shipment")}>Explore shipment delay →</button></div>
            </section>
          </div>
          <section className="card">
            <h2>Why two models and not one?</h2>
            <p>A supplier can be financially sound and still ship late, and a struggling firm can ship on time right up until it doesn't.
              Averaging the two would hide exactly the signal each team needs. Keeping them apart also means each model is judged on
              its own data, its own imbalance and its own metric.</p>
            <div className="callout">
              <b>Everything here is real held-out test data.</b> Scores come from running the exported models on the
              {" "}{int(m.facts.financial.test)} test firms and {int(m.facts.operations.test)} test orders they never saw in training.
              Nothing is synthetic, and nothing is retrained in your browser.
            </div>
            <Source><code>results/week6_*.csv</code>, <code>results/web/dataset_facts.json</code> (notebook 07)</Source>
          </section>
        </>
      )}
    </>
  );
}
