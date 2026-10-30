"""
Runs real SHAP TreeExplainer explanations for both CEROP models against the
8+8 live-demo cases, exports per-case top-4 driver CSVs, and prints the
required reconciliation + sanity checks before anything is trusted.

Financial (XGBoost): plain TreeExplainer defaults to margin/log-odds space
(confirmed empirically — base+sum(shap) only matches predict_proba() after
sigmoid, not directly). To get genuinely additive probability-point
contributions (not a post-hoc sigmoid applied per-feature, which would be
mathematically invalid), uses model_output="probability" with the
interventional method and a 100-row background sample from the training set.

That path requires bypassing a shap guard that blocks XGBoost models with
enable_categorical=True — confirmed this flag is a version-default artifact
(none of the 85 financial features are actually categorical) and flipping it
in-memory does not change predict_proba() output at all (bit-identical,
verified). Never touches or re-saves the .pkl file — models\ stays read-only.

Operations (RandomForest): plain TreeExplainer already reconciles directly
in probability space (RF's leaf outputs are literal class-probability
fractions, not boosted log-odds) — confirmed empirically, no conversion
needed.
"""
import shap
import joblib
import pandas as pd
import numpy as np

MODELS_DIR = r"<AIT506_PROJECT_FOLDER>\CEROP_Live_Demo\models"
DEMO_DIR = r"<AIT506_PROJECT_FOLDER>\CEROP_Live_Demo\demo_data"
FIN_TRAIN = r"<AIT506_PROJECT_FOLDER>\Week 5\GROUP\Ankit\data\financial_X_train_processed.csv"
OPS_TRAIN = r"<AIT506_PROJECT_FOLDER>\Week 6\Group\data\operations_X_train_processed_v2.csv"

TOP_N = 4

# One-hot dummy columns get grouped back into their parent categorical
# feature (summing SHAP contributions) before ranking for top-N — otherwise
# a single real driver like "Shipping Mode" gets split across 2-3 separate
# rows (one per dummy column), which both understates its true rank and
# produces misleading labels like "Shipping Mode (Standard Class)" on a row
# whose actual mode isn't Standard Class (the dummy's SHAP credit there
# really means "this order is NOT Standard Class", not "this order IS").
ONE_HOT_GROUPS = ["Type", "Customer Country", "Customer Segment", "Order Status", "Shipping Mode"]


def group_operations_shap(X, shap_vals):
    """Collapse low_cardinality__<Group>_<Category> dummy columns back into
    a single <Group> column (summed SHAP), leaving all other columns as-is."""
    grouped_names = []
    grouped_cols = []
    handled = set()
    for i, col in enumerate(X.columns):
        if i in handled:
            continue
        matched_group = None
        for g in ONE_HOT_GROUPS:
            if col.startswith(f"low_cardinality__{g}_"):
                matched_group = g
                break
        if matched_group:
            idxs = [j for j, c in enumerate(X.columns) if c.startswith(f"low_cardinality__{matched_group}_")]
            grouped_names.append(matched_group)
            grouped_cols.append(idxs)
            handled.update(idxs)
        else:
            grouped_names.append(col)
            grouped_cols.append([i])
            handled.add(i)
    grouped_shap = np.zeros((shap_vals.shape[0], len(grouped_names)))
    for gi, idxs in enumerate(grouped_cols):
        grouped_shap[:, gi] = shap_vals[:, idxs].sum(axis=1)
    return pd.DataFrame(grouped_shap, columns=grouped_names)


def section(title):
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def top_n_rows(case_ids, labels, X, shap_vals, base_val, proba, n=TOP_N):
    """Build the per-case CSV rows: top-N |shap| features + base/final."""
    rows = []
    for i, cid in enumerate(case_ids):
        feat_contribs = list(zip(X.columns, shap_vals[i]))
        feat_contribs.sort(key=lambda x: abs(x[1]), reverse=True)
        top = feat_contribs[:n]
        row = {"case_id": cid, "base_rate": round(float(base_val), 6)}
        for j in range(n):
            name, val = top[j]
            row[f"feature_{j+1}_name"] = name
            row[f"feature_{j+1}_contribution"] = round(float(val), 6)
        row["final_score"] = round(float(proba[i]), 6)
        rows.append(row)
    return rows


