@echo off
setlocal
cd /d %~dp0
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

:: очищаем лог дублей перед каждым запуском
del "%~dp0state\sent_log.csv" 2>nul

mkdir logs 2>nul

echo [%date% %time%] prepare_recipients.py > logs\last_run.txt
"%~dp0.venv\Scripts\python.exe" prepare_recipients.py >> logs\last_run.txt 2>&1
if errorlevel 1 goto :err

echo [%date% %time%] send_mail.py --send >> logs\last_run.txt
"%~dp0.venv\Scripts\python.exe" send_mail.py --send >> logs\last_run.txt 2>&1
if errorlevel 1 goto :err

echo [%date% %time%] OK >> logs\last_run.txt
type logs\last_run.txt
pause
exit /b 0

:err
echo [%date% %time%] FAILED %errorlevel% >> logs\last_run.txt
type logs\last_run.txt
pause
exit /b %errorlevel%
