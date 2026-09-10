"""
Convert your existing product data (CSV or Excel) into the products_master.json
schema expected by app.py.

USAGE:
    python csv_to_json.py your_products.csv
    python csv_to_json.py your_products.xlsx

Your source file should have these columns (case-insensitive, order doesn't matter):
    id, name, code, category, brand, description, keywords, price, currency, stock, image

- 'keywords' can be a single cell with comma/semicolon separated terms
  e.g. "water bottle, steel bottle, flask"
- 'image' should just be the filename, e.g. "P0001.jpg"
  Place the actual image file in static/images/ with that same filename.
- Missing columns are simply left blank/None in the output.
"""

import sys
import os
import json

try:
    import pandas as pd
except ImportError:
    print("This script needs pandas. Install it with: pip install pandas openpyxl --break-system-packages")
    sys.exit(1)


def normalize_keywords(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []
    parts = [p.strip() for p in str(value).replace(";", ",").split(",")]
    return [p for p in parts if p]


def main():
    if len(sys.argv) < 2:
        print("Usage: python csv_to_json.py <source_file.csv|.xlsx>")
        sys.exit(1)

    source_path = sys.argv[1]
    ext = os.path.splitext(source_path)[1].lower()

    if ext == ".csv":
        df = pd.read_csv(source_path)
    elif ext in (".xlsx", ".xls"):
        df = pd.read_excel(source_path)
    else:
        print("Unsupported file type. Use .csv or .xlsx")
        sys.exit(1)

    # normalize column names to lowercase
    df.columns = [c.strip().lower() for c in df.columns]

    products = []
    for _, row in df.iterrows():
        product = {
            "id": str(row.get("id", "")).strip(),
            "name": str(row.get("name", "")).strip(),
            "code": str(row.get("code", "")).strip(),
            "category": str(row.get("category", "")).strip(),
            "brand": str(row.get("brand", "")).strip(),
            "description": str(row.get("description", "")).strip(),
            "keywords": normalize_keywords(row.get("keywords")),
            "price": float(row["price"]) if "price" in row and not pd.isna(row["price"]) else None,
            "currency": str(row.get("currency", "INR")).strip(),
            "stock": int(row["stock"]) if "stock" in row and not pd.isna(row["stock"]) else None,
            "image": str(row.get("image", "")).strip(),
        }
        products.append(product)

    output = {"products": products}
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "products_master.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Converted {len(products)} products -> {out_path}")
    print("Now copy your image files into static/images/ using the same filenames as in the 'image' column.")


if __name__ == "__main__":
    main()
