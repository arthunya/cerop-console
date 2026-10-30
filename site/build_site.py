"""
Renders the showcase site into _site/ (the folder GitHub Pages deploys).

Pages under site/ are plain HTML with two kinds of placeholder:
  {{> header}}            a partial from site/_partials/header.html
  {{ fin.official.f1 | f3 }}   a value from site/assets/data/metrics.json, formatted
So no number on the site is typed by hand: each one is looked up in the JSON that
site/build_data.py builds from results/. An unknown placeholder stops the build.

    python site/build_data.py && python site/build_site.py [--out _site] [--console console/dist]
"""
import argparse
import csv
import json
import re
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SITE = REPO / "site"
DATA = SITE / "assets" / "data"

FORMATS = {
    "f2": lambda v: f"{v:.2f}",
    "f3": lambda v: f"{v:.3f}",
    "f4": lambda v: f"{v:.4f}",
    "t2": lambda v: f"{v:.2f}",
    "pct0": lambda v: f"{v * 100:.0f}%",
    "pct1": lambda v: f"{v * 100:.1f}%",
    "int": lambda v: f"{int(round(v)):,}",
    "plus": lambda v: f"+{int(round(v)):,}",
    "raw": lambda v: str(v),
}


def context():
    m = json.loads((DATA / "metrics.json").read_text(encoding="utf-8"))
    fin, ops = m["financial"], m["operations"]
    rep = {r["model"]: r for r in fin["model_comparison_reported"]["models"]}
    rerun = {r["model"]: r for r in fin["model_comparison_rerun"]["models"]}
    w5o = {r["model"]: r for r in ops["week5_comparison"]["models"]}
    best_val = max(ops["validation_curve"], key=lambda r: r["f1"])
    fs = json.loads((DATA / "financial_shap_cases.json").read_text(encoding="utf-8"))
    os_ = json.loads((DATA / "operations_shap_cases.json").read_text(encoding="utf-8"))
    report = {}
    for p in sorted((REPO / "results" / "reported").glob("final_report_table_*.csv")):
        with open(p, newline="", encoding="utf-8") as f:
            table = list(csv.reader(f))
        def cell(v):
            try:
                return float(v.replace(",", ""))
            except ValueError:
                return v
        report["t" + p.stem[-2:]] = {f"r{i}": {f"c{j}": cell(v) for j, v in enumerate(row)} for i, row in enumerate(table)}
    return {
        "report": report,
        "fin": fin, "ops": ops, "facts": m["facts"],
        "finrep": {"logreg": rep["Logistic Regression"], "rf": rep["Random Forest"], "xgb": rep["XGBoost"]},
        "finrerun": {"rf": rerun["Random Forest"], "xgb": rerun["XGBoost"]},
        "opsBase": ops["week6"][0], "opsDef": ops["week6"][1], "opsCal": ops["week6"][2],
        "colabDef": ops["colab_run"]["rows"][1], "colabCal": ops["colab_run"]["rows"][2],
        "w5o": {"lr": w5o["Logistic Regression"], "rf": w5o["Random Forest"], "svm": w5o["SVM (linear)"]},
        "val": best_val,
        "shap": {"fin_n": len(fs["cases"]), "ops_n": len(os_["cases"]), "fin_base": fs["base_value"],
                 "ops_base": os_["base_value"], "fin_top": fs["top_n"], "ops_groups": os_["grouped_feature_count"]},
        "derived": {
            "fin_negatives_test": m["facts"]["financial"]["test"] - m["facts"]["financial"]["test_bankrupt"],
            "always_no_accuracy": 1 - m["facts"]["financial"]["test_bankrupt"] / m["facts"]["financial"]["test"],
            "ops_rows_removed": m["facts"]["operations"]["rows_before_cleaning"] - m["facts"]["operations"]["orders"],
            "fin_flagged": fin["official"]["tp"] + fin["official"]["fp"],
            "ops_leaky_cols": m["facts"]["operations"]["processed_features"] - m["facts"]["operations"]["model_features"],
            "ops_on_time_test": m["facts"]["operations"]["test"] - m["facts"]["operations"]["test_late"],
        },
    }


def lookup(ctx, path):
    cur = ctx
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            raise KeyError(path)
    return cur


VALUE = re.compile(r"\{\{\s*([A-Za-z0-9_.]+)\s*(?:\|\s*([a-z0-9]+)\s*)?\}\}")
PARTIAL = re.compile(r"\{\{>\s*([a-z0-9_-]+)\s*\}\}")


def render(text, ctx, root, page):
    for _ in range(3):  # partials may contain partials
        text = PARTIAL.sub(lambda mt: (SITE / "_partials" / f"{mt.group(1)}.html").read_text(encoding="utf-8"), text)
    text = text.replace("{{root}}", root).replace("{{page}}", page)

    def sub(mt):
        path, fmt = mt.group(1), mt.group(2) or "raw"
        try:
            v = lookup(ctx, path)
        except KeyError:
            raise SystemExit(f"{page}: unknown placeholder {{{{ {path} }}}}")
        if fmt not in FORMATS:
            raise SystemExit(f"{page}: unknown format '{fmt}'")
        return FORMATS[fmt](v)

    text = VALUE.sub(sub, text)
    if "{{" in text:
        raise SystemExit(f"{page}: unrendered placeholder left near: {text[text.index('{{'):text.index('{{') + 60]!r}")
    return text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(REPO / "_site"))
    ap.add_argument("--console", default=str(REPO / "console" / "dist"))
    a = ap.parse_args()
    out = Path(a.out)
    if out.exists():  # clear old files; folders stay (Windows may hold a lock on them)
        for f in sorted(out.rglob("*"), reverse=True):
            if f.is_file():
                f.unlink()
    out.mkdir(parents=True, exist_ok=True)
    ctx = context()

    pages = [p for p in SITE.rglob("*.html") if "_partials" not in p.parts]
    for p in pages:
        rel = p.relative_to(SITE)
        depth = len(rel.parts) - 1
        root = "../" * depth if depth else "./"
        html = render(p.read_text(encoding="utf-8"), ctx, root, rel.as_posix())
        dest = out / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(html, encoding="utf-8")
    for f in (SITE / "deck").glob("*"):
        if f.suffix in (".css", ".js"):
            shutil.copy(f, out / "deck" / f.name)
    shutil.copytree(SITE / "assets", out / "assets", dirs_exist_ok=True)
    shutil.copytree(REPO / "reports", out / "reports", dirs_exist_ok=True)
    console = Path(a.console)
    if (console / "index.html").exists():
        shutil.copytree(console, out / "console", dirs_exist_ok=True)
    (out / ".nojekyll").write_text("")
    print(f"rendered {len(pages)} pages to {out} (console {'included' if (out / 'console').exists() else 'not built'})")


if __name__ == "__main__":
    main()
