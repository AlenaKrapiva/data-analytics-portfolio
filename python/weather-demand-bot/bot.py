# bot.py — Погодный индекс спроса
import os, csv, requests, pandas as pd
from io import BytesIO
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv
load_dotenv()


TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")                 
OWM_KEY = os.getenv("OPENWEATHER_KEY")         
TZ_OFFSET_MIN = int(os.getenv("TZ_OFFSET_MIN", "0"))
ALERT_THRESHOLD = int(os.getenv("ALERT_THRESHOLD", "80"))


def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def now_local(): return datetime.now() + timedelta(minutes=TZ_OFFSET_MIN)

def load_stores():
    with open("stores.csv", encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        rows = []
        for i, r in enumerate(rdr, start=2):
            name = (r.get("name") or "").strip()
            area = (r.get("area") or "").strip()
            lat = float((r.get("lat") or "").strip())
            lon = float((r.get("lon") or "").strip())
            rows.append((name, area, lat, lon))
        return rows 

def fetch_weather(lat, lon):
    url = "https://api.openweathermap.org/data/2.5/weather"
    r = requests.get(url, params={"lat": lat, "lon": lon, "appid": OWM_KEY, "units":"metric", "lang":"ru"}, timeout=12)
    r.raise_for_status()
    j = r.json()
    return {
        "temp_c": float(j["main"]["temp"]),
        "wind_mps": float(j.get("wind", {}).get("speed", 0.0)),
        "clouds": float(j.get("clouds", {}).get("all", 0.0)),
        "rain_mm": float((j.get("rain") or {}).get("1h", (j.get("rain") or {}).get("3h", 0.0))),
        "desc": j["weather"][0]["description"] if j.get("weather") else ""
    }

def demand_index(w, ts):
    temp_score  = clamp((15 - w["temp_c"]) / 20.0)
    rain_score  = clamp(w["rain_mm"] / 3.0)
    wind_score  = clamp(w["wind_mps"] / 10.0)
    cloud_score = clamp(w["clouds"] / 100.0)
    weekend_bonus = 0.10 if ts.weekday() >= 5 else 0.0
    return round(100 * clamp(0.5*temp_score + 0.3*rain_score + 0.2*wind_score + 0.2*cloud_score + weekend_bonus))

def action_hint(idx):
    if idx >= 80: return "🟢 усилить смену/курьеров, включить промо"
    if idx >= 65: return "🟡 быть готовыми, пуши/телега"
    if idx >= 50: return "⚪ стандартный режим"
    return "🔵 эконом-режим закупок/штата"

def build_df():
    ts = now_local()
    rows = []
    for name, area, lat, lon in load_stores():   # ← 4 переменные
        w = fetch_weather(lat, lon)
        idx = demand_index(w, ts)
        rows.append({
            "store": name,
            "area": area,                         # можно оставить или удалить, если не нужна
            "dt": ts.strftime("%Y-%m-%d %H:%M"),
            "temp_c": w["temp_c"],
            "rain_mm": w["rain_mm"],
            "wind_mps": w["wind_mps"],
            "clouds_pct": w["clouds"],
            "weekend": "yes" if ts.weekday() >= 5 else "no",
            "demand_index": idx,
            "action_hint": action_hint(idx),
            "desc": w["desc"],
        })
    return pd.DataFrame(rows).sort_values(["demand_index","store"], ascending=[False, True])

def build_df_by_area():
    df = build_df()
    if "area" not in df.columns or df["area"].eq("").all():
        return pd.DataFrame()  
    g = df.groupby("area", as_index=False).agg({
        "dt":           "first",
        "temp_c":       "mean",
        "rain_mm":      "mean",
        "wind_mps":     "mean",
        "clouds_pct":   "mean",
        "demand_index": "mean",
    })
    g["demand_index"] = g["demand_index"].round().astype(int)
    g["action_hint"]  = g["demand_index"].apply(action_hint)
    return (g.rename(columns={"area": "store"})
            .sort_values(["demand_index", "store"], ascending=[False, True]))


def to_excel(df: pd.DataFrame, sheet_name: str = "demand_now") -> BytesIO:
    bio = BytesIO()
    with pd.ExcelWriter(bio, engine="openpyxl") as w:
        df.to_excel(w, index=False, sheet_name=sheet_name)  # ← используем имя листа
        pd.DataFrame({
            "metric": ["temp_score","rain_score","wind_score","cloud_score","weekend_bonus","index_range"],
            "note":   ["=(15-T)/20","=rain/3","=wind/10","=clouds/100","+0.10 Sat/Sun","0..100 (выше — спрос выше)"]
        }).to_excel(w, index=False, sheet_name="method")
    bio.seek(0)
    return bio


async def send_excel_to(chat_id, context):
    df = build_df()

    # Текстовый алерт при высоком индексе 
    high = df[df["demand_index"] >= ALERT_THRESHOLD]
    if not high.empty:
        lines = "\n".join(f"• {r.store} — {r.demand_index}" for r in high.itertuples())
        await context.bot.send_message(
            chat_id=int(chat_id),
            text=f"🔥 Высокий спрос (≥{ALERT_THRESHOLD}):\n{lines}"
        )

    # Отправка Excel 
    excel = to_excel(df)
    fname = f"demand_index_{now_local().strftime('%Y%m%d_%H%M')}.xlsx"
    caption = f"Индекс спроса по точкам — {now_local().strftime('%d.%m %H:%M')}"
    await context.bot.send_document(
        chat_id=int(chat_id),
        document=excel,
        filename=fname,
        caption=caption
    )

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! /id — chat_id, /now — пришлю Excel сюда.")

async def cmd_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"chat_id: {update.effective_chat.id}")

async def cmd_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_excel_to(update.effective_chat.id, context)

async def cmd_now_areas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # строим сводку по округам
    df = build_df_by_area()
    if df.empty:
        await update.message.reply_text("Нет сводки по округам: проверь, что в stores.csv есть колонка 'area'.")
        return

    # опциональный текстовый алерт по порогу
    high = df[df["demand_index"] >= ALERT_THRESHOLD]
    if not high.empty:
        lines = "\n".join(f"• {r.store} — {r.demand_index}" for r in high.itertuples())
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"🔥 Высокий спрос (≥{ALERT_THRESHOLD}) по округам:\n{lines}"
        )

    # Excel со сводкой по округам
    excel = to_excel(df, sheet_name="areas_now")   # важно: лист 'areas_now'
    fname = f"areas_{now_local().strftime('%Y%m%d_%H%M')}.xlsx"
    caption = f"Индекс спроса по округам — {now_local().strftime('%d.%m %H:%M')}"

    await context.bot.send_document(
        chat_id=update.effective_chat.id,
        document=excel,
        filename=fname,
        caption=caption,
    )
 
async def job_send(context: ContextTypes.DEFAULT_TYPE):
    if CHAT_ID: await send_excel_to(CHAT_ID, context)

def main():
    assert TOKEN, "Нужна переменная BOT_TOKEN"
    assert OWM_KEY, "Нужна переменная OPENWEATHER_KEY"
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("id", cmd_id))
    app.add_handler(CommandHandler("now", cmd_now))
    app.add_handler(CommandHandler("now_areas", cmd_now_areas))
    app.job_queue.run_repeating(job_send, interval=3600, first=60)
    app.run_polling(close_loop=False)

if __name__ == "__main__":
    main()
