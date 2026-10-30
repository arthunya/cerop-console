"""
Step 2 scoring script — batch inference on the FULL held-out test sets.

Loads the two exported model .pkl files and scores them against the complete
financial and operations test sets (not a 5-row sample), recomputing
Accuracy/Precision/Recall/F1/ROC-AUC/PR-AUC and comparing each against the
metrics already reported in the Week 5 and Week 6 notebooks. Since these are
the exact fitted objects joblib-dumped from those notebook runs, scored
against the exact same test CSVs, the recomputed metrics are expected to
match the reported ones exactly (deterministic inference, no randomness).
"""
import sys
import joblib
import pandas as pd
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, confusion_matrix,
)

MODELS_DIR = r"<AIT506_PROJECT_FOLDER>\CEROP_Live_Demo\models"

FINANCIAL_X_TEST = r"<AIT506_PROJECT_FOLDER>\Week 5\GROUP\Ankit\data\financial_X_test_processed.csv"
FINANCIAL_Y_TEST = r"<AIT506_PROJECT_FOLDER>\Week 5\GROUP\Ankit\data\financial_y_test.csv"

OPERATIONS_X_TEST = r"<AIT506_PROJECT_FOLDER>\Week 6\Group\data\operations_X_test_processed_v2.csv"
OPERATIONS_Y_TEST = r"<AIT506_PROJECT_FOLDER>\Week 6\Group\data\operations_y_test_v2.csv"

# Metrics as reported in the notebooks' own executed output (same fitted
# objects, same test CSVs), at the default 0.5 threshold.
REPORTED_FINANCIAL = {
    "Accuracy": 0.9699, "Precision": 0.5349, "Recall": 0.5227,
    "F1-Score": 0.5287, "ROC-AUC": 0.9503, "PR-AUC": 0.4760,
}
REPORTED_OPERATIONS = {
    "Accuracy": 0.7337, "Precision": 0.8456, "Recall": 0.6290,
    "F1": 0.7214, "ROC-AUC": 0.8258, "PR-AUC": 0.8730,
}
TOLERANCE = 0.0005  # rounding tolerance vs. the 4-decimal reported values

overall_pass = True

def section(title):
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)

def check_metric(name, actual, expected, tol=TOLERANCE):
    global overall_pass
    diff = abs(actual - expected)
    status = "PASS" if diff <= tol else "FAIL"
    if status == "FAIL":
        overall_pass = False
    print(f"  {name:<10} actual={actual:.4f}  reported={expected:.4f}  diff={diff:.4f}  [{status}]")

# 1. Load models
section("1. LOADING MODELS")
try:
    xgb_model = joblib.load(MODELS_DIR + r"\cerop_financial_xgb.pkl")
    print("OK   cerop_financial_xgb.pkl ->", type(xgb_model).__name__)
except Exception as e:
    overall_pass = False
    xgb_model = None
    print("FAIL cerop_financial_xgb.pkl ->", repr(e))

try:
    rf_model = joblib.load(MODELS_DIR + r"\cerop_operations_rf.pkl")
    print("OK   cerop_operations_rf.pkl ->", type(rf_model).__name__)
except Exception as e:
    overall_pass = False
    rf_model = None
    print("FAIL cerop_operations_rf.pkl ->", repr(e))

# 2. Score financial XGBoost on the FULL financial test set
section("2. cerop_financial_xgb.pkl — FULL TEST SET SCORING")
if xgb_model is not None:
    X_test = pd.read_csv(FINANCIAL_X_TEST)
    y_test = pd.read_csv(FINANCIAL_Y_TEST).squeeze("columns")
    print(f"Test set size: {X_test.shape[0]} rows, {X_test.shape[1]} features "
          f"({int(y_test.sum())} bankrupt / {len(y_test)} total)")

    y_pred = xgb_model.predict(X_test)
    y_prob = xgb_model.predict_proba(X_test)[:, 1]

    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()
    print("\nConfusion matrix (rows=actual, cols=predicted):")
    print(cm)
    print(f"  TN={tn}  FP={fp}  FN={fn}  TP={tp}")

    actual_metrics = {
        "Accuracy": accuracy_score(y_test, y_pred),
        "Precision": precision_score(y_test, y_pred, zero_division=0),
        "Recall": recall_score(y_test, y_pred, zero_division=0),
        "F1-Score": f1_score(y_test, y_pred, zero_division=0),
        "ROC-AUC": roc_auc_score(y_test, y_prob),
        "PR-AUC": average_precision_score(y_test, y_prob),
    }
    print("\nRecomputed vs. reported (Week 5 notebook, Section 4.1):")
    for k in ["Accuracy", "Precision", "Recall", "F1-Score", "ROC-AUC", "PR-AUC"]:
        check_metric(k, actual_metrics[k], REPORTED_FINANCIAL[k])
else:
    overall_pass = False
    print("SKIPPED — model failed to load.")

# 3. Score operations RF on the FULL operations test set
section("3. cerop_operations_rf.pkl — FULL TEST SET SCORING (threshold=0.50)")
if rf_model is not None:
    X_test = pd.read_csv(OPERATIONS_X_TEST)
    y_test_df = pd.read_csv(OPERATIONS_Y_TEST)
    y_test = pd.to_numeric(y_test_df.iloc[:, 0]).astype(int)
    print(f"Test set size: {X_test.shape[0]} rows, {X_test.shape[1]} features "
          f"(late-delivery rate: {round(y_test.mean(), 4)})")

    y_prob = rf_model.predict_proba(X_test)[:, 1]
    y_pred = (y_prob >= 0.50).astype(int)

    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()
    print("\nConfusion matrix (rows=actual, cols=predicted):")
    print(cm)
    print(f"  TN={tn}  FP={fp}  FN={fn}  TP={tp}")

    actual_metrics = {
        "Accuracy": accuracy_score(y_test, y_pred),
        "Precision": precision_score(y_test, y_pred, zero_division=0),
        "Recall": recall_score(y_test, y_pred, zero_division=0),
        "F1": f1_score(y_test, y_pred, zero_division=0),
        "ROC-AUC": roc_auc_score(y_test, y_prob),
        "PR-AUC": average_precision_score(y_test, y_prob),
    }
    print("\nRecomputed vs. reported (Week 6 notebook, 'Tuned RF at 0.50' row):")
    for k in ["Accuracy", "Precision", "Recall", "F1", "ROC-AUC", "PR-AUC"]:
        check_metric(k, actual_metrics[k], REPORTED_OPERATIONS[k])
else:
    overall_pass = False
    print("SKIPPED — model failed to load.")

# Final verdict
section("FINAL RESULT")
print("PASS" if overall_pass else "FAIL")
sys.exit(0 if overall_pass else 1)
