// Parity gate for the financial what-if feature.
// Runs the JavaScript XGBoost scorer over all 1,364 test firms and compares each probability
// with Python's predict_proba (computed in notebooks/07_export_web_artifacts.ipynb).
// Pass = max absolute difference <= 1e-5 on every row. Writes
// results/web/financial_whatif_parity.csv and exits non-zero on failure.
//
// Usage (from console/): node scripts/parity.mjs

import { readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { buildScorer } from "../src/lib/xgbScorer.js";

const here = dirname(fileURLToPath(import.meta.url));
const web = join(here, "..", "..", "results", "web");
const whatif = JSON.parse(readFileSync(join(web, "financial_whatif_model.json"), "utf8"));
const test = JSON.parse(readFileSync(join(web, "financial_test_raw.json"), "utf8"));

const scorer = buildScorer(whatif);
const TOL = 1e-5;
let maxDiff = 0;
let fails = 0;
const lines = ["row,python_proba,js_proba,abs_diff,pass"];
test.rows.forEach((row, i) => {
  const js = scorer.predictRaw(row);
  const py = test.python_proba[i];
  const d = Math.abs(js - py);
  maxDiff = Math.max(maxDiff, d);
  const ok = d <= TOL;
  if (!ok) fails++;
  lines.push(`${i},${py},${js},${d},${ok}`);
});
writeFileSync(join(web, "financial_whatif_parity.csv"), lines.join("\n") + "\n");
console.log(`rows: ${test.rows.length}  max |js - python|: ${maxDiff.toExponential(3)}  failures: ${fails}`);
if (fails > 0) {
  console.error("PARITY FAILED - the what-if feature must not ship");
  process.exit(1);
}
console.log("PARITY PASSED");
