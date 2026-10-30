import { useData, f3, int } from "../data.js";
import { PageHead, Skeleton, LoadError } from "../components/ui.jsx";

export default function Limits() {
  const { data: m, error } = useData("metrics.json");
  if (error) return <LoadError error={error} />;
  return (
    <>
      <PageHead eyebrow="Limits" title="What this can't tell you">
        CEROP is a working prototype from a graduate course. These are the places where it would need more work before anyone relied on it.
      </PageHead>
      {!m ? <Skeleton h={400} /> : (
        <ul className="limits">
          <li><b>Small number of failures to learn from</b><span>Only {m.facts.financial.test_bankrupt} bankrupt firms are in the test set. One or two predictions changing moves F1 by several points, so treat every financial metric as a rough estimate.</span></li>
          <li><b>Half of bankruptcies are missed at the default threshold</b><span>Recall is {f3(m.financial.official.recall)}. That makes the financial model a screening aid that points an analyst at files to read, not something that should decide on its own.</span></li>
          <li><b>Results moved between runs</b><span>The exported financial model scores F1 {f3(m.financial.reproduced.f1)} on this machine against the reported {f3(m.financial.official.f1)}, with the same code, data and seed. Library versions differ between Colab and the local setup. The operations threshold also came out at {m.operations.calibrated_threshold.toFixed(2)} in the saved re-run and 0.39 in the earlier run the reports quote.</span></li>
          <li><b>Old, single-market financial data</b><span>The firms are Taiwanese and the data covers 1999 to 2009. Nothing here shows the model works for other countries or recent years.</span></li>
          <li><b>Teaching dataset for shipments</b><span>DataCo is a public dataset built for teaching and research, not a live feed from a real company.</span></li>
          <li><b>Two drivers that are really one</b><span>Every shipping mode has exactly one scheduled window in this data, so "scheduled days" and "shipping mode" carry the same information. Read those two explanation rows together.</span></li>
          <li><b>Mismatched saved artifacts</b><span>The saved operations preprocessor produces {m.facts.operations.processed_features} columns and the model expects {m.facts.operations.model_features}; scoring has to drop the extra Order Status columns. It also leaves Order Item Profit Ratio on a different scale from the model's training data. On the 8 demo orders that moves scores by under one point (notebook 06). The scores on this site use the model's own test file and are not affected.</span></li>
          <li><b>Top drivers aren't the whole story</b><span>The explanation panels show the six largest factors. The rest are summed into one line so the total still adds up, and sometimes that remainder is large.</span></li>
          <li><b>Tuning didn't improve either model</b><span>At the default threshold both tuned models scored a little below their starting configuration. The useful change was the operations threshold, which caught {int(m.operations.extra_caught)} more late shipments.</span></li>
          <li><b>No production plumbing</b><span>There's no monitoring, retraining, access control or live data feed. It's a demo of the modelling, not a deployed system.</span></li>
        </ul>
      )}
    </>
  );
}
