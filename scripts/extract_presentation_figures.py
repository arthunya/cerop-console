"""
Reads the headline figures from the team's final class presentation (.pptx) so the
report-vs-presentation-vs-repo comparison on the site is built from code, not retyped.

Only numbers are extracted, each tagged with the slide it came from. The .pptx itself is
never copied into this repo.

Usage:
    python scripts/extract_presentation_figures.py "<path to CEROP_Presentation_Slides_Final.pptx>"
Writes results/reported/final_presentation_figures.csv
"""
import csv
import hashlib
import html
import re
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "results" / "reported" / "final_presentation_figures.csv"


def slide_texts(path):
    z = zipfile.ZipFile(path)
    names = sorted((n for n in z.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", n)),
                   key=lambda n: int(re.findall(r"\d+", n)[0]))
    out = {}
    for n in names:
        xml = z.read(n).decode("utf-8", "ignore")
        parts = [html.unescape(t).strip() for t in re.findall(r"<a:t>([^<]*)</a:t>", xml)]
        out[int(re.findall(r"\d+", n)[0])] = " | ".join(p for p in parts if p)
    return out


def num(s):
    return float(s.replace(",", ""))


def counts(text):
    m = re.search(r"([\d,]+) \| Caught \| ([\d,]+) \| Missed \| ([\d,]+) \| False alarm \| ([\d,]+) \| Cleared", text)
    return None if not m else dict(zip(("tp", "fn", "fp", "tn"), (int(g.replace(",", "")) for g in m.groups())))


def main(pptx):
    pptx = Path(pptx)
    s = slide_texts(pptx)
    fin_half, ops_half = s[5].split("Operations Layer", 1)
    rows = []

    def add(layer, metric, value, slide, note=""):
        rows.append({"layer": layer, "metric": metric, "value": round(value, 4) if isinstance(value, float) else value, "slide": slide, "note": note})

    f1 = re.search(r"XGBoost, F1 = ([\d.]+)", fin_half)
    add("financial", "f1", num(f1.group(1)), 5, "XGBoost, Week 5 configuration")
    fr = re.search(r"Recall \| ([\d.]+)%", fin_half); fp_ = re.search(r"Precision \| ([\d.]+)%", fin_half)
    add("financial", "recall", num(fr.group(1)) / 100, 5)
    add("financial", "precision", num(fp_.group(1)) / 100, 5)
    for k, v in counts(fin_half).items():
        add("financial", k, v, 5)

    thr = re.search(r"threshold ([\d.]+) → ([\d.]+)", ops_half)
    add("operations", "threshold", num(thr.group(2)), 5, f"from {thr.group(1)}")
    orr = re.search(r"Recall \| ([\d.]+)%", ops_half); opr = re.search(r"Precision \| ([\d.]+)%", ops_half)
    add("operations", "recall", num(orr.group(1)) / 100, 5)
    add("operations", "precision", num(opr.group(1)) / 100, 5)
    for k, v in counts(ops_half).items():
        add("operations", k, v, 5)
    of1 = re.search(r"F1 = ([\d.]+), threshold ([\d.]+)", s[6])
    add("operations", "f1", num(of1.group(1)), 6)

    t4 = s[4]
    ft = re.search(r"([\d,]+) train / ([\d,]+) test", t4)
    add("financial", "train", int(ft.group(1).replace(",", "")), 4)
    add("financial", "test", int(ft.group(2).replace(",", "")), 4)
    add("financial", "features", int(re.search(r"\| Financial \(Taiwan\) \| [\d,]+ \| [\d,]+ \| [\d,]+ \| (\d+)", t4).group(1)), 4)
    ops = re.search(r"Operations \(DataCo\) \| ([\d,]+) → ([\d,]+) \| ([\d,]+) \| ([\d,]+) \| (\d+)", t4)
    add("operations", "rows_in", int(ops.group(1).replace(",", "")), 4)
    add("operations", "rows_after_cleaning", int(ops.group(2).replace(",", "")), 4)
    add("operations", "train", int(ops.group(3).replace(",", "")), 4)
    add("operations", "test", int(ops.group(4).replace(",", "")), 4)
    add("operations", "features", int(ops.group(5)), 4, "Week 4 processed features")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["layer", "metric", "value", "slide", "note"])
        w.writeheader(); w.writerows(rows)
    (OUT.parent / "final_presentation_SOURCE.txt").write_text(
        f"Figures read from: {pptx.name}\nsha256: {hashlib.sha256(pptx.read_bytes()).hexdigest()}\n"
        "Only numbers are kept. The presentation file is not part of this repo.\n", encoding="utf-8")
    print(f"wrote {len(rows)} figures to {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main(sys.argv[1])
