"""
Builds the compact JSON files the showcase site, the deck and the console read.

Every number on those pages comes from here, and every number here comes from a file in
results/ (committed CSVs, the tables extracted from the Final Report, or the JSON written
by notebooks/07_export_web_artifacts.ipynb). Nothing is typed in.

Runs locally and in the GitHub Pages workflow:
    python site/build_data.py
Writes to site/assets/data/.
"""
import csv
import json
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RES = REPO / "results"
WEB = RES / "web"
OUT = REPO / "site" / "assets" / "data"


def rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def num(v):
    return float(str(v).replace(",", ""))


def pick(table, key, value):
    for r in table:
        if r[key] == value:
            return r
    raise KeyError(f"{value!r} not found in column {key!r}")


def load(name):
    with open(WEB / name, encoding="utf-8") as f:
        return json.load(f)


def write(name, obj, compact=False):
    with open(OUT / name, "w", encoding="utf-8") as f:
        if compact:
            json.dump(obj, f, separators=(",", ":"))
        else:
            json.dump(obj, f, indent=1)


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    # ---------- financial ----------
    w6f = rows(RES / "week6_financial_tuning_results.csv")
    w6f_cm = rows(RES / "week6_financial_confusion_matrices.csv")
    official = pick(w6f, "Model", "XGBoost - Week 5 published")
    official_cm = pick(w6f_cm, "Model", "XGBoost - Week 5 published")
    report_cmp = rows(RES / "reported" / "final_report_table_07.csv")
    rerun_cmp = rows(RES / "week5_financial_model_comparison.csv")
    fin_scores = load("financial_test_scores.json")
    before = pick(w6f, "Model", "XGBoost - Week 5 config")
    after = pick(w6f, "Model", "XGBoost - tuned")

    financial = {
        "official": {
            "source": "results/week6_financial_tuning_results.csv (row 'XGBoost - Week 5 published'); matches Final Report Table 7",
            "accuracy": num(official["Accuracy"]), "precision": num(official["Precision"]),
            "recall": num(official["Recall"]), "f1": num(official["F1-Score"]),
            "roc_auc": num(official["ROC-AUC"]), "pr_auc": num(official["PR-AUC"]),
            "tn": int(official_cm["TN"]), "fp": int(official_cm["FP"]),
            "fn": int(official_cm["FN"]), "tp": int(official_cm["TP"]),
        },
        "reproduced": {k: fin_scores["metrics_reproduced"][k] for k in
                       ["accuracy", "precision", "recall", "f1", "roc_auc", "pr_auc", "tn", "fp", "fn", "tp"]},
        "model_comparison_reported": {
            "source": "Final Report Table 7 (results/reported/final_report_table_07.csv)",
            "models": [{"model": r["Model"], "accuracy": num(r["Accuracy"]), "precision": num(r["Precision"]),
                        "recall": num(r["Recall"]), "f1": num(r["F1-Score"]), "roc_auc": num(r["ROC-AUC"])}
                       for r in report_cmp],
        },
        "model_comparison_rerun": {
            "source": "results/week5_financial_model_comparison.csv (2026-08-17 local re-run)",
            "models": [{"model": r["Model"], "precision": num(r["Precision"]), "recall": num(r["Recall"]),
                        "f1": num(r["F1-Score"]), "roc_auc": num(r["ROC-AUC"]), "pr_auc": num(r["PR-AUC"])}
                       for r in rerun_cmp],
        },
        "tuning": {
            "source": "results/week6_financial_tuning_results.csv",
            "before": {"label": before["Model"], "f1": num(before["F1-Score"]), "pr_auc": num(before["PR-AUC"])},
            "after": {"label": after["Model"], "f1": num(after["F1-Score"]), "pr_auc": num(after["PR-AUC"])},
            "fit_on": after["Fit on"],
            "bootstrap": json.loads((RES / "week6_financial_metrics.json").read_text(encoding="utf-8"))["diagnostics"]["bootstrap"],
        },
    }

    xgb_report = pick(report_cmp, "Model", "XGBoost")
    for k_csv, k in [("Precision", "precision"), ("Recall", "recall"), ("F1-Score", "f1"), ("ROC-AUC", "roc_auc")]:
        assert round(financial["official"][k], 3) == num(xgb_report[k_csv]), f"official {k} does not match the report"

    # ---------- operations ----------
    w6o = rows(RES / "week6_operations_tuning_results.csv")
    w6o_cm = rows(RES / "week6_operations_confusion_matrices.csv")
    colab = rows(RES / "week6_operations_colab_run" / "week6_operations_tuning_results.csv")
    colab_cm = rows(RES / "week6_operations_colab_run" / "week6_operations_confusion_matrices.csv")
    w5o = rows(RES / "week5_operations_model_comparison.csv")

    def ops_row(table, cm_table, name):
        r, c = pick(table, "Model", name), pick(cm_table, "Model", name)
        return {"model": name, "threshold": num(r["Threshold"]), "accuracy": num(r["Accuracy"]),
                "precision": num(r["Precision"]), "recall": num(r["Recall"]), "f1": num(r["F1"]),
                "roc_auc": num(r["ROC-AUC"]), "pr_auc": num(r["PR-AUC"]),
                "tn": int(c["TN"]), "fp": int(c["FP"]), "fn": int(c["FN"]), "tp": int(c["TP"])}

    names = ["Corrected Baseline RF", "Tuned RF at 0.50", "Tuned RF at Calibrated Threshold"]
    week6 = [ops_row(w6o, w6o_cm, n) for n in names]
    colab_rows = [ops_row(colab, colab_cm, n) for n in names]
    default, calibrated = week6[1], week6[2]
    operations = {
        "source": "results/week6_operations_tuning_results.csv + week6_operations_confusion_matrices.csv (notebook 05b as saved)",
        "week6": week6,
        "calibrated_threshold": calibrated["threshold"],
        "extra_caught": calibrated["tp"] - default["tp"],
        "extra_false_alarms": calibrated["fp"] - default["fp"],
        "late_in_test": calibrated["tp"] + calibrated["fn"],
        "colab_run": {
            "source": "results/week6_operations_colab_run/ (2026-08-08 Colab run, cited in the submitted reports)",
            "rows": colab_rows,
            "extra_caught": colab_rows[2]["tp"] - colab_rows[1]["tp"],
        },
        "week5_comparison": {
            "source": "results/week5_operations_model_comparison.csv (35-feature data, before the Order Status leakage fix)",
            "models": [{"model": r["Model"], "precision": num(r["Precision"]), "recall": num(r["Recall"]),
                        "f1": num(r["F1-Score"]), "roc_auc": num(r["ROC-AUC"]), "pr_auc": num(r["PR-AUC"])} for r in w5o],
        },
        "validation_curve": [{"t": num(r["Threshold"]), "precision": num(r["Precision"]),
                              "recall": num(r["Recall"]), "f1": num(r["F1"])}
                             for r in rows(RES / "week6_operations_threshold_results.csv")],
    }

    # Test-set threshold curve from the exported model's real predictions, one point per slider step.
    ops = load("operations_test_scores.json")
    p, y = ops["proba"], ops["label"]
    pos = sum(y)
    curve = []
    for step in range(5, 96):
        t = round(step / 100, 2)
        tp = sum(1 for a, b in zip(p, y) if a >= t and b == 1)
        fp = sum(1 for a, b in zip(p, y) if a >= t and b == 0)
        fn, tn = pos - tp, len(y) - pos - fp
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / pos
        f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
        curve.append({"t": t, "tp": tp, "fp": fp, "fn": fn, "tn": tn,
                      "precision": round(prec, 6), "recall": round(rec, 6), "f1": round(f1, 6)})
    at_cal = next(c for c in curve if c["t"] == calibrated["threshold"])
    assert (at_cal["tn"], at_cal["fp"], at_cal["fn"], at_cal["tp"]) == \
        (calibrated["tn"], calibrated["fp"], calibrated["fn"], calibrated["tp"]), "explorer does not reproduce Week 6"
    at_def = next(c for c in curve if c["t"] == 0.5)
    assert (at_def["tp"], at_def["fp"]) == (default["tp"], default["fp"])
    bins = 20
    hist = {"late": [0] * bins, "on_time": [0] * bins}
    for a, b in zip(p, y):
        k = min(int(a * bins), bins - 1)
        hist["late" if b == 1 else "on_time"][k] += 1
    write("ops_threshold_curve.json", {"source": "results/web/operations_test_scores.json (34,393 test orders scored by the exported Random Forest)",
                                       "n": len(y), "positives": pos, "curve": curve,
                                       "histogram": {"bins": bins, **hist}})

    # Financial score histogram (test set) for the console
    fp_, fy = fin_scores["proba"], fin_scores["label"]
    fh = {"bankrupt": [0] * bins, "healthy": [0] * bins}
    for a, b in zip(fp_, fy):
        fh["bankrupt" if b == 1 else "healthy"][min(int(a * bins), bins - 1)] += 1

    facts = load("dataset_facts.json")
    report_rows = pick(rows(RES / "reported" / "final_report_table_05.csv"), "Layer", "Operations (DataCo)")
    facts["operations"]["rows_before_cleaning"] = int(num(report_rows["Rows in"]))
    facts["operations"]["rows_before_cleaning_source"] = "Final Report Table 5"
    assert int(num(report_rows["Rows after cleaning"])) == facts["operations"]["orders"]


    # ---------- comparison: final report vs final presentation vs this repo ----------
    deck = {(r["layer"], r["metric"]): num(r["value"]) for r in rows(RES / "reported" / "final_presentation_figures.csv")}
    rep_ops = pick(rows(RES / "reported" / "final_report_table_13.csv"), "Model", "Tuned RF at 0.39 (calibrated)")
    rep_cm = pick(rows(RES / "reported" / "final_report_table_14.csv"), "Model", "Tuned RF at 0.39 (calibrated)")
    rep_fin = pick(report_cmp, "Model", "XGBoost")
    rep_data = rows(RES / "reported" / "final_report_table_05.csv")
    rep_f = pick(rep_data, "Layer", "Financial (Taiwan)")
    rep_o = pick(rep_data, "Layer", "Operations (DataCo)")
    rf, ro = financial["official"], operations["week6"][2]
    rr = financial["reproduced"]

    def entry(name, key, **kw):
        return dict(source=name, key=key, **kw)

    comparison = {
        "financial": [
            entry("Final report", "report", precision=num(rep_fin["Precision"]), recall=num(rep_fin["Recall"]), f1=num(rep_fin["F1-Score"]),
                  tp=rf["tp"], fp=rf["fp"], fn=rf["fn"], tn=rf["tn"], threshold=0.5,
                  note="XGBoost refit on all 5,455 training firms (Week 5 published row)"),
            entry("Final presentation", "deck", precision=deck[("financial", "precision")], recall=deck[("financial", "recall")], f1=deck[("financial", "f1")],
                  tp=int(deck[("financial", "tp")]), fp=int(deck[("financial", "fp")]), fn=int(deck[("financial", "fn")]), tn=int(deck[("financial", "tn")]), threshold=0.5,
                  note="Same model settings, refit on the 4,364-firm tuning split (Week 6 'before' row)"),
            entry("This repo (re-run)", "repo", precision=rr["precision"], recall=rr["recall"], f1=rr["f1"],
                  tp=rr["tp"], fp=rr["fp"], fn=rr["fn"], tn=rr["tn"], threshold=0.5,
                  note="Exported model re-evaluated locally; library versions differ from Colab"),
        ],
        "operations": [
            entry("Final report", "report", precision=num(rep_ops["Precision"]), recall=num(rep_ops["Recall"]), f1=num(rep_ops["F1"]),
                  tp=int(num(rep_cm["TP"])), fp=int(num(rep_cm["FP"])), fn=int(num(rep_cm["FN"])), tn=int(num(rep_cm["TN"])), threshold=num(rep_ops["Threshold"]),
                  note="Team's Colab run; threshold 0.39"),
            entry("Final presentation", "deck", precision=deck[("operations", "precision")], recall=deck[("operations", "recall")], f1=deck[("operations", "f1")],
                  tp=int(deck[("operations", "tp")]), fp=int(deck[("operations", "fp")]), fn=int(deck[("operations", "fn")]), tn=int(deck[("operations", "tn")]), threshold=deck[("operations", "threshold")],
                  note="Same Colab run as the report"),
            entry("This repo (re-run)", "repo", precision=ro["precision"], recall=ro["recall"], f1=ro["f1"],
                  tp=ro["tp"], fp=ro["fp"], fn=ro["fn"], tn=ro["tn"], threshold=ro["threshold"],
                  note="Saved notebook re-run and the exported model; threshold 0.40"),
        ],
        "data": [
            {"item": "Financial firms: train / test", "report": f"{int(num(rep_f['Train'])):,} / {int(num(rep_f['Test'])):,}", "deck": f"{int(deck[('financial', 'train')]):,} / {int(deck[('financial', 'test')]):,}",
             "repo": f"{facts['financial']['train']:,} / {facts['financial']['test']:,}"},
            {"item": "Financial features", "report": str(int(num(rep_f["Features"]))), "deck": str(int(deck[("financial", "features")])), "repo": str(facts["financial"]["features"])},
            {"item": "Operations orders after cleaning", "report": f"{int(num(rep_o['Rows after cleaning'])):,}", "deck": f"{int(deck[('operations', 'rows_after_cleaning')]):,}", "repo": f"{facts['operations']['orders']:,}"},
            {"item": "Operations orders: train / test", "report": f"{int(num(rep_o['Train'])):,} / {int(num(rep_o['Test'])):,}", "deck": f"{int(deck[('operations', 'train')]):,} / {int(deck[('operations', 'test')]):,}",
             "repo": f"{facts['operations']['train']:,} / {facts['operations']['test']:,}"},
            {"item": "Operations features", "report": f"{int(num(rep_o['Features']))} (Week 4)", "deck": f"{int(deck[('operations', 'features')])} (Week 4)",
             "repo": f"{facts['operations']['processed_features']} processed, {facts['operations']['model_features']} used by the final model"},
        ],
    }
    for row in comparison["data"]:
        same = row["report"] == row["deck"] == row["repo"]
        row["mark"] = "same" if same else "see note"
    write("comparison.json", comparison)

    write("metrics.json", {"financial": financial, "operations": operations, "facts": facts,
                           "financial_histogram": {"bins": bins, **fh}})

    for name in ["financial_shap_cases.json", "operations_shap_cases.json"]:
        shutil.copy(WEB / name, OUT / name)

    # What-if: the model plus the full raw rows of the sample firms (not all 1,364)
    whatif = load("financial_whatif_model.json")
    parity_path = WEB / "financial_whatif_parity.csv"
    parity = rows(parity_path) if parity_path.exists() else []
    passed = bool(parity) and all(r["pass"] == "true" for r in parity)
    if passed:
        test_raw = load("financial_test_raw.json")
        cases = load("financial_shap_cases.json")["cases"]
        whatif["cases"] = {c["id"]: test_raw["rows"][c["row"]] for c in cases}
        whatif["parity"] = {"rows": len(parity), "max_abs_diff": max(num(r["abs_diff"]) for r in parity)}
        write("financial_whatif.json", whatif, compact=True)
    else:
        (OUT / "financial_whatif.json").unlink(missing_ok=True)
    print(f"wrote {len(list(OUT.glob('*.json')))} files to site/assets/data (what-if {'on' if passed else 'off'})")


if __name__ == "__main__":
    main()
