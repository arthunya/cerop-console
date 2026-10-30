"""
Regenerates the raw/unencoded operations TEST split, since the canonical
v3_FIXED notebook never persists this intermediate stage to disk (it only
saves the final encoded/processed CSV). This script deterministically
replicates cells 13-26 of Week4_CEROP_Pipeline_Integration_FIXED_v3_FIXED.ipynb
exactly as written there — no new cleaning logic, no fitting of anything
randomness-sensitive (train/test split + IQR capping only, both deterministic
given random_state=42).

Output: X_operations_test, 24 columns, 34,393 rows, matching the schema that
cerop_operations_preprocessor.pkl expects as .transform() input.

Provenance: see CLAUDE.md > "Regenerated files" for verification result.
"""
import os
import pandas as pd
import kagglehub
from sklearn.model_selection import train_test_split

# --- cell-13 / cell-14: download + date-tail filter ---
operations_path = kagglehub.dataset_download(
    "shashwatwork/dataco-smart-supply-chain-for-big-data-analysis"
)
operations_file = os.path.join(operations_path, "DataCoSupplyChainDataset.csv")
operations_df = pd.read_csv(operations_file, encoding="latin-1")
operations_df.columns = operations_df.columns.str.strip()
operations_df["order date (DateOrders)"] = pd.to_datetime(
    operations_df["order date (DateOrders)"], errors="coerce"
)
original_rows = len(operations_df)
operations_df = operations_df[
    operations_df["order date (DateOrders)"] < "2017-10-01"
].copy()
print("Original operations rows:", original_rows)
print("Rows after artifact removal:", len(operations_df))

# --- cell-16: train/test split (identical params to the canonical notebook) ---
operations_train_raw, operations_test_raw = train_test_split(
    operations_df,
    test_size=0.20,
    stratify=operations_df["Late_delivery_risk"],
    random_state=42,
)
print("Train:", operations_train_raw.shape, "Test:", operations_test_raw.shape)

# --- cell-17: clean_operations_structure (verbatim from the notebook) ---
def clean_operations_structure(df):
    df = df.copy()

    drop_cols = [
        "Delivery Status",
        "Days for shipping (real)",
        "shipping date (DateOrders)",
        "Customer Email",
        "Customer Fname",
        "Customer Lname",
        "Customer Password",
        "Customer Street",
        "Product Image",
        "Product Description",
        "Order Customer Id",
        "Order Item Cardprod Id",
        "Product Category Id",
        "Product Status",
        "Latitude",
        "Longitude",
        "Order Id",
        "Order Item Id",
        "Customer Zipcode",
        "Order Zipcode",
        "Customer City",
        "Order City",
        "Order State",
        "Product Name",
        "Customer Id",
        "Category Id",
        "Department Id",
        "Product Card Id",
        "Order Item Total",
        "Order Item Product Price",
        "Order Profit Per Order",
        "Sales per customer",
    ]

    df["order date (DateOrders)"] = pd.to_datetime(
        df["order date (DateOrders)"], errors="coerce"
    )

    df["Order_Year"] = df["order date (DateOrders)"].dt.year
    df["Order_Month"] = df["order date (DateOrders)"].dt.month
    df["Order_DayOfWeek"] = df["order date (DateOrders)"].dt.dayofweek
    df["Order_Hour"] = df["order date (DateOrders)"].dt.hour

    df["Order_YearMonth"] = (
        df["order date (DateOrders)"].dt.to_period("M").dt.to_timestamp()
    )

    drop_cols.append("order date (DateOrders)")

    return df.drop(columns=[col for col in drop_cols if col in df.columns])

operations_train_clean = clean_operations_structure(operations_train_raw)
operations_test_clean = clean_operations_structure(operations_test_raw)
print("Train clean:", operations_train_clean.shape, "Test clean:", operations_test_clean.shape)

# --- cell-19/20: IQR capping, fit on train, applied to both ---
OUTLIER_COLS = ["Benefit per order"]

def fit_iqr_bounds(df, columns, factor=1.5):
    bounds = {}
    for col in columns:
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1
        bounds[col] = (q1 - factor * iqr, q3 + factor * iqr)
    return bounds

def apply_iqr_bounds(df, bounds):
    df = df.copy()
    for col, (lower, upper) in bounds.items():
        df[col] = df[col].clip(lower=lower, upper=upper)
    return df

operations_outlier_bounds = fit_iqr_bounds(operations_train_clean, OUTLIER_COLS)
operations_train_clean = apply_iqr_bounds(operations_train_clean, operations_outlier_bounds)
operations_test_clean = apply_iqr_bounds(operations_test_clean, operations_outlier_bounds)
print("Operations outliers handled.")

# --- cell-22/23: GSCPI merge ---
gscpi_candidates = [
    "gscpi_data.xls",
    r"<AIT506_PROJECT_FOLDER>\Week 4\Final\gscpi_data.xls",
    "/content/gscpi_data.xls",
    "/mnt/data/gscpi_data.xls",
]
gscpi_file = next((p for p in gscpi_candidates if os.path.exists(p)), None)
if gscpi_file is None:
    raise FileNotFoundError("gscpi_data.xls not found in any candidate location.")

gscpi_df = pd.read_excel(gscpi_file)
if "Date" not in gscpi_df.columns or "GSCPI" not in gscpi_df.columns:
    gscpi_df = pd.read_excel(gscpi_file, skiprows=4)
gscpi_df = gscpi_df.iloc[:, :2].copy()
gscpi_df.columns = ["Date", "GSCPI"]

gscpi_df["Order_YearMonth"] = (
    pd.to_datetime(gscpi_df["Date"], errors="coerce").dt.to_period("M").dt.to_timestamp()
)
gscpi_monthly = (
    gscpi_df[["Order_YearMonth", "GSCPI"]]
    .dropna(subset=["Order_YearMonth"])
    .drop_duplicates(subset=["Order_YearMonth"])
)

operations_train_clean = operations_train_clean.merge(gscpi_monthly, on="Order_YearMonth", how="left")
operations_test_clean = operations_test_clean.merge(gscpi_monthly, on="Order_YearMonth", how="left")
print("Train after GSCPI merge:", operations_train_clean.shape, "Test:", operations_test_clean.shape)

# --- cell-26: split into X/y, drop target + join key ---
X_operations_train = operations_train_clean.drop(columns=["Late_delivery_risk", "Order_YearMonth"])
y_operations_train = operations_train_clean["Late_delivery_risk"]
X_operations_test = operations_test_clean.drop(columns=["Late_delivery_risk", "Order_YearMonth"])
y_operations_test = operations_test_clean["Late_delivery_risk"]

print("\nFinal X_operations_test shape:", X_operations_test.shape)
print("Columns:", list(X_operations_test.columns))

# --- sample 8 rows and save ---
sample = X_operations_test.head(8).reset_index(drop=True)
out_path = r"<AIT506_PROJECT_FOLDER>\CEROP_Live_Demo\demo_data\operations_new_cases_source.csv"
sample.to_csv(out_path, index=False)
print(f"\nSaved 8-row sample to: {out_path}")

# Also save the full regenerated test set to a side file for verification use
# (not part of the deliverable, just scratch for the cross-check step)
verify_path = r"<AIT506_PROJECT_FOLDER>\CEROP_Live_Demo\demo_data\_regenerated_operations_X_test_full.csv"
X_operations_test.to_csv(verify_path, index=False)
print(f"Saved full regenerated test set (for verification only) to: {verify_path}")
