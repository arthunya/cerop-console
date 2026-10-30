"""
Builds human-readable driver labels + point values for App.jsx, from the
SHAP output CSVs + the raw new_cases CSVs (for actual category values).
Prints ready-to-paste JS object literals.
"""
import pandas as pd
import re

DEMO_DIR = r"<AIT506_PROJECT_FOLDER>\CEROP_Live_Demo\demo_data"

FIN_LABELS = {
    "Total debt/Total net worth": "Total debt / net worth",
    "Quick Ratio": "Quick ratio",
    "Retained Earnings to Total Assets": "Retained earnings / assets",
    "Profitability_Composite": "Profitability (composite)",
    "Persistent EPS in the Last Four Seasons": "EPS, last 4 seasons",
    "Total expense/Assets": "Total expense / assets",
    "Current Liabilities/Liability": "Current liabilities / liability",
    "Continuous Net Profit Growth Rate": "Net profit growth rate",
    "Revenue Per Share (Yuan ¥)": "Revenue per share",
    "Net Value Growth Rate": "Net value growth rate",
}

def fin_label(feat):
    return FIN_LABELS.get(feat, feat)


OPS_NUMERIC_LABELS = {
    "Days for shipment (scheduled)": "Scheduled shipping window",
    "Order_Hour": "Order hour",
    "Order_DayOfWeek": "Order day of week",
    "Order_Year": "Order year",
    "Order_Month": "Order month",
    "GSCPI": "Supply chain pressure (GSCPI)",
    "Benefit per order": "Benefit per order",
    "Sales": "Sale amount",
    "Product Price": "Product price",
    "Order Item Quantity": "Order quantity",
    "Order Item Discount": "Order discount",
    "Order Item Discount Rate": "Discount rate",
    "Order Item Profit Ratio": "Profit ratio",
}

DOW_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def ops_label(feat, case_raw):
    if feat.startswith("numeric__"):
        base = feat[len("numeric__"):]
        label = OPS_NUMERIC_LABELS.get(base, base)
        if base == "Days for shipment (scheduled)":
            days = case_raw["Days for shipment (scheduled)"]
            return f"{label} ({int(days)} day{'s' if days != 1 else ''})"
        if base == "Order_DayOfWeek":
            try:
                return f"{label} ({DOW_NAMES[int(case_raw['Order_DayOfWeek'])]})"
            except Exception:
                return label
        if base == "Order_Hour":
            return f"{label} ({int(case_raw['Order_Hour'])}:00)"
        return label
    # Already-grouped categorical features (one-hot dummies summed back into
    # their parent column by group_operations_shap) — look up this case's
    # actual real-world value, not the encoded column name.
    if feat in ("Type", "Customer Country", "Customer Segment", "Order Status", "Shipping Mode"):
        nice_col = "Payment type" if feat == "Type" else feat
        val = case_raw.get(feat, "")
        return f"{nice_col} ({val})"
    if feat.startswith("low_cardinality__"):
        rest = feat[len("low_cardinality__"):]
        # format: "<Column>_<Category>" — column names we know: Type, Customer Country,
        # Customer Segment, Order Status, Shipping Mode
        for col in ["Shipping Mode", "Customer Segment", "Customer Country", "Order Status", "Type"]:
            prefix = col + "_"
            if rest.startswith(prefix):
                category = rest[len(prefix):]
                nice_col = "Payment type" if col == "Type" else col
                return f"{nice_col} ({category})"
        return rest
    if feat.startswith("high_cardinality__"):
        col = feat[len("high_cardinality__"):]
        val = case_raw.get(col, "")
        return f"{col} ({val})"
    return feat


def build_layer(csv_name, cases_name, id_col, label_fn, is_ops, total_feature_count):
    shap_df = pd.read_csv(DEMO_DIR + "\\" + csv_name)
    cases_df = pd.read_csv(DEMO_DIR + "\\" + cases_name)
    cases_df = cases_df.set_index(id_col)

    print(f"\n// ==== {csv_name} -> JS object ====")
    for _, row in shap_df.iterrows():
        cid = row["case_id"]
        case_raw = cases_df.loc[cid]
        drivers = []
        top4_sum_frac = 0.0
        for i in range(1, 5):
            feat = row[f"feature_{i}_name"]
            contrib = row[f"feature_{i}_contribution"]
            top4_sum_frac += contrib
            pts = round(contrib * 100)
            if is_ops:
                nice = ops_label(feat, case_raw)
            else:
                nice = fin_label(feat)
            drivers.append((nice, pts))
        # Remainder bucket: makes base + top4 + rest == final EXACTLY (in
        # whole points after rounding), so the panel never implies the top-4
        # alone explain the full base->final movement when they don't.
        rest_frac = (row["final_score"] - row["base_rate"]) - top4_sum_frac
        rest_pts = round(rest_frac * 100)
        n_rest = total_feature_count - 4
        rest_label = f"{n_rest} more factors combined"
        drivers.append((rest_label, rest_pts))
        print(f'  "{cid}": {{ base: {row["base_rate"]:.4f}, final: {row["final_score"]:.4f}, drivers: [')
        for nice, pts in drivers:
            sign = "+" if pts >= 0 else ""
            print(f'    {{ label: "{nice}", pts: {pts} }},  // {sign}{pts} pts')
        print("  ]},")


build_layer("financial_shap_explanations.csv", "financial_new_cases.csv", "case_id", fin_label, is_ops=False, total_feature_count=85)
build_layer("operations_shap_explanations.csv", "operations_new_cases.csv", "case_id", ops_label, is_ops=True, total_feature_count=22)
