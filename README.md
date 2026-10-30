# CEROP: Cross-Border Enterprise Risk & Operations Predictor

Two machine-learning models built side by side: one estimates whether a **supplier** may go bankrupt, the other whether a **shipment** will arrive late. Each score comes with a reason you can read.

**[Project site](https://arthunya.github.io/cerop/)** · **[Live demo](https://arthunya.github.io/cerop/console/)** · **[Final report (PDF)](https://arthunya.github.io/cerop/reports/CEROP_Final_Report.pdf)** · [Deck](https://arthunya.github.io/cerop/deck/)

A graduate group project from AIT 506 Machine Learning at Westcliff University (summer 2026). It's a working prototype on public datasets, not a production system.

## Results

Held-out test sets: 1,364 firms (44 bankrupt) and 34,393 orders (18,854 late).

| Layer | Model | Threshold | Precision | Recall | F1 | ROC-AUC | PR-AUC |
|---|---|---|---|---|---|---|---|
| Financial | XGBoost | 0.50 | 0.535 | 0.523 | **0.529** | 0.950 | 0.476 |
| Operations | Random Forest (tuned) | 0.50 | 0.845 | 0.629 | 0.721 | 0.826 | 0.873 |
| Operations | Random Forest (tuned) | 0.40 | 0.710 | **0.825** | **0.763** | 0.826 | 0.873 |

Sources: `results/week6_financial_tuning_results.csv` (row "XGBoost - Week 5 published", the official figure) and `results/week6_operations_tuning_results.csv`. Calibrating the operations threshold from 0.50 to 0.40 catches 3,705 more late shipments and adds 4,200 false alarms (`results/week6_operations_confusion_matrices.csv`).

Two things worth knowing before you rerun anything:

- **Reproducibility drift.** The exported XGBoost scores F1 0.533 on a local machine against the reported 0.529, with the same code, data and seed. Library versions differ between the Colab run and the local one. The reported figure stays official. Details in [docs/limitations.md](docs/limitations.md).
- **Two Week 6 runs.** The submitted reports quote an operations threshold of 0.39 from the team's Colab run. The saved notebook here, and the exported model, come from a later local re-run that selected 0.40. Both sets of result files are kept (`results/week6_operations_colab_run/`). This repo uses the 0.40 run throughout.

## Team and roles

- **Arthunya Kanoklertwongse (Aty):** financial layer (exploration and cleaning), verifying the operations leakage and auditing the team's notebooks, the live demo (model export, scoring, SHAP explanations, Risk Console), coordination and report writing. Built this repo, the site and the deck after the course.
- **Ankit Kumar:** financial model selection and tuning.
- **Divya Gopal:** Week 4 pipeline integration, operations model selection and tuning.
- **Aswin Shriram Thiagarajan:** operations EDA and cleaning.

## Quick start

```bash
pip install -r requirements.txt
```

Notebooks run in order, `01` to `07` ([docs/notebook_map.md](docs/notebook_map.md)). They need the raw and processed data described in [data/README.md](data/README.md); set `AIT506_DIR` to the folder that holds it. Notebooks `06` and `07` also need the 1.24 GB Random Forest, which isn't hosted here (available on request; see [models/README.md](models/README.md)); point `CEROP_RF_PKL` at it.

To rebuild the site data and run the console locally:

```bash
python site/build_data.py
cd console && npm ci && CEROP_BASE=/ npm run dev
```

`npm run parity` (in `console/`) re-checks the browser XGBoost scorer against Python on all 1,364 test firms. `python site/build_site.py` renders the site into `_site/`.

## Repository map

| Path | What's there |
|---|---|
| `notebooks/` | The eight course notebooks (outputs kept, local paths redacted) plus `06` and `07`, added for the demo and the site |
| `results/` | Week 5 and 6 result CSVs, both Week 6 operations runs, tables extracted from the Final Report, and `web/` exports from notebook 07 |
| `reports/` | Weekly reports, the Final Report and the deck, as PDF |
| `models/` | The XGBoost model and both preprocessors (the 1.24 GB Random Forest is available on request) |
| `scripts/` | The original demo scripts and `extract_report_tables.py` |
| `console/` | The Risk Console (React + Vite) and the parity test |
| `site/` | The showcase site, the deck, and the scripts that turn `results/` into page data |
| `docs/` | Methodology, limitations, engineering log, notebook map, redaction log |
| `data/` | Download instructions and the 8 + 8 demo cases |

## Limitations

Only 44 bankrupt firms to test on. About half of bankruptcies are missed at the default threshold. The financial data is Taiwanese, 1999 to 2009. DataCo is a teaching dataset. Two shipping features carry the same information. Tuning didn't improve either model. There's no monitoring, retraining or live data. The full list, with the saved-artifact mismatches, is in [docs/limitations.md](docs/limitations.md).

## Data and licenses

| Dataset | Source | License |
|---|---|---|
| Taiwanese Bankruptcy Prediction | [UCI ML Repository](https://archive.ics.uci.edu/dataset/572/taiwanese+bankruptcy+prediction), doi:10.24432/C5004D | CC BY 4.0 |
| DataCo Smart Supply Chain | [Mendeley Data](https://data.mendeley.com/datasets/8gx2fvg2k6/5), Constante, Silva & Pereira, doi:10.17632/8gx2fvg2k6.5 | CC BY 4.0 |
| Global Supply Chain Pressure Index | [Federal Reserve Bank of New York](https://www.newyorkfed.org/research/policy/gscpi) | NY Fed website terms of use; not redistributed here |

Code is under the [MIT license](LICENSE). The datasets keep their own licenses.

## Contact

Arthunya Kanoklertwongse · [LinkedIn](https://linkedin.com/in/arthunya) · [Portfolio](https://arthunya.github.io/portfolio/)
