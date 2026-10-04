
from pathlib import Path
import sqlite3
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
SAMPLE = ROOT / "data" / "sample"
DB_PATH = ROOT / "data" / "analytics.db"

# Accept both the simplified names used by this repo and the original Olist names.
ALIASES = {
    "customers": ["customers.csv", "olist_customers_dataset.csv"],
    "orders": ["orders.csv", "olist_orders_dataset.csv"],
    "order_items": ["order_items.csv", "olist_order_items_dataset.csv"],
    "payments": ["payments.csv", "olist_order_payments_dataset.csv"],
    "reviews": ["reviews.csv", "olist_order_reviews_dataset.csv"],
    "products": ["products.csv", "olist_products_dataset.csv"],
    "sellers": ["sellers.csv", "olist_sellers_dataset.csv"],
    "geolocation": ["geolocation.csv", "olist_geolocation_dataset.csv"],
    "category_translation": ["category_translation.csv", "product_category_name_translation.csv"],
}

def find_file(folder, aliases):
    for name in aliases:
        path = folder / name
        if path.exists():
            return path
    return None

def choose_data_dir():
    if all(find_file(RAW, aliases) for aliases in ALIASES.values()):
        return RAW
    return SAMPLE

def load_tables():
    data_dir = choose_data_dir()
    tables = {}
    for table, aliases in ALIASES.items():
        path = find_file(data_dir, aliases)
        if path is not None:
            tables[table] = pd.read_csv(path)
    return tables, data_dir

def build_database():
    tables, data_dir = load_tables()
    if not tables:
        raise FileNotFoundError("No dataset files found. Keep the bundled sample data or add the public dataset to data/raw/.")
    conn = sqlite3.connect(DB_PATH)
    for name, df in tables.items():
        df.to_sql(name, conn, if_exists="replace", index=False)
    for statement in [
        "CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id)",
        "CREATE INDEX IF NOT EXISTS idx_items_order ON order_items(order_id)",
        "CREATE INDEX IF NOT EXISTS idx_items_product ON order_items(product_id)",
        "CREATE INDEX IF NOT EXISTS idx_reviews_order ON reviews(order_id)",
    ]:
        conn.execute(statement)
    conn.commit()
    conn.close()
    return data_dir

if __name__ == "__main__":
    selected = build_database()
    print(f"Database created at: {DB_PATH}")
    print(f"Data source: {selected}")
