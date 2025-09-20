@echo off
cd /d C:\projects\weather_demand_bot
taskkill /F /IM python.exe >nul 2>&1
call .\.venv\Scripts\activate.bat
python bot.py
