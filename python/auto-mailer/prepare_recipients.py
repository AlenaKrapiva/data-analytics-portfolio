from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import re

RAW_DIR = Path("data/raw/kaggle/airlines")
RECIPIENTS_PATH = Path("data/processed/recipients.csv")
OUT_PATH = Path("data/processed/mail_merge.csv")

# 1) ищем первый CSV в data/raw/kaggle/airlines
raw_files = list(RAW_DIR.glob("**/*.csv"))
if not raw_files:
    raise FileNotFoundError("Не найден CSV в data/raw/kaggle/airlines/")
raw_path = raw_files[0]

def read_csv_auto(path: Path) -> pd.DataFrame:
    """Пробуем разные разделители; берём тот, где колонок > 1."""
    for sep in [",", ";", "\t", "|"]:
        try:
            df = pd.read_csv(path, sep=sep, encoding="utf-8")
            if df.shape[1] > 1:
                return df
        except Exception:
            pass
    return pd.read_csv(path)  # как есть

df_raw = read_csv_auto(raw_path)

# нормализуем имена колонок
df_raw.columns = [c.strip().lower() for c in df_raw.columns]

def first_col(candidates):
    for c in candidates:
        if c in df_raw.columns:
            return c
    return None

col_origin   = first_col(["origin", "source", "from", "source_city", "from_city", "departure_city", "src"])
col_dest     = first_col(["destination", "dest", "to", "destination_city", "to_city", "arrival_city", "dst"])
col_date     = first_col(["date", "journey_date", "date_of_journey", "departure_date", "dep_time", "flight_date"])
col_price    = first_col(["price", "fare", "ticket_price", "selling_price", "amount", "cost"])
col_airline  = first_col(["airline", "carrier", "airline_name", "airline_code"])
col_duration = first_col(["duration", "journey_time", "travel_time"])

def norm(s):
    return str(s).strip().lower()

# приводим для фильтрации
if col_origin: df_raw["__origin"] = df_raw[col_origin].map(norm)
if col_dest:   df_raw["__dest"]   = df_raw[col_dest].map(norm)

# цена → число
if col_price:
    def parse_price(x):
        if pd.isna(x): return None
        s = re.sub(r"[^\d.,]", "", str(x))
        s = s.replace(",", "")
        try:
            return float(s)
        except Exception:
            return None
    df_raw["__price"] = df_raw[col_price].apply(parse_price)
else:
    df_raw["__price"] = None

# дата → datetime (если есть)
if col_date:
    df_raw["__date"] = pd.to_datetime(df_raw[col_date], errors="coerce")
else:
    df_raw["__date"] = pd.NaT

# читаем получателей
rec = pd.read_csv(RECIPIENTS_PATH)
if "active" in rec.columns:
    rec = rec[rec["active"] == 1]

rows = []
now = datetime.now()

for _, r in rec.iterrows():
    origin = norm(r.get("origin", ""))
    dest = norm(r.get("destination", ""))
    days = int(r.get("days_window", 30))
    max_price = float(r.get("max_price", 1e12))

    subset = df_raw.copy()
    if col_origin: subset = subset[subset["__origin"] == origin]
    if col_dest:   subset = subset[subset["__dest"] == dest]

    # фильтр по дате, если в датасете есть дата
    if col_date and subset["__date"].notna().any():
        end = now + timedelta(days=days)
        subset = subset[(subset["__date"] >= now) & (subset["__date"] <= end)]

    # выбираем самое дешёвое
    candidate = None
    if "__price" in subset.columns and subset["__price"].notna().any():
        candidate = subset.loc[subset["__price"].idxmin()]

    rows.append({
        "email":        r.get("email", ""),
        "name":         r.get("name", ""),
        "origin":       r.get("origin", ""),
        "destination":  r.get("destination", ""),
        "days_window":  days,
        "max_price":    max_price,
        "cheapest_price": int(candidate["__price"]) if candidate is not None and pd.notna(candidate["__price"]) else "",
        "flight_date":    candidate["__date"].strftime("%Y-%m-%d") if candidate is not None and pd.notna(candidate["__date"]) else "",
        "airline":        str(candidate[col_airline]) if candidate is not None and col_airline else "",
        "duration":       str(candidate[col_duration]) if candidate is not None and col_duration else "",
        "active":       r.get("active", 1),
    })

OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
pd.DataFrame(rows).to_csv(OUT_PATH, index=False, encoding="utf-8")
print(f"[OK] Готово: записано {len(rows)} строк в {OUT_PATH}")

