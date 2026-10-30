"""
CEROP local scoring demo — no cloud dependency.

Loads the four exported CEROP artifacts (read-only), scores the 8 new
financial cases and 8 new operations cases in this folder, and writes both
a console summary and a self-contained scored_output.html.

Thresholds are hard-coded per CLAUDE.md's "Live demo — decision log":
  financial:  0.50 (Week 5 published configuration, default)
  operations: 0.39 (Week 6 calibrated threshold, NOT the 0.50 default)
"""
import os
import html
import datetime
import joblib
import pandas as pd

MODELS_DIR = r"<AIT506_PROJECT_FOLDER>\CEROP_Live_Demo\models"
DEMO_DIR = r"<AIT506_PROJECT_FOLDER>\CEROP_Live_Demo\demo_data"

FINANCIAL_THRESHOLD = 0.50
OPERATIONS_THRESHOLD = 0.39

DRIFT_NOTE = (
    "cerop_financial_xgb.pkl, re-evaluated in this environment, produces "
    "F1 = 0.5333, not the F1 = 0.5287 reported in the Week 5/6 written report "
    "and cited on the presentation slides and dashboard. Confirmed root cause: "
    "library-version drift between this machine's xgboost/scikit-learn and "
    "whatever produced the original result (likely Colab) \u2014 random_state=42 "
    "fixes the RNG seed but not internal algorithm behavior across library "
    "versions. The published report/slides/dashboard number (F1=0.5287) stays "
    "as the official figure. This live demo shows F1=0.5333 for this specific "
    "exported artifact \u2014 stated here as a reproducibility lesson, not hidden "
    "or apologized for."
)


def risk_band(prob, threshold):
    if prob >= threshold:
        return "HIGH"
    if prob >= threshold * 0.6:
        return "WATCH"
    return "CLEAR"


def score_layer(csv_path, id_cols, preprocessor, model, threshold, layer_name):
    """Score each row independently so one bad row can't crash the batch."""
    df = pd.read_csv(csv_path)
    meta_cols = id_cols
    feature_cols = [c for c in df.columns if c not in meta_cols]

    results = []
    for idx in df.index:
        case_id = df.loc[idx, meta_cols[0]]
        try:
            # .loc[[idx], cols] keeps this a single-row DataFrame with each
            # column's original dtype intact (unlike .to_frame().T, which
            # upcasts everything to object and silently breaks numeric/
            # categorical transformers).
            feature_row = df.loc[[idx], feature_cols]

            transformed = preprocessor.transform(feature_row)
            transformed_df = pd.DataFrame(
                transformed, columns=preprocessor.get_feature_names_out()
            )
            # The Week 4 operations preprocessor's ColumnTransformer still
            # includes 8 leaky "Order Status_*" one-hot columns that the
            # Week 6 RF was correctly trained without (see CLAUDE.md /
            # STATUS.md — documented artifact-level mismatch, confirmed
            # 2026-08-18). Reindexing to the model's own expected feature
            # set drops exactly those 8 columns for operations and is a
            # no-op for financial, where the sets already match.
            if hasattr(model, "feature_names_in_"):
                transformed_df = transformed_df[list(model.feature_names_in_)]
            prob = float(model.predict_proba(transformed_df)[:, 1][0])
            band = risk_band(prob, threshold)
            results.append({
                "case_id": case_id,
                "label": df.loc[idx, meta_cols[1]],
                "risk_score": round(prob, 6),
                "risk_band": band,
            })
        except Exception as e:
            print(f"[{layer_name}] ERROR scoring {case_id}: {type(e).__name__}: {e}")
            continue

    return pd.DataFrame(results)


def render_table_html(df, label_col_name):
    if df.empty:
        return "<p><em>No rows scored successfully.</em></p>"
    df_sorted = df.sort_values("risk_score", ascending=False)
    band_colors = {
        "HIGH": "#fddede",
        "WATCH": "#fdf0cc",
        "CLEAR": "#dcf5df",
    }
    rows_html = []
    for _, r in df_sorted.iterrows():
        color = band_colors.get(r["risk_band"], "#ffffff")
        rows_html.append(
            f'<tr style="background-color:{color};">'
            f'<td>{html.escape(str(r["case_id"]))}</td>'
            f'<td>{html.escape(str(r["label"]))}</td>'
            f'<td>{r["risk_score"]:.4f}</td>'
            f'<td>{html.escape(str(r["risk_band"]))}</td>'
            f'</tr>'
        )
    return (
        f'<table>'
        f'<thead><tr><th>Case ID</th><th>{html.escape(label_col_name)}</th>'
        f'<th>Risk Score</th><th>Risk Band</th></tr></thead>'
        f'<tbody>{"".join(rows_html)}</tbody>'
        f'</table>'
    )


