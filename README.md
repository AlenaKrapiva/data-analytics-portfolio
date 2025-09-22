# 📊 Data Analytics Portfolio

Набор рабочих дашбордов и мини-проектов на Python.  
Данные обезличены, цифры — демонстрационные, скриншоты и видео — для портфолио.

---

##  Карта репозитория

---

## 🔗 Быстрые ссылки

### Дашборды
- [Delivery Pizza](dashboards/delivery_pizza/) — контроль выручки, среднего и глубины чека, GMV по ресторанам.
- [E-commerce Growth](dashboards/ecommerce-growth/) — микс каналов/OS, конверсия, AOV, TTF, категории/SKU.
- [Gamedev Market](dashboards/gamedev-market/) — жанры/страны/платформы, активность игроков, топ-релизы.
- [Retail FMCG Supply](dashboards/retail-fmcg-supply/) — продажи vs поставки, запасы, промо, тренды SKU.
- [Agency Real Estate](dashboards/agency-real-estate/) — средняя цена/м², дни до продажи, сезонность объявлений.

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
- [auto-mailer](python/auto-mailer/)

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
- [weather-demand-bot](python/weather-demand-bot/)
---

## Примечания

- Все цифры и примеры — **анонимизированы/синтетические**.  
- Скриншоты — в папках `screenshots/`; видео-демо (если есть) — ссылкой в README соответствующего дашборда.  
- Репозиторий структурирован так, чтобы можно было открыть **любой проект изолированно**.

---

