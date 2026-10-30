# Methodology

## Problem

Two supervised binary classifiers, trained offline on fixed data:

| Layer | Question | Label | Data |
|---|---|---|---|
| Financial | Will this firm go bankrupt? | `Bankrupt?` | Taiwanese Bankruptcy Prediction (UCI), 6,819 firms |
| Operations | Will this order arrive late? | `Late_delivery_risk` | DataCo Smart Supply Chain, 171,962 orders after cleaning, plus the NY Fed GSCPI by month |

They are deliberately separate: different owners, different data, different class balance (3.2% vs 54.8% positive).

## Preparation (Week 4, notebooks 02a, 02b, 03)

- **Split first, then fit.** Stratified 80/20 splits with `random_state=42`. Every fitted step (99th-percentile caps, IQR bounds, scalers, one-hot vocabularies, target encoders) learns from the training split only.
- **Financial.** Sentinel values sorted into tiers: lightly damaged columns capped at the 99th percentile, columns mostly made of placeholders dropped. Two composite features added. 85 features after cleaning.
- **Operations.** Personal data, free text and duplicate IDs removed. Leakage columns removed: `Days for shipping (real)`, `Delivery Status`, shipping date. Orders from 2017-10-01 onward removed before the split as a data-quality filter. Date split into year, month, day of week, hour; GSCPI joined by month. 35 processed features; Week 6 dropped the 8 `Order Status_*` columns as a leakage risk, leaving 27.
- **Checks** (asserts in notebook 03): no missing values, all values finite, matching train/test columns, for both layers.

## Model selection (Week 5, notebooks 04a, 04b)

- Financial: Logistic Regression and Random Forest with `class_weight="balanced"`, XGBoost with `scale_pos_weight` (about 30). No synthetic oversampling. XGBoost chosen on F1 and ROC-AUC.
- Operations: Logistic Regression, linear SVM, Random Forest. Random Forest chosen.

## Tuning and threshold (Week 6, notebooks 05a, 05b)

- Randomized search with cross-validation for both layers. Neither tuned model beat its baseline at 0.50.
- Operations threshold picked as the best F1 on a validation set carved from the training data (0.40 in the saved run), then evaluated once on the test set.
- Financial threshold stays at 0.50.

## Export and scoring

- `final_model` (fit on all 137,569 training rows) exported for operations; the Week 5 XGBoost for financial. Artifacts are loaded read-only; notebooks 06 and 07 print SHA-256 before and after.
- Operations scoring reindexes the preprocessor output to `model.feature_names_in_`.

## Explanations (notebook 07)

- **Financial XGBoost:** `shap.TreeExplainer(model, data=<100 training rows, random_state=42>, feature_perturbation="interventional", model_output="probability")`. The saved model has `enable_categorical=True` (a library default; no feature is categorical), which this path rejects. It is set to `False` in memory only, after confirming `predict_proba` is identical.
- **Operations Random Forest:** plain `TreeExplainer`; leaf values are already probabilities.
- One-hot columns are summed back to the parent feature and labelled with the case's real category.
- **Reconciliation:** for every exported case, base value plus all contributions equals `predict_proba` within 1e-6 (assert). Largest observed: 3.9e-7 financial, 4e-13 operations.

## Web artifacts

- `operations_test_scores.json` stores probabilities at full double precision. Rounding to 4 or 6 decimals moved a few orders across a 0.01 slider step; full precision reproduces the Week 6 confusion matrices exactly at every step (asserted).
- **Browser what-if:** the XGBoost booster is serialised to JSON in memory (`save_raw("json")`, the `.pkl` is not written) with the scaler's `mean_` and `scale_`. `console/src/lib/xgbScorer.js` walks the trees in float32 arithmetic with XGBoost's missing-value rule. `console/scripts/parity.mjs` compares it with Python on all 1,364 test firms; it shipped because the largest difference was 6e-8 (gate: 1e-5). Results in `results/web/financial_whatif_parity.csv`.
- `site/build_data.py` turns `results/` into the JSON the site, deck and console read. `site/build_site.py` fills every number on the site from that JSON and fails on an unknown placeholder.