def main():
    # 1. Load models (read-only)
    xgb_model = joblib.load(os.path.join(MODELS_DIR, "cerop_financial_xgb.pkl"))
    rf_model = joblib.load(os.path.join(MODELS_DIR, "cerop_operations_rf.pkl"))
    financial_preprocessor = joblib.load(os.path.join(MODELS_DIR, "cerop_financial_preprocessor.pkl"))
    operations_preprocessor = joblib.load(os.path.join(MODELS_DIR, "cerop_operations_preprocessor.pkl"))
    print("Loaded all 4 models/preprocessors from:", MODELS_DIR)

    # 2/3. Score both layers
    financial_results = score_layer(
        os.path.join(DEMO_DIR, "financial_new_cases.csv"),
        ["case_id", "counterparty_name"],
        financial_preprocessor, xgb_model,
        FINANCIAL_THRESHOLD, "FINANCIAL",
    )
    operations_results = score_layer(
        os.path.join(DEMO_DIR, "operations_new_cases.csv"),
        ["case_id", "order_ref"],
        operations_preprocessor, rf_model,
        OPERATIONS_THRESHOLD, "OPERATIONS",
    )

    # 5. Console summary
    print("\n" + "=" * 70)
    print("FINANCIAL LAYER \u2014 risk scores (threshold = %.2f)" % FINANCIAL_THRESHOLD)
    print("=" * 70)
    if financial_results.empty:
        print("No rows scored successfully.")
    else:
        print(financial_results.sort_values("risk_score", ascending=False).to_string(index=False))

    print("\n" + "=" * 70)
    print("OPERATIONS LAYER \u2014 risk scores (threshold = %.2f)" % OPERATIONS_THRESHOLD)
    print("=" * 70)
    if operations_results.empty:
        print("No rows scored successfully.")
    else:
        print(operations_results.sort_values("risk_score", ascending=False).to_string(index=False))

    # 6. HTML output
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>CEROP Scoring \u2014 Local Simulation</title>
<style>
  body {{ font-family: -apple-system, Segoe UI, Arial, sans-serif; margin: 2rem; background: #fafafa; color: #1a1a1a; }}
  h1 {{ font-size: 1.4rem; }}
  h2 {{ font-size: 1.1rem; margin-top: 2rem; }}
  .disclaimer {{ background: #eef2f7; border-left: 4px solid #4a6fa5; padding: 0.75rem 1rem; margin-bottom: 1.5rem; font-size: 0.95rem; }}
  table {{ border-collapse: collapse; width: 100%; margin-bottom: 1rem; font-size: 0.92rem; }}
  th, td {{ border: 1px solid #ccc; padding: 6px 10px; text-align: left; }}
  th {{ background: #333; color: #fff; }}
  footer {{ margin-top: 2.5rem; padding-top: 1rem; border-top: 1px solid #ccc; font-size: 0.85rem; color: #444; }}
  footer p {{ margin: 0.4rem 0; }}
</style>
</head>
<body>
<h1>CEROP Scoring Output</h1>
<div class="disclaimer">
  This is a <strong>local simulation</strong> of the CEROP scoring pipeline, run entirely
  offline against exported model artifacts. It is <strong>not a live production system</strong>
  \u2014 no data leaves this machine, and no scheduled or automated scoring is occurring.
  Generated {html.escape(timestamp)}.
</div>

<h2>Financial Layer (bankruptcy risk)</h2>
{render_table_html(financial_results, "Counterparty")}

<h2>Operations Layer (late-delivery risk)</h2>
{render_table_html(operations_results, "Order Ref")}

<footer>
  <p><strong>Thresholds used:</strong> Financial = {FINANCIAL_THRESHOLD:.2f} (Week 5 published configuration, default) &nbsp;|&nbsp;
  Operations = {OPERATIONS_THRESHOLD:.2f} (Week 6 calibrated threshold, not the 0.50 default)</p>
  <p><strong>Known reproducibility gap (financial model):</strong> {html.escape(DRIFT_NOTE)}</p>
</footer>
</body>
</html>
"""

    out_path = os.path.join(DEMO_DIR, "scored_output.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"\nWrote HTML output to: {out_path}")
    print(f"Financial rows scored: {len(financial_results)} / 8")
    print(f"Operations rows scored: {len(operations_results)} / 8")


if __name__ == "__main__":
    main()
