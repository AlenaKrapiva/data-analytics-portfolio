# Auto Mailer (SendGrid + Windows Task Scheduler)

Авто-рассылка писем по шаблонам и данным из CSV (на базе датасета авиа-рейсов). 
Запуск планируется раз в час через Планировщик задач Windows.

## Стек
- Python 3.11+, `pandas`, `python-dotenv`, `sendgrid`
- Windows Task Scheduler

## Структура
data/
processed/
recipients.sample.csv # пример
templates/
subject.txt
body.txt
run_mailer.bat                         # тихий запуск: подготовка + отправка
prepare_recipients.py                  # формирует data/processed/mail_merge.csv
send_mail.py                           # отправка через SendGrid
.env.sample                            # пример переменных окружения


## Установка
```bash
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt

copy .env.sample .env  
# SENDGRID_API_KEY=...
# MAIL_FROM=...
# MAIL_FROM_NAME=...

## Запуск вручную
python prepare_recipients.py
python send_mail.py --send

## Планировщик
# Создать задачу, запускающую run_mailer.bat каждый час.
# Логи: logs/last_run.txt, журнал отправок: state/sent_log.csv.
