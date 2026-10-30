"""
Verification script for the four CEROP .pkl exports.
Checks:
  1. All four .pkl files load without error.
  2. cerop_financial_xgb.pkl and cerop_operations_rf.pkl produce predictions
     on 5 real held-out test rows.
  3. cerop_financial_preprocessor.pkl transforms real financial test rows into
     exactly 85 output features (Week 4 report Table 4).
  4. cerop_operations_preprocessor.pkl's fitted output schema has exactly 35
     features (Week 4 report Table 4).
If either feature-count check fails, the script stops that check and reports
the actual count instead of treating it as a pass.
"""
import sys
import joblib
import pandas as pd

MODELS_DIR = r"<AIT506_PROJECT_FOLDER>\CEROP_Live_Demo\models"
FINANCIAL_TEST_CSV = r"<AIT506_PROJECT_FOLDER>\Week 5\GROUP\Ankit\data\financial_X_test_processed.csv"
OPERATIONS_TEST_CSV = r"<AIT506_PROJECT_FOLDER>\Week 6\Group\data\operations_X_test_processed_v2.csv"

EXPECTED_FINANCIAL_FEATURES = 85
EXPECTED_OPERATIONS_FEATURES = 35

overall_pass = True

def section(title):
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)

# 1. Load all four .pkl files
section("1. LOADING ALL FOUR .pkl FILES")
paths = {
    "cerop_financial_xgb.pkl": None,
    "cerop_operations_rf.pkl": None,
    "cerop_financial_preprocessor.pkl": None,
    "cerop_operations_preprocessor.pkl": None,
}
for name in paths:
    full_path = MODELS_DIR + "\\" + name
    try:
        obj = joblib.load(full_path)
        paths[name] = obj
        print(f"OK   {name:<40} -> {type(obj).__name__}")
    except Exception as e:
        overall_pass = False
        print(f"FAIL {name:<40} -> could not load: {e!r}")

xgb_model = paths["cerop_financial_xgb.pkl"]
rf_model = paths["cerop_operations_rf.pkl"]
financial_preprocessor = paths["cerop_financial_preprocessor.pkl"]
operations_preprocessor = paths["cerop_operations_preprocessor.pkl"]

# 2. Financial XGBoost: 5-row prediction on real test data
section("2. cerop_financial_xgb.pkl — 5-ROW PREDICTION (real test rows)")
if xgb_model is not None:
    fin_test = pd.read_csv(FINANCIAL_TEST_CSV)
    fin_sample = fin_test.head(5)
    fin_pred = xgb_model.predict(fin_sample)
    fin_prob = xgb_model.predict_proba(fin_sample)[:, 1]
    out = pd.DataFrame({
        "row": range(5),
        "predicted_class": fin_pred,
        "predicted_prob_bankrupt": fin_prob.round(6),
    })
    print(f"Source: {FINANCIAL_TEST_CSV}")
    print(out.to_string(index=False))
else:
    overall_pass = False
    print("SKIPPED — model failed to load.")

# 3. Operations RF: 5-row prediction on real test data
section("3. cerop_operations_rf.pkl — 5-ROW PREDICTION (real test rows)")
if rf_model is not None:
    ops_test = pd.read_csv(OPERATIONS_TEST_CSV)
    ops_sample = ops_test.head(5)
    ops_pred = rf_model.predict(ops_sample)
    ops_prob = rf_model.predict_proba(ops_sample)[:, 1]
    out = pd.DataFrame({
        "row": range(5),
        "predicted_class": ops_pred,
        "predicted_prob_late": ops_prob.round(6),
    })
    print(f"Source: {OPERATIONS_TEST_CSV}")
    print(out.to_string(index=False))
else:
    overall_pass = False
    print("SKIPPED — model failed to load.")

# 4. Financial preprocessor feature-count check
section("4. cerop_financial_preprocessor.pkl — FEATURE COUNT CHECK")
if financial_preprocessor is not None:
    fin_test = pd.read_csv(FINANCIAL_TEST_CSV)
    fin_sample = fin_test.head(5)
    transformed = financial_preprocessor.transform(fin_sample)
    actual_count = transformed.shape[1]
    n_features_in = getattr(financial_preprocessor, "n_features_in_", None)
    print(f"n_features_in_ (fit-time):       {n_features_in}")
    print(f"transform() output feature count: {actual_count}")
    print(f"Expected (Week 4 report Table 4): {EXPECTED_FINANCIAL_FEATURES}")
    if actual_count == EXPECTED_FINANCIAL_FEATURES:
        print(f"PASS — matches published count of {EXPECTED_FINANCIAL_FEATURES}.")
    else:
        overall_pass = False
        print(f"STOP — MISMATCH. Preprocessor actually produces {actual_count} "
              f"features, not the published {EXPECTED_FINANCIAL_FEATURES}.")
else:
    overall_pass = False
    print("SKIPPED — preprocessor failed to load.")

# 5. Operations preprocessor feature-count check
section("5. cerop_operations_preprocessor.pkl — FEATURE COUNT CHECK")
if operations_preprocessor is not None:
    feature_names = operations_preprocessor.get_feature_names_out()
    actual_count = len(feature_names)
    print(f"get_feature_names_out() length:   {actual_count}")
    print(f"Expected (Week 4 report Table 4): {EXPECTED_OPERATIONS_FEATURES}")
    print(f"Feature names: {list(feature_names)}")
    if actual_count == EXPECTED_OPERATIONS_FEATURES:
        print(f"PASS — matches published count of {EXPECTED_OPERATIONS_FEATURES}.")
    else:
        overall_pass = False
        print(f"STOP — MISMATCH. Preprocessor actually produces {actual_count} "
              f"features, not the published {EXPECTED_OPERATIONS_FEATURES}.")
else:
    overall_pass = False
    print("SKIPPED — preprocessor failed to load.")

# Known drift note
section("KNOWN DRIFT NOTE — cerop_financial_xgb.pkl")
print(
    "Live-redeployed model shows F1=0.5333 vs F1=0.5290 reported in Week 5 — a 0.004\n"
    "difference attributed to xgboost/scikit-learn version drift between the original\n"
    "Colab environment and this local re-execution. Same code, data, and random seed;\n"
    "not a modeling change.\n"
    "See CEROP_Live_Demo_Setup.md for the full investigation (ruled out thread\n"
    "nondeterminism and data/seed differences). Final Report, slides, and dashboard were\n"
    "not edited; F1=0.529 remains the official reported result.\n"
)
try:
    import xgboost
    import sklearn
    print(f"This run's library versions — xgboost: {xgboost.__version__}, "
          f"scikit-learn: {sklearn.__version__}")
except ImportError:
    pass

# Final verdict
section("FINAL RESULT")
if overall_pass:
    print("PASS")
else:
    print("FAIL")

sys.exit(0 if overall_pass else 1)