# ============================================================================
# FINANCIAL
# ============================================================================
section("FINANCIAL — computing SHAP (XGBoost, probability space)")

xgb_model = joblib.load(MODELS_DIR + r"\cerop_financial_xgb.pkl")
xgb_model.enable_categorical = False  # in-memory only; verified no effect on predict_proba
fin_pre = joblib.load(MODELS_DIR + r"\cerop_financial_preprocessor.pkl")
fin_cases = pd.read_csv(DEMO_DIR + r"\financial_new_cases.csv")

X_raw = fin_cases.drop(columns=["case_id", "counterparty_name"])
X_t = fin_pre.transform(X_raw)
X_fin = pd.DataFrame(X_t, columns=fin_pre.get_feature_names_out())
X_fin = X_fin[list(xgb_model.feature_names_in_)]

fin_background = pd.read_csv(FIN_TRAIN).sample(n=100, random_state=42)
fin_background = fin_background[list(xgb_model.feature_names_in_)]

fin_explainer = shap.TreeExplainer(
    xgb_model, data=fin_background,
    feature_perturbation="interventional",
    model_output="probability",
)
fin_shap = fin_explainer.shap_values(X_fin)
fin_base = float(fin_explainer.expected_value)
fin_proba = xgb_model.predict_proba(X_fin)[:, 1]

print(f"base_value (financial): {fin_base:.6f}")
print(f"shap_values shape: {fin_shap.shape}")

fin_rows = top_n_rows(
    fin_cases["case_id"].tolist(), fin_cases["counterparty_name"].tolist(),
    X_fin, fin_shap, fin_base, fin_proba,
)
fin_out = pd.DataFrame(fin_rows)
fin_out_path = DEMO_DIR + r"\financial_shap_explanations.csv"
fin_out.to_csv(fin_out_path, index=False)
print(f"Saved: {fin_out_path}")
print(fin_out.to_string(index=False))


# ============================================================================
# OPERATIONS
# ============================================================================
section("OPERATIONS — computing SHAP (RandomForest, already probability space)")

rf_model = joblib.load(MODELS_DIR + r"\cerop_operations_rf.pkl")
ops_pre = joblib.load(MODELS_DIR + r"\cerop_operations_preprocessor.pkl")
ops_cases = pd.read_csv(DEMO_DIR + r"\operations_new_cases.csv")

X_raw_o = ops_cases.drop(columns=["case_id", "order_ref"])
X_t_o_full = ops_pre.transform(X_raw_o)
X_ops_full = pd.DataFrame(X_t_o_full, columns=ops_pre.get_feature_names_out())
X_ops = X_ops_full[list(rf_model.feature_names_in_)]  # drop the 8 leaky Order Status cols

ops_explainer = shap.TreeExplainer(rf_model)
ops_shap_raw = ops_explainer.shap_values(X_ops)
ops_base_raw = ops_explainer.expected_value

# RF binary output: (n_samples, n_features, 2) — take the positive class
if isinstance(ops_shap_raw, list):
    ops_shap = ops_shap_raw[1]
    ops_base = float(ops_base_raw[1]) if hasattr(ops_base_raw, "__len__") else float(ops_base_raw)
elif np.ndim(ops_shap_raw) == 3:
    ops_shap = ops_shap_raw[:, :, 1]
    ops_base = float(ops_base_raw[1]) if hasattr(ops_base_raw, "__len__") else float(ops_base_raw)
else:
    ops_shap = ops_shap_raw
    ops_base = float(ops_base_raw)

ops_proba = rf_model.predict_proba(X_ops)[:, 1]

print(f"base_value (operations): {ops_base:.6f}")
print(f"shap_values shape: {ops_shap.shape}")

# Group one-hot dummy columns (Shipping Mode, Type, etc.) back into their
# parent categorical feature before ranking for top-N — see ONE_HOT_GROUPS
# comment above for why. Sum-of-all-contributions is unchanged by grouping
# (pure re-bucketing), so this does not affect the Step 2 reconciliation
# check above, which is computed from the ungrouped ops_shap.
ops_shap_grouped = group_operations_shap(X_ops, ops_shap)
print(f"\nGrouped from {X_ops.shape[1]} columns down to {ops_shap_grouped.shape[1]} "
      f"features (one-hot dummies combined): {list(ops_shap_grouped.columns)}")

