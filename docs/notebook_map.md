# Notebook map

Run in order. Each was copied from the course folder with outputs intact; the only edits are path redactions ([redactions.md](redactions.md)).

| Notebook | Course week | Source file in the course folder | Author | Purpose |
|---|---|---|---|---|
| `01_eda_combined` | 3 | `Week 3/[Week_3]_Group_4_CEROP.ipynb` | Arthunya (financial), Aswin (operations) | Exploration of both datasets |
| `02a_financial_cleaning` | 4 | `Week 4/WEEK_4_—_Financial_Layer_Cleaning_(Taiwan_Bankruptcy_Dataset).ipynb` | Arthunya | Sentinel tiers, capping, composites |
| `02b_operations_cleaning` | 4 | `Week 4/Final/Wk4_Operations_Layer_Cleaning_FIXED.ipynb` | Aswin | Leakage columns, outliers, dates |
| `03_pipeline_integration` | 4 | `Week 4/Final/Week4_CEROP_Pipeline_Integration_FIXED_v3_FIXED.ipynb` | Divya | One split-then-fit pipeline, GSCPI, checks |
| `04a_financial_model_selection` | 5 | `Week 5/GROUP/Ankit/Week5_Financial_Model_Selection.ipynb` | Ankit | LR vs RF vs XGBoost |
| `04b_operations_model_selection` | 5 | `Week 5/GROUP/Test Divya file/AIT506_Week5_Operational_Model_Selection.ipynb` | Divya | LR vs linear SVM vs RF |
| `05a_financial_finalization` | 6 | `Week 6/Group/Ankit/week6/week6/Week6_Financial_Model_Finalization.ipynb` | Ankit | Tuning, threshold checks, bootstrap |
| `05b_operations_tuning` | 6 | `Week 6/Group/AIT506_Week6_Operations_Model_Tuning.ipynb` | Divya | RF search, threshold calibration |
| `06_live_demo_scoring_and_shap` | 7–8 | new | Arthunya | Runs the demo scripts; profit-ratio scale check |
| `07_export_web_artifacts` | post-course | new | Arthunya | Scores, SHAP cases, what-if model for the site |

Choices made during the inventory (2026-10-24):

- Week 3 had two notebooks of identical size; their SHA-256 hashes match, so `[Week_3]_Group_4_CEROP.ipynb` was used.
- Week 5 operations had two copies; they differ only in execution counts and Colab output IDs, so the newer `Test Divya file` copy was used.
- Notebooks `04a` and `05b` show the 2026-08-17 local re-run outputs, not the Colab outputs quoted in the submitted reports. See [limitations.md](limitations.md).

Notebooks `06` and `07` read inputs from `AIT506_DIR` (the course data folder) and `CEROP_RF_PKL` (a copy of the Random Forest, available on request; see `models/README.md`).
