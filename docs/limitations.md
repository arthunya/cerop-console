# Limitations

CEROP is a working prototype from a graduate course. These are the known limits, roughly in order of how much they matter.

## Results

- **Reproducibility drift.** `models/cerop_financial_xgb.pkl`, evaluated locally (`xgboost==3.4.1`, `scikit-learn==1.9.0`), scores F1 0.533. The submitted report, built from the team's Colab run, says 0.529. Same code, data and `random_state=42`. Ruled out: threading nondeterminism, data mismatch, seed failure. The cause is library-version differences in the algorithm's internals. The reported 0.529 stays the official figure; nothing was retrained to force a match.
- **Two Week 6 operations runs.** The Colab run (quoted in the submitted reports) chose threshold 0.39: recall 0.849, F1 0.764. The saved notebook in this repo is a later local re-run that chose 0.40: recall 0.825, F1 0.763. Validation F1 at the two thresholds differs in the fourth decimal (notebook 05b, cell 10), so a small change in the data or library flips the pick. The exported model comes from the 0.40 run, so the site, console and README use it. Both runs' files are in `results/`.
- **Week 5 financial CSVs are from the re-run.** `results/week5_financial_*.csv` and the outputs in `notebooks/04a` were overwritten by the local re-run (XGBoost F1 0.533, Random Forest 0.472). The submitted figures (0.529, 0.489) are in the Final Report; `scripts/extract_report_tables.py` pulls them into `results/reported/`.
- **Few positives.** 44 bankrupt firms in the test set. One or two changed predictions move F1 by several points.
- **Half of bankruptcies missed at 0.50.** Recall 0.523. A screening aid, not an automated decision tool.
- **Tuning didn't help.** Neither tuned model beat its starting configuration at 0.50. The financial PR-AUC change has a bootstrap 95% interval that includes zero.

## Data

- **Taiwanese firms, 1999 to 2009.** Not validated on other markets or recent years.
- **DataCo is a teaching dataset,** not live company data.
- **Collinear shipping features.** In the full DataCo file each shipping mode has exactly one scheduled window (Same Day 0 days, First Class 1, Second Class 2, Standard Class 4). SHAP splits credit between `Days for shipment (scheduled)` and `Shipping Mode` arbitrarily; read them as one driver.

## Saved artifacts

- **Column count.** `cerop_operations_preprocessor.pkl` (Week 4) outputs 35 columns, including 8 `Order Status_*` columns. `cerop_operations_rf.pkl` (Week 6) expects 27. Any scoring code must reindex to `model.feature_names_in_` after `.transform()`.
- **One column's scale.** The Week 6 `_v2` training data caps `Order Item Profit Ratio` at the training IQR bounds (−0.34, 0.78) and standard-scales the capped values. The Week 4 preprocessor does neither for that column. Notebook 07 recovers the exact `_v2` transform (max residual 4e-16 over 34,393 rows). On the 8 demo orders the mismatch moves scores by at most 0.009 and changes no decision at 0.40 (notebook 06, section 4). The site and console score the `_v2` test file directly and are not affected.

## Explanations

- The panels show the top six drivers. The rest are summed into one "N more factors combined" line so the total still reconciles. For some firms that remainder is the largest line.
- Financial SHAP uses the interventional method with a 100-row training background. A different background sample gives slightly different attributions; the reconciliation to the score holds either way.

## Scope

No monitoring, retraining, authentication or live data feed. The Random Forest (1.24 GB) can't run in a browser, so operations scores in the console are precomputed on the test set.