ops_rows = top_n_rows(
    ops_cases["case_id"].tolist(), ops_cases["order_ref"].tolist(),
    ops_shap_grouped, ops_shap_grouped.values, ops_base, ops_proba,
)
ops_out = pd.DataFrame(ops_rows)
ops_out_path = DEMO_DIR + r"\operations_shap_explanations.csv"
ops_out.to_csv(ops_out_path, index=False)
print(f"Saved: {ops_out_path}")
print(ops_out.to_string(index=False))


# ============================================================================
# STEP 2 — RECONCILIATION CHECK (full feature vector, not just top 4)
# ============================================================================
section("STEP 2 — RECONCILIATION CHECK (full SHAP vector vs. predict_proba)")

def check_case(label, case_ids, target_id, X, shap_vals, base_val, proba):
    idx = case_ids.index(target_id)
    full_sum = base_val + np.sum(shap_vals[idx])
    actual = proba[idx]
    diff = abs(full_sum - actual)
    status = "PASS" if diff < 1e-6 else "FAIL"
    print(f"[{label}] {target_id}: base({base_val:.6f}) + sum(ALL {shap_vals.shape[1]} shap) "
          f"= {full_sum:.8f}  |  predict_proba = {actual:.8f}  |  diff = {diff:.2e}  [{status}]")
    return status == "PASS"

fin_ids = fin_cases["case_id"].tolist()
ops_ids = ops_cases["case_id"].tolist()

# Financial: FIN-006 (HIGH, 0.996) + FIN-001 (CLEAR, ~0.00002)
r1 = check_case("FINANCIAL / HIGH ", fin_ids, "FIN-006", X_fin, fin_shap, fin_base, fin_proba)
r2 = check_case("FINANCIAL / CLEAR", fin_ids, "FIN-001", X_fin, fin_shap, fin_base, fin_proba)

# Operations: OPS-008 (HIGH, 0.900) + OPS-001 (WATCH, 0.339)
r3 = check_case("OPERATIONS / HIGH ", ops_ids, "OPS-008", X_ops, ops_shap, ops_base, ops_proba)
r4 = check_case("OPERATIONS / WATCH", ops_ids, "OPS-001", X_ops, ops_shap, ops_base, ops_proba)

all_pass = r1 and r2 and r3 and r4
print(f"\nALL 4 RECONCILIATION CHECKS PASS (< 1e-6)? {all_pass}")
if not all_pass:
    print("!!! STOPPING — do not trust these numbers, do not proceed to Step 3 !!!")


# ============================================================================
# SANITY CHECK — Shipping Mode should be a large positive contributor
# for ORD-88360 (First Class) and ORD-88302 (Second Class)
# ============================================================================
section("SANITY CHECK — Shipping Mode contribution for ORD-88360 / ORD-88302")

ship_cols = [c for c in X_ops.columns if "Shipping Mode" in c]
print("Shipping-mode-related columns in the model's 27-feature input:", ship_cols)

ref_to_case = dict(zip(ops_cases["order_ref"], ops_cases["case_id"]))
for target_ref in ["ORD-88360", "ORD-88302"]:
    target = ref_to_case[target_ref]
    idx = ops_ids.index(target)
    print(f"\n(order_ref {target_ref} = case_id {target})")
    print(f"\n{target} — full driver ranking (all {X_ops.shape[1]} features, sorted by |contribution|):")
    contribs = list(zip(X_ops.columns, ops_shap[idx]))
    contribs.sort(key=lambda x: abs(x[1]), reverse=True)
    for rank, (name, val) in enumerate(contribs[:8], 1):
        flag = "  <-- shipping mode" if "Shipping Mode" in name else ""
        print(f"  #{rank}: {name:<45} {val:+.6f}{flag}")
    ship_contribs = [(n, v) for n, v in contribs if "Shipping Mode" in n]
    if ship_contribs:
        top_ship = max(ship_contribs, key=lambda x: x[1])
        print(f"  -> Largest shipping-mode contribution: {top_ship[0]} = {top_ship[1]:+.6f}")
    else:
        print("  -> No shipping-mode column found with nonzero contribution for this row "
              "(expected for Standard Class rows, since that's the reference/dropped category — "
              "check whether that's the case here).")
