# 📊 Data Analytics Portfolio

Набор рабочих дашбордов и мини-проектов на Python.  
Данные обезличены, цифры — демонстрационные, скриншоты и видео — для портфолио.

---

##  Карта репозитория

---

## Дашборды (коротко)

- **Delivery Pizza** — контроль выручки, среднего и глубины чека, GMV по ресторанам, “узкие места”.  
  _Папка:_ `dashboards/delivery_pizza`

- **E-commerce Growth** — микс каналов/OS, конверсия, AOV, путь до первого заказа, категории/SKU.  
  _Папка:_ `dashboards/ecommerce-growth`

- **Gamedev Market** — разрез по жанрам/странам/платформам, активность игроков, топ-релизы.  
  _Папка:_ `dashboards/gamedev-market`

- **Retail FMCG Supply** — продажи vs поставки, доля промо, запасы, тренды SKU, остатки.  
  _Папка:_ `dashboards/retail-fmcg-supply`

- **Agency Real Estate** — средняя цена/м², time-to-sell, сезонность публикаций, детализация по локациям.  
  _Папка:_ `dashboards/agency-real-estate`

> Внутри каждой папки: `README.md` с описанием, `screenshots/` и (если есть) ссылка на видео-демо.

---

## Python-проекты

- **auto-mailer**  
  - `requirements.txt`, `.env.sample`  
  - Запуск:  
    ```bash
    cd python/auto-mailer
    python -m venv .venv && source .venv/Scripts/activate  # Windows Git Bash
    pip install -r requirements.txt
    cp .env.sample .env   # заполнить ключи/пароли
    python send_mail.py   # или используемый entry-point
    ```

- **weather-demand-bot**  
  - `requirements.txt`, `.env.sample`  
  - Запуск:  
    ```bash
    cd python/weather-demand-bot
    python -m venv .venv && source .venv/Scripts/activate
    pip install -r requirements.txt
    cp .env.sample .env   # заполнить токены
    python bot.py
    ```

---

## Примечания

- Все цифры и примеры — **анонимизированы/синтетические**.  
- Скриншоты — в папках `screenshots/`; видео-демо (если есть) — ссылкой в README соответствующего дашборда.  
- Репозиторий структурирован так, чтобы можно было открыть **любой проект изолированно**.

---

