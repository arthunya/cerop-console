"""
Extracts every table from the submitted Final Report (.docx) into CSV files under
results/reported/, so figures that only exist in the report can be read by code
instead of being typed in by hand.

Why this exists: the Week 5 financial results CSVs in this repo come from a later local
re-run (XGBoost F1 0.533, Random Forest 0.472). The submitted report, built from the team's
Colab run, cites 0.529 and 0.489. The project quotes the submitted figures, and this script
is how the site gets them.

Usage:
    python scripts/extract_report_tables.py "<path to [AIT506] Group 4 - CEROP_Final_Report.docx>"

The .docx is not committed. The PDF export of the same file is in reports/CEROP_Final_Report.pdf.
"""
import csv
import hashlib
import html
import re
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "results" / "reported"


def cell_text(xml):
    paras = re.findall(r"<w:p[ >].*?</w:p>", xml, flags=re.S) or [xml]
    return " ".join(html.unescape(re.sub(r"<[^>]+>", "", p)).strip() for p in paras).strip()


def main(docx_path):
    docx = Path(docx_path)
    raw = docx.read_bytes()
    xml = zipfile.ZipFile(docx).read("word/document.xml").decode("utf-8")
    tables = re.findall(r"<w:tbl>.*?</w:tbl>", xml, flags=re.S)
    OUT.mkdir(parents=True, exist_ok=True)
    index = []
    for k, t in enumerate(tables, start=1):
        rows = [[cell_text(c) for c in re.findall(r"<w:tc>.*?</w:tc>", r, flags=re.S)]
                for r in re.findall(r"<w:tr[ >].*?</w:tr>", t, flags=re.S)]
        name = f"final_report_table_{k:02d}.csv"
        with open(OUT / name, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows(rows)
        index.append([name, len(rows), " | ".join(rows[0]) if rows else ""])
    with open(OUT / "index.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["file", "rows_including_header", "header"])
        w.writerows(index)
    (OUT / "SOURCE.txt").write_text(
        f"Extracted from: {docx.name}\nsha256: {hashlib.sha256(raw).hexdigest()}\n"
        f"Tables: {len(tables)}\nPDF of the same document: reports/CEROP_Final_Report.pdf\n",
        encoding="utf-8")
    print(f"wrote {len(tables)} tables to {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main(sys.argv[1])
